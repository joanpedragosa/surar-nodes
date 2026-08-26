# =====================================================================
# NOM DEL CODI: step35_xat_interactiu.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step35_xat_interactiu.py
# DESCRIPCIÓ FUNCIONAL: Interfície conversacional client-side per a 
#                      inferència geomètrica lleugera (ARD).
#                      Utilitza embeddings optimitzats distribuïts per 
#                      calcular similitud còsina sense models pesats.
# OPCIONS D'EXECUCIÓ: python pipeline/step35_xat_interactiu.py
# DEPENDÈNCIES: aiohttp, asyncio, numpy
# =====================================================================

import os
import sys
import json
import logging
import asyncio
import aiohttp
import re
import numpy as np
import time

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import GLOBAL, STEP_05, STEP_10, STEP_33, STEP_35, DATA_ROOT
from pipeline.step00_contracte_global import normalitzar_token_català, construir_url_node_oficial

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_STEP35 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 35 (XAT INTERACTIU ARD)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Proporcionar una interfície natural ràpida i traçable que utilitza inferència 
geomètrica pura sobre embeddings distribuïts.

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Resolució d'Identitat via Mapa Global: Traducció robusta de tokens a URLs.
2. Descàrrega Paral·lela Massiva (Asyncio): Obté simultàniament els nodes 
   rellevants (amb els seus embeddings optimitzats) des de GitHub.
3. Vectorització de la Pregunta: Calcula el vector mitjà dels embeddings 
   dels tokens de la consulta.
4. Ranking per Similaritat Còsina: Compara geomètricament el vector de la 
   pregunta amb els vectors dels candidats potencials.
5. Generació Determinista: Retorna la resposta amb la major proximitat 
   semàntica en l'espai vectorial.

RESULTAT EXECUTAT CONCRET:
Respostes precises basades en geometria semàntica pura, amb temps de resposta 
optimitzat gràcies a la concurrència asíncrona i sense dependre de GPUs.
================================================================================
"""

class SurarChatBotARD:
    def __init__(self):
        self.cache_nodes = {}
        self.global_map = {}
        self.session = None
        
        # Indicadors quantitatius per filtrar candidats (opcional, per millorar precisió)
        self.quantitative_indicators = set(str(i) for i in range(1000))
        self.quantitative_indicators.update({
            'un', 'dos', 'tres', 'quatre', 'cinc', 'sis', 'set', 'vuit', 'nou', 'deu',
            'onze', 'dotze', 'tretze', 'catorze', 'quinze', 'vint', 'trenta', 'quaranta',
            'cent', 'cents', 'mil', 'milers', 'molts', 'pocs', 'diversos', 'cap'
        })

    async def initialize(self):
        # Configurar timeout per evitar penjades
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        await self.load_global_map()

    async def close(self):
        if self.session:
            await self.session.close()

    async def load_global_map(self):
        ruta_mapping = os.path.join(DATA_ROOT, "mapping_global.json")
        if os.path.exists(ruta_mapping):
            try:
                with open(ruta_mapping, "r", encoding="utf-8") as f:
                    self.global_map = json.load(f)
                logging.info(f"🗺️ Mapa global carregat amb {len(self.global_map)} entrades.")
            except Exception as e:
                logging.error(f"❌ Error carregant mapa global: {e}")
                self.global_map = {}

    def resolve_url_from_map(self, token: str) -> str:
        if token in self.global_map:
            return self.global_map[token].get("github_raw_url")
        token_lower = token.lower()
        if token_lower in self.global_map:
            return self.global_map[token_lower].get("github_raw_url")
        return construir_url_node_oficial(token)

    async def fetch_node(self, token: str) -> dict:
        if token in self.cache_nodes:
            return self.cache_nodes[token]
            
        url = self.resolve_url_from_map(token)
        if not url: return None

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    text_content = await response.text()
                    data = json.loads(text_content)
                    self.cache_nodes[token] = data
                    return data
        except Exception as e:
            pass # Silenciem errors individuals
        return None

    async def fetch_multiple_nodes(self, tokens: list) -> dict:
        """Descarrega múltiples nodes en paral·lel."""
        unique_tokens = list(set([t for t in tokens if t not in self.cache_nodes]))
        if unique_tokens:
            tasks = [self.fetch_node(t) for t in unique_tokens]
            await asyncio.gather(*tasks)
        
        return {t: self.cache_nodes[t] for t in tokens if t in self.cache_nodes}

    def clean_token(self, token: str) -> str:
        token = token.strip().lower()
        token = re.sub(r"^['\"]+|['\"]+$", "", token)
        token = re.sub(r"^(l|d|s|n|m|qu|j)'", "", token)
        token = re.sub(r"[.,;:!?]+$", "", token)
        return token

    def is_quantitative(self, term: str) -> bool:
        if term.isdigit(): return True
        if '-' in term and all(p.isdigit() for p in term.split('-')): return True
        return term in self.quantitative_indicators

    def cosine_similarity(self, vec_a, vec_b):
        """Calcula la similitud còsina entre dos vectors."""
        vec_a = np.array(vec_a)
        vec_b = np.array(vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(vec_a, vec_b) / (norm_a * norm_b)

    async def process_query(self, query: str):
        start_time = time.time()
        raw_tokens = query.split()
        stop_words = {'quants', 'de', 'el', 'la', 'els', 'les', 'un', 'una', 'que', 'com', 'amb', 'per', 'en', 'a', 'i', 'o', 'te', 'té', 'tenia', 'era', 'hi', 'ha', 'va', 'ser', 'estar'}
        
        tokens = []
        for t in raw_tokens:
            cleaned = self.clean_token(t)
            if len(cleaned) > 2 and cleaned not in stop_words:
                tokens.append(normalitzar_token_català(cleaned))
                
        logging.info(f"🔍 Tokens efectius: {tokens}")
        if not tokens: return "No he identificat conceptes clau."

        # 1. Descarregar nodes clau de la pregunta en paral·lel
        logging.info("🌐 Descarregant nodes de la consulta...")
        query_nodes_data = await self.fetch_multiple_nodes(tokens)
        
        if not query_nodes_data: 
            return "No trobo aquests conceptes al graf públic."

        # 2. Calcular el Vector Mitjà de la Pregunta
        query_vectors = []
        for token, data in query_nodes_data.items():
            emb = data.get("embedding_vector")
            if emb:
                query_vectors.append(emb)
        
        if not query_vectors:
            return "Els nodes trobats no tenen embeddings vàlids."
            
        # Mitjana simple dels vectors dels tokens de la pregunta
        query_vector_mean = np.mean(query_vectors, axis=0)

        # 3. Recollir candidats potencials (basat en connexions o vocabulari)
        # En ARD pur, podem usar el mapping global per buscar candidats relacionats 
        # o simplement usar paraules clau quantitatives si la pregunta ho demana.
        candidate_tokens = set()
        for node_name, data in query_nodes_data.items():
            # Aquí podríem usar 'edges' si existissin, però per ara usarem 
            # una heurística simple: si la pregunta té indicadors quantitatius,
            # busquem candidats que també ho siguin o que estiguin en el mapa.
            # Per simplificar, agafarem tots els tokens del mapa que comparteixin 
            # alguna connexió o simplement provarem amb els més freqüents si no hi ha edges.
            # Com que els nodes actuals no tenen edges complexos, farem una cerca ampla:
            # Si la pregunta és "Quants regidors...", els candidats són números.
            
            has_quant_intent = any(self.is_quantitative(t) for t in tokens)
            
            if has_quant_intent:
                # Si hi ha intenció quantitativa, afegim tokens quantitatius coneguts com a candidats
                for t in self.quantitative_indicators:
                    if t in self.global_map:
                        candidate_tokens.add(t)
            else:
                # Si no, afegim tokens relacionats (simulació bàsica)
                # En un futur, això hauria de venir de les 'edges' del node
                pass 

        # Si no hem trobat candidats específics, provem amb tots els tokens del mapa 
        # que no siguin stop words (això és molt lent, millor limitar-ho)
        # Per ara, ens limitem als candidats quantitatius si s'ha detectat intenció.
        
        logging.info(f"🎯 Candidats potencials detectats: {len(candidate_tokens)}")
        if not candidate_tokens: 
            # Fallback: si no hi ha candidats clars, retornem un missatge genèric
            return "No puc determinar candidats clars per a aquesta consulta amb la lògica actual."

        # 4. Descarregar nodes candidats en paral·lel
        logging.info("🌐 Descarregant nodes candidats...")
        candidates_data = await self.fetch_multiple_nodes(list(candidate_tokens))
        
        best_term = None
        best_score = -1.0
        scores_log = []

        # 5. Calcular Similitud Còsina
        for term, data in candidates_data.items():
            cand_emb = data.get("embedding_vector")
            if cand_emb:
                score = self.cosine_similarity(query_vector_mean, cand_emb)
                scores_log.append((term, score))
                
                if score > best_score:
                    best_score = score
                    best_term = term

        # Log de scores per depuració
        scores_log.sort(key=lambda x: x[1], reverse=True)
        logging.info(f"📊 Top 5 Scores (Cosine): {scores_log[:5]}")

        elapsed = time.time() - start_time
        logging.info(f"⏱️ Temps total de procés: {elapsed:.2f}s")

        if best_term:
            return f"Segons la meva anàlisi geomètrica, la resposta més propera semànticament és '{best_term}' (Score: {best_score:.3f})."
        
        return "No puc determinar una resposta clara amb les dades actuals."

async def main():
    print("="*60)
    print("🤖 BENVINGUT AL XAT SURAR-AINA (Inferència Geomètrica ARD)")
    print("Escriu 'sortir' per acabar.")
    print("="*60)
    
    bot = SurarChatBotARD()
    await bot.initialize()
    
    try:
        while True:
            user_input = input("\n👤 Tu: ")
            if user_input.lower() == 'sortir': break
            
            response = await bot.process_query(user_input)
            print(f"🤖 SURAR: {response}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
    print(DESCRIPCIO_FINAL_STEP35)