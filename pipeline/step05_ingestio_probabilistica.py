# =====================================================================
# NOM DEL CODI: step05_ingestio_probabilistica.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step05_ingestio_probabilistica.py
# DESCRIPCIÓ FUNCIONAL: Motor d'ingestió de dades brutes per a l'arquitectura ARD.
#                      Descarrega el dataset CatalanQA, neteja el text, construeix 
#                      el vocabulari global i inicialitza els nodes JSON amb 
#                      embeddings aleatoris preparats per a l'entrenament Keras.
# OPCIONS D'EXECUCIÓ: python pipeline/step05_ingestio_probabilistica.py
# DEPENDÈNCIES: datasets, numpy, json
# =====================================================================

import os
import sys
import json
import logging
import re
import numpy as np
from collections import Counter

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import STEP_05, DATA_ROOT, STOP_WORDS_CA, STEP_10, STEP_33
from pipeline.step00_contracte_global import (
    normalitzar_token_català, 
    carregar_o_inicialitzar_vocabulari,
    afegir_al_vocabulari,
    guardar_vocabulari
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_STEP05 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 05 (INGESTIÓ ARD)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Preparar les dades brutes per a l'entrenament de Deep Learning.
1. Generar 'aina_corpus.txt' netejat (format: Pregunta? Resposta).
2. Construir 'vocabulari.json' consistent per a la capa Embedding de Keras.
3. Inicialitzar nodes JSON amb embeddings aleatoris (punt de partida per a Step 33).

LOGICA DE FUNCIONAMENT INTERN:
1. Ingestió Telemàtica: Descarrega 'projecte-aina/catalanqa'.
2. Neteja Lingüística: Normalització catalana, NER bàsic i filtratge de stop-words.
3. Construcció de Vocabulari: Mappeig token -> índex numèric únic.
4. Inicialització de Nodes: Creació de fitxers JSON amb vectors d'embedding 
   inicials (aleatoris controlats) que seran optimitzats posteriorment.

RESULTAT EXECUTAT CONCRET:
Corpus net, vocabulari global i carpeta 'data/nodes/' amb estructures bàsiques 
preparades per rebre la intel·ligència semàntica durant l'entrenament.
================================================================================
"""

def extreure_text_resposta(answers_raw):
    """Funció robusta per extreure el text net de qualsevol estructura de resposta."""
    if not answers_raw:
        return ""
    if isinstance(answers_raw, dict):
        text_field = answers_raw.get("text", [])
        if isinstance(text_field, list) and len(text_field) > 0:
            return str(text_field[0]).strip()
        elif isinstance(text_field, str):
            return text_field.strip()
    if isinstance(answers_raw, list):
        if len(answers_raw) > 0:
            primer_element = answers_raw[0]
            if isinstance(primer_element, dict):
                return str(primer_element.get("text", "")).strip()
            else:
                return str(primer_element).strip()
    if isinstance(answers_raw, str):
        return answers_raw.strip()
    return ""

def detectar_i_unir_noms_propis(text: str) -> str:
    """Detecta seqüències de paraules que comencen per majúscula i les uneix amb '_'."""
    patro = r'\b([A-ZÀÈÍÒÚÇ][a-zàèíòuç]*)\s+([A-ZÀÈÍÒÚÇ][a-zàèíòuç]*)\b'
    while re.search(patro, text):
        text = re.sub(patro, r'\1_\2', text)
    return text

def netejar_i_tokenitzar_text(text: str) -> list:
    """Aplica NER, normalització i filtratge de stop-words."""
    text_amb_entitats = detectar_i_unir_noms_propis(text)
    # Mantenim lletres, accents catalans i guions baixos
    text_net = re.sub(r"[^\w\sçàéèíóòúü_]", " ", text_amb_entitats, flags=re.UNICODE)
    
    tokens_nets = []
    for p in text_net.split():
        if len(p) < 2 or p.isdigit(): continue
        if p not in STOP_WORDS_CA:
            token_segur = normalitzar_token_català(p)
            if token_segur and token_segur not in STOP_WORDS_CA:
                tokens_nets.append(token_segur)
    return tokens_nets

def generar_embedding_inicial(dim: int, seed: int) -> list:
    """
    Genera un vector d'embedding inicial aleatori però determinista.
    Aquest vector serà el punt de partida que el model Keras ajustarà.
    """
    rng = np.random.RandomState(seed)
    # Inicialització amb distribució uniforme petita per estabilitat inicial
    embedding = rng.uniform(-0.05, 0.05, dim)
    return embedding.tolist()

def generar_nodes_inicials():
    """Funció principal que executa el pipeline d'ingestió ARD."""
    logging.info("🚀 Iniciant Ingestió de Dades Brutes (ARD) des de Hugging Face...")
    
    try:
        from datasets import load_dataset
        logging.info(f"🌐 Carregant dataset '{STEP_05['DATASET_ID']}'...")
        dataset = load_dataset(STEP_05["DATASET_ID"], split=STEP_05["SPLIT"])
    except ImportError:
        logging.error("❌ Error: La llibreria 'datasets' no està instal·lada. Executa: pip install datasets")
        return
    except Exception as e:
        logging.error(f"❌ Error carregant dataset: {e}")
        return

    # Preparar directoris
    output_dir = STEP_05["OUTPUT_LOCAL_DIR"]
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(DATA_ROOT, exist_ok=True)

    frequencies_global = Counter()
    linies_corpus = []
    mostres_a_processar = min(len(dataset), STEP_05["MAX_SAMPLES_INGESTIO"])
    
    # Inicialitzar Vocabulari Global
    vocabulari = carregar_o_inicialitzar_vocabulari()
    
    # Obtenir la dimensió d'embedding des de la configuració global
    embedding_dim = STEP_33.get("EMBEDDING_DIM", 64)
    logging.info(f"📐 Dimensió d'embedding configurada: {embedding_dim}")

    logging.info(f"Processant {mostres_a_processar} mostres del dataset...")

    for idx in range(mostres_a_processar):
        try:
            mostra = dataset[idx]
            question = str(mostra.get("question", "")).strip()
            text_resposta = extreure_text_resposta(mostra.get("answers"))
            
            if question and text_resposta:
                # Format estandarditzat per al corpus
                linea_neta = f"{question} {text_resposta}"
                linies_corpus.append(linea_neta)
                
                tokens = netejar_i_tokenitzar_text(linea_neta)
                
                # Actualitzar Vocabulari i Freqüències
                for token in tokens:
                    vocabulari = afegir_al_vocabulari(token, vocabulari)
                    frequencies_global[token] += 1
                        
        except Exception as e:
            continue

    # Guardar Corpus Net
    if linies_corpus:
        with open(STEP_05["CORPUS_FILE_TXT"], "w", encoding="utf-8") as f:
            for linea in linies_corpus:
                f.write(linea + "\n")
        logging.info(f"✅ Corpus guardat a: {STEP_05['CORPUS_FILE_TXT']} ({len(linies_corpus)} línies)")

    # Guardar Vocabulari Global
    guardar_vocabulari(vocabulari)

    logging.info("💾 Generant nodes JSON inicials amb Embeddings Aleatoris...")
    nodes_generats = 0
    max_nodes = STEP_05["MAX_NODES_PRODUCCIO"]
    # Ordenem per freqüència per garantir que els tokens més importants tenen IDs baixos si calgués
    nodes_seleccionats = frequencies_global.most_common(max_nodes)
    
    for token, freq_val in nodes_seleccionats:
        if freq_val < STEP_05["MIN_FREQ_THRESHOLD"]: continue
        
        # Generar embedding inicial aleatori basat en la freqüència com a seed (determinista)
        embedding_inicial = generar_embedding_inicial(embedding_dim, seed=freq_val)

        # Dades bàsiques del node (sense Markov/Bayes complexos)
        node_data = {
            "concept": token,
            "frequency": freq_val,
            "embedding_vector": embedding_inicial, # Vector inicial per a Keras
            "edges": [] 
        }
        
        ruta_node = os.path.join(output_dir, f"{token}.json")
        with open(ruta_node, "w", encoding="utf-8") as f:
            json.dump(node_data, f, ensure_ascii=False, indent=2)
            
        nodes_generats += 1
        
    logging.info(f"🏁 Procés finalitzat. {nodes_generats} nodes inicials generats a {output_dir}")

if __name__ == "__main__":
    generar_nodes_inicials()
    print(DESCRIPCIO_FINAL_STEP05)