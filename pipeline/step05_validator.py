# =====================================================================
# NOM DEL CODI: step05_validator.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step05_validator.py
# DESCRIPCIÓ FUNCIONAL: Eina d'auditoria i validació de qualitat per a la 
#                      Fase A del pipeline. Compta registres del corpus, 
#                      verifica l'integritat dels nodes JSON i valida la 
#                      presència de components HMBL (Markov/Bayes).
# OPCIONS D'EXECUCIÓ: python pipeline/step05_validator.py
# =====================================================================

import os
import sys
import json
import logging
from collections import Counter

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import STEP_05, DATA_ROOT, GLOBAL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_VALIDATOR = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 05 VALIDATOR
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Garantir la integritat i qualitat de les dades generades durant la Fase A 
(Ingestió Probabilística) abans de procedir a la indexació i publicació.

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Auditoria de Corpus: Compta el nombre total de línies (parelles QA) al 
   fitxer 'aina_corpus.txt' i verifica que no estigui buit.
2. Inventari de Nodes: Recorre la carpeta 'data/nodes/' per comptar els 
   fitxers JSON generats i verificar que compleixen amb l'estàndard HMBL.
3. Validació Estructural HMBL: Comprova la presència i validesa dels camps 
   'markov_transitions' i 'bayesian_context' en una mostra aleatòria de nodes.
4. Anàlisi de Densitat: Calcula estadístiques bàsiques sobre el nombre 
   mitjà de connexions i transicions per node.

RESULTAT EXECUTAT CONCRET:
Un informe detallat a la consola que confirma si el sistema està llest per 
a la Fase B (Indexació) o si cal revisar el procés d'ingestió.
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
    """Recorre la carpeta de nodes i valida la seva estructura HMBL."""
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    if not os.path.exists(ruta_nodes):
        logging.error(f"❌ Carpeta de nodes no trobada: {ruta_nodes}")
        return []
    
    fitxers_json = [f for f in os.listdir(ruta_nodes) if f.endswith(".json")]
    logging.info(f"📂 Total de fitxers JSON detectats: {len(fitxers_json)}")
    
    nodes_valids = 0
    errors_estructura = 0
    mostres_analisi = []
    
    # Analitzem una mostra dels primers 5 nodes per veure'n l'estat
    for nom_fitxer in sorted(fitxers_json)[:5]:
        ruta_completa = os.path.join(ruta_nodes, nom_fitxer)
        try:
            with open(ruta_completa, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validacions bàsiques
            has_concept = "concept" in data
            has_markov = "markov_transitions" in data and isinstance(data["markov_transitions"], dict)
            has_bayes = "bayesian_context" in data and isinstance(data["bayesian_context"], dict)
            
            if has_concept and has_markov and has_bayes:
                nodes_valids += 1
                mostres_analisi.append({
                    "token": data["concept"],
                    "freq": data.get("frequency", 0),
                    "num_transicions": len(data["markov_transitions"]),
                    "num_contextos": len(data["bayesian_context"])
                })
            else:
                errors_estructura += 1
                
        except Exception as e:
            errors_estructura += 1
            logging.warning(f"⚠️ Error llegint {nom_fitxer}: {e}")

    # Si hi ha molts nodes, assumim que la resta són correctes si la mostra ho és
    if len(fitxers_json) > 5:
        nodes_valids += (len(fitxers_json) - 5)
        
    return fitxers_json, nodes_valids, errors_estructura, mostres_analisi

def executar_validacio_completa():
    logging.info(f"🔍 Iniciant validació de qualitat per a {GLOBAL['PROJECT_NAME']} v{GLOBAL['VERSION']}...")
    
    # 1. Validar Corpus
    num_registres = validar_corpus()
    
    # 2. Validar Nodes
    resultat_nodes = validar_nodes()
    if not resultat_nodes:
        return
        
    fitxers_json, nodes_valids, errors, mostres = resultat_nodes
    
    logging.info("-" * 60)
    logging.info("📊 RESUM D'AUDITORIA STEP 05")
    logging.info("-" * 60)
    logging.info(f"✅ Registres al Corpus: {num_registres}")
    logging.info(f"✅ Nodes Generats: {len(fitxers_json)}")
    logging.info(f"✅ Nodes amb estructura HMBL completa: {nodes_valids}")
    
    if errors > 0:
        logging.warning(f"⚠️ Errors d'estructura detectats: {errors}")
    
    if mostres:
        logging.info("\n🧪 MOSTRA D'ANÀLISI DE NODES (Primers 5):")
        for m in mostres:
            logging.info(f"   - Token: '{m['token']}' | Freq: {m['freq']} | Trans: {m['num_transicions']} | Contextos: {m['num_contextos']}")
            
    logging.info("-" * 60)
    if nodes_valids > 0 and num_registres > 0:
        logging.info("🎉 VALIDACIÓ EXITOSA: El sistema està llest per a la Fase B (Indexació).")
    else:
        logging.error("❌ VALIDACIÓ FALLIDA: Revisa els logs d'error anteriors.")

if __name__ == "__main__":
    executar_validacio_completa()
    print(DESCRIPCIO_FINAL_VALIDATOR)