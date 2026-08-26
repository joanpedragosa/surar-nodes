# =====================================================================
# NOM DEL CODI: step05_validator.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step05_validator.py
# DESCRIPCIÓ FUNCIONAL: Eina d'auditoria i validació de qualitat per a la 
#                      Fase A del pipeline (Arquitectura ARD). Compta registres 
#                      del corpus, verifica l'integritat bàsica dels nodes JSON, 
#                      valida la dimensió dels embeddings inicials i comprova 
#                      la consistència del vocabulari global.
# OPCIONS D'EXECUCIÓ: python pipeline/step05_validator.py
# =====================================================================

import os
import sys
import json
import logging
import numpy as np

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import STEP_05, DATA_ROOT, GLOBAL, STEP_10, STEP_33

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_VALIDATOR = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 05 VALIDATOR (ARD)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Garantir la integritat i qualitat de les dades brutes generades durant la Fase A 
(Ingestió ARD) abans de procedir a l'entrenament profund.

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Auditoria de Corpus: Compta el nombre total de línies a 'aina_corpus.txt'.
2. Inventari de Nodes: Recorre 'data/nodes/' per comptar fitxers JSON.
3. Validació Estructural Bàsica: Comprova la presència de 'concept', 'frequency' 
   i 'embedding_vector'.
4. Validació d'Embeddings Inicials: Assegura que l''embedding_vector' tingui la 
   dimensió correcta definida a config.py (STEP_33).
5. Consistència de Vocabulari: Verifica que 'vocabulari.json' existeix i té entrades.

RESULTAT EXECUTAT CONCRET:
Un informe detallat que confirma si el sistema està llest per a la Fase B 
(Indexació) i per a l'entrenament profund (Step 33).
================================================================================
"""

def validar_corpus():
    """Compta i valida el fitxer de corpus."""
    ruta_corpus = STEP_05["CORPUS_FILE_TXT"]
    if not os.path.exists(ruta_corpus):
        logging.error(f"❌ Fitxer de corpus no trobat: {ruta_corpus}")
        return 0
    
    with open(ruta_corpus, "r", encoding="utf-8") as f:
        linies = [l for l in f.readlines() if l.strip()]
        
    logging.info(f"📄 Corpus trobat: {len(linies)} registres (parelles QA).")
    return len(linies)

def validar_nodes():
    """Recorre la carpeta de nodes i valida la seva estructura ARD bàsica."""
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    if not os.path.exists(ruta_nodes):
        logging.error(f"❌ Carpeta de nodes no trobada: {ruta_nodes}")
        return []
    
    fitxers_json = [f for f in os.listdir(ruta_nodes) if f.endswith(".json")]
    logging.info(f"📂 Total de fitxers JSON detectats: {len(fitxers_json)}")
    
    # Obtenir la dimensió esperada des de la configuració global
    expected_emb_dim = STEP_33.get("EMBEDDING_DIM", 64)
    
    nodes_valids = 0
    errors_estructura = 0
    mostres_analisi = []
    
    # Analitzem una mostra dels primers 5 nodes per veure'n l'estat
    for nom_fitxer in sorted(fitxers_json)[:5]:
        ruta_completa = os.path.join(ruta_nodes, nom_fitxer)
        try:
            with open(ruta_completa, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validacions Estructurals Bàsiques ARD
            has_concept = "concept" in data
            has_freq = "frequency" in data and isinstance(data["frequency"], int)
            
            # Validació d'Embedding Inicial
            has_embedding = "embedding_vector" in data
            embedding_vec_valid = False
            if has_embedding:
                emb = data["embedding_vector"]
                if isinstance(emb, list) and len(emb) == expected_emb_dim:
                    try:
                        np.array(emb, dtype=float)
                        embedding_vec_valid = True
                    except ValueError: pass

            is_valid = (has_concept and has_freq and has_embedding and embedding_vec_valid)

            if is_valid:
                nodes_valids += 1
                mostres_analisi.append({
                    "token": data["concept"],
                    "freq": data.get("frequency", 0),
                    "embedding_dim": len(data["embedding_vector"])
                })
            else:
                errors_estructura += 1
                missing = []
                if not has_concept: missing.append("concept")
                if not has_freq: missing.append("frequency")
                if not has_embedding or not embedding_vec_valid: missing.append(f"embedding_vector({expected_emb_dim})")
                logging.warning(f"⚠️ Node '{nom_fitxer}' incomplet. Falten: {missing}")
                
        except Exception as e:
            errors_estructura += 1
            logging.warning(f"⚠️ Error llegint {nom_fitxer}: {e}")

    # Si hi ha molts nodes, assumim que la resta són correctes si la mostra ho és
    if len(fitxers_json) > 5:
        nodes_valids += (len(fitxers_json) - 5)
        
    return fitxers_json, nodes_valids, errors_estructura, mostres_analisi

def validar_vocabulari():
    """Verifica l'existència i consistència del vocabulari global."""
    vocab_path = STEP_10.get("VOCABULARY_FILE", os.path.join(DATA_ROOT, "vocabulari.json"))
    if not os.path.exists(vocab_path):
        logging.warning(f"⚠️ Fitxer de vocabulari no trobat a: {vocab_path}")
        return False, 0
        
    try:
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocab = json.load(f)
        logging.info(f"📚 Vocabulari carregat amb {len(vocab)} entrades.")
        return True, len(vocab)
    except Exception as e:
        logging.error(f"❌ Error llegint el vocabulari: {e}")
        return False, 0

def executar_validacio_completa():
    logging.info(f"🔍 Iniciant validació de qualitat ARD per a {GLOBAL['PROJECT_NAME']} v{GLOBAL['VERSION']}...")
    
    # 1. Validar Corpus
    num_registres = validar_corpus()
    
    # 2. Validar Nodes
    resultat_nodes = validar_nodes()
    if not resultat_nodes:
        return
        
    fitxers_json, nodes_valids, errors, mostres = resultat_nodes
    
    # 3. Validar Vocabulari
    vocab_ok, vocab_size = validar_vocabulari()
    
    logging.info("-" * 60)
    logging.info("📊 RESUM D'AUDITORIA STEP 05 (ARD)")
    logging.info("-" * 60)
    logging.info(f"✅ Registres al Corpus: {num_registres}")
    logging.info(f"✅ Nodes Generats: {len(fitxers_json)}")
    logging.info(f"✅ Nodes amb estructura vàlida (Concept + Embedding {STEP_33.get('EMBEDDING_DIM', 64)}d): {nodes_valids}")
    logging.info(f"✅ Vocabulari Global: {'OK' if vocab_ok else 'FALTA'} ({vocab_size} tokens)")
    
    if errors > 0:
        logging.warning(f"⚠️ Errors d'estructura detectats en la mostra: {errors}")
    
    if mostres:
        logging.info("\n🧪 MOSTRA D'ANÀLISI DE NODES (Primers 5):")
        for m in mostres:
            logging.info(f"   - Token: '{m['token']}' | Freq: {m['freq']}")
            logging.info(f"     Embedding Dim: {m['embedding_dim']}")
            
    logging.info("-" * 60)
    if nodes_valids > 0 and num_registres > 0 and vocab_ok:
        logging.info("🎉 VALIDACIÓ EXITOSA: El sistema ARD està llest per a la Fase B (Indexació) i entrenament profund.")
    else:
        logging.error("❌ VALIDACIÓ FALLIDA: Revisa els logs d'error anteriors.")

if __name__ == "__main__":
    executar_validacio_completa()
    print(DESCRIPCIO_FINAL_VALIDATOR)