# =====================================================================
# NOM DEL CODI: step35_xat_interactiu.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step35_xat_interactiu.py
# DESCRIPCIÓ FUNCIONAL: Interfície de xat interactiu que navega pel graf 
#                      remot (GitHub) mitjançant descàrregues asíncrones 
#                      paral·leles. Utilitza el motor HMBL per calcular 
#                      la ruta de màxima versemblança semàntica i sintàctica,
#                      amb mecanismes de resiliència per a variacions de cas.
# OPCIONS D'EXECUCIÓ: python pipeline/step35_xat_interactiu.py
# DEPENDÈNCIES: aiohttp, asyncio
# =====================================================================

import os
import sys
import json
import logging
import asyncio
import aiohttp
from collections import defaultdict

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import STEP_10, STEP_35, STOP_WORDS_CA
from pipeline.step00_contracte_global import netejar_i_tokenitzar, construir_url_node_oficial

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_STEP35 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 35 (XAT INTERACTIU HMBL)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Proporcionar una interfície de consulta en llenguatge natural que opera directament 
sobre la "Xarxa a la Deriva". Sense servidors centrals, el client descarrega només 
els fragments de coneixement necessaris per resoldre la pregunta des de GitHub.

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Parsing i Detecció d'Intenció: Neteja la consulta i identifica tokens clau.
   Implementa un sistema de 'Fallback' per provar variants de minúscules si la 
   forma original (ex: majúscules) no es troba al repositori remot.
2. Propagació Asíncrona (Asyncio): Executa múltiples crides HTTP concurrents 
   cap a GitHub Raw per descarregar els nodes dels tokens clau i els seus veïns 
   immediats, minimitzant la latència total de la resposta.
3. Motor de Puntuació Híbrida (HMBL Engine):
   - Energia Base: Freqüència del node al corpus original.
   - Boost Bayesià: Multiplicador contextual si el veí apareix al context de la pregunta.
   - Probabilitat Markoviana: Validació sintàctica de la seqüència proposta.
   - Fórmula: Score = Energia * Boost_Bayes * Prob_Markov
4. Generació Determinista: Construeix la resposta seleccionant els candidats amb 
   major puntuació híbrida, garantint traçabilitat total de cada paraula.

RESULTAT EXECUTAT CONCRET:
Una resposta precisa i explicada, generada en temps real navegant per fitxers JSON 
públics allotjats a Internet, sense dependre de cap model de llenguatge extern.
================================================================================
"""

class SurarInferenceEngine:
    def __init__(self):
        self.session = None
        self.cache_nodes = {} # Memòria cau local per a la sessió
        
    async def init_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def fetch_node(self, token: str) -> dict:
        """Descarrega un node des de GitHub amb memòria cau."""
        if token in self.cache_nodes:
            return self.cache_nodes[token]
            
        url = construir_url_node_oficial(token)
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.cache_nodes[token] = data
                    return data
        except Exception as e:
            logging.debug(f"Error descarregant node {token}: {e}")
        return None

    async def fetch_neighbors_batch(self, tokens: list) -> dict:
        """Descarrega en paral·lel els nodes dels tokens donats."""
        tasks = [self.fetch_node(t) for t in tokens]
        results = await asyncio.gather(*tasks)
        # Retorna un diccionari {token: dades} filtrant els nuls
        return {t: r for t, r in zip(tokens, results) if r is not None}

    def calculate_hmbl_score(self, candidate_token: str, query_tokens: list, source_node: dict) -> float:
        """Calcula la puntuació híbrida per a un candidat."""
        if not source_node: return 0.0
        
        # 1. Energia Base (normalitzada per evitar valors massa grans)
        base_energy = min(10.0, source_node.get("frequency", 1)) / 10.0
        
        # 2. Boost Bayesià (mitjana dels boosts dels tokens de la pregunta)
        bayesian_context = source_node.get("bayesian_context", {})
        boosts = []
        for q_token in query_tokens:
            # Provem tant el token original com el seu equivalent en minúscules
            if q_token in bayesian_context:
                boosts.append(bayesian_context[q_token].get("posterior_boost", 1.0))
            elif q_token.lower() in bayesian_context:
                boosts.append(bayesian_context[q_token.lower()].get("posterior_boost", 1.0))
        
        avg_boost = sum(boosts) / len(boosts) if boosts else 1.0
        
        # 3. Probabilitat Markoviana
        markov_trans = source_node.get("markov_transitions", {})
        max_markov_prob = 0.0
        for q_token in query_tokens:
            if q_token in markov_trans:
                max_markov_prob = max(max_markov_prob, markov_trans[q_token])
            elif q_token.lower() in markov_trans:
                max_markov_prob = max(max_markov_prob, markov_trans[q_token.lower()])
        
        # Suavitzat per evitar zeros absoluts si no hi ha connexió directa però sí boost
        if max_markov_prob == 0.0 and not boosts:
             max_markov_prob = 0.05 

        # Fórmula Final
        score = base_energy * avg_boost * (max_markov_prob + 0.1) 
        return round(score, 4)

    async def process_query(self, query: str) -> str:
        """Processa una pregunta i genera una resposta."""
        await self.init_session()
        
        # 1. Parsing
        query_tokens = netejar_i_tokenitzar(query)
        if not query_tokens:
            await self.close_session()
            return "No he entès la pregunta."
            
        logging.info(f"🔍 Tokens de consulta detectats: {query_tokens}")
        
        # CORRECCIÓ DE RESILIÈNCIA: Crear llista de tokens de reserva (minúscules)
        fallback_tokens = [t.lower() for t in query_tokens]
        all_search_tokens = list(set(query_tokens + fallback_tokens))
        
        # 2. Propagació Asíncrona (Descarregar nodes clau)
        nodes_data = await self.fetch_neighbors_batch(all_search_tokens)
        
        if not nodes_data:
            await self.close_session()
            return "No he trobat informació sobre aquests conceptes a la xarxa."
            
        logging.info(f"📥 Nodes descarregats correctament: {list(nodes_data.keys())}")

        # 3. Recollida de Candidats (Veïns dels nodes clau)
        candidates = defaultdict(float)
        
        for token, data in nodes_data.items():
            # Afegir el propi token com a candidat potencial
            score = self.calculate_hmbl_score(token, query_tokens, data)
            if score > candidates[token]:
                candidates[token] = score
                
            # Afegir veïns de transicions markovianes
            for neighbor, prob in data.get("markov_transitions", {}).items():
                if neighbor not in query_tokens and neighbor.lower() not in [qt.lower() for qt in query_tokens] and neighbor not in STOP_WORDS_CA:
                    # Per als veïns, utilitzem les dades del node origen per al càlcul inicial
                    temp_score = self.calculate_hmbl_score(neighbor, query_tokens, data) 
                    if temp_score > candidates[neighbor]:
                        candidates[neighbor] = temp_score
                        
        # Ordenar candidats per puntuació
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:5]
        
        await self.close_session()
        
        # 4. Generació de Resposta
        if not sorted_candidates or sorted_candidates[0][1] < STEP_35["MIN_CONFIDENCE_SCORE"]:
            return "No estic segur de la resposta basada en el meu graf actual."
            
        # Construir resposta simple amb els top candidats
        top_answer = sorted_candidates[0][0]
        explanation = f"Segons el meu graf, la resposta més probable és '{top_answer}' (Score: {sorted_candidates[0][1]})."
        
        if len(sorted_candidates) > 1:
            alternatives = ", ".join([c[0] for c in sorted_candidates[1:3]])
            explanation += f" Altres possibilitats: {alternatives}."
            
        return explanation

def iniciar_xat():
    print("="*60)
    print("🤖 BENVINGUT AL XAT SURAR-AINA (Model HMBL Distribuït)")
    print("Escriu 'sortir' per acabar.")
    print("="*60)
    
    engine = SurarInferenceEngine()
    
    while True:
        try:
            user_input = input("\n👤 Tu: ")
            if user_input.lower() in ["sortir", "exit", "quit"]:
                break
                
            # Executar la inferència asíncrona dins del bucle síncron
            resposta = asyncio.run(engine.process_query(user_input))
            print(f"🤖 SURAR: {resposta}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Error inesperat: {e}")

if __name__ == "__main__":
    iniciar_xat()
    print(DESCRIPCIO_FINAL_STEP35)