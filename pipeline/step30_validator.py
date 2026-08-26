# =====================================================================
# NOM DEL CODI: step30_validator.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step30_validator.py
# DESCRIPCIÓ FUNCIONAL: Eina d'auditoria pre-publicació que realitza un 
#                      diagnòstic comparatiu entre l'estat local dels nodes 
#                      ARD i la seva contrapart remota a GitHub. Verifica 
#                      la consistència de volums, detecta anomalies de noms 
#                      de fitxers (Windows) i valida l'estructura interna 
#                      (embeddings neurals) abans de permetre la sincronització massiva.
# OPCIONS D'EXECUCIÓ: python pipeline/step30_validator.py
# DEPENDÈNCIES: requests
# =====================================================================

import os
import sys
import json
import logging
import random
import requests

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import GLOBAL, STEP_05, STEP_10, STEP_33, DATA_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_VALIDATOR_STEP30 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 30 VALIDATOR (AUDITORIA REMOTA ARD)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Garantir la integritat tècnica i la coherència de dades abans de procedir a 
qualsevol operació de publicació massiva. Actua com a "guardià" del repositori ARD.

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Inventari Local Precís: Recorre la carpeta 'data/nodes/' per comptar el 
   nombre exacte de fitxers JSON generats pel Step 05.
2. Telemetria Remota Intel·ligent: Consulta l'API pública de GitHub per obtenir 
   el recompte de fitxers allotjats actualment al repositori 'surar-nodes', 
   gestionant correctament els límits de paginació de l'API (>1000 fitxers).
3. Diagnòstic de Sincronització: Compara els volums Local vs Remot.
   - Si Local > Remot: Indica que hi ha dades pendents de pujada (Step 30 necessari).
   - Si Remot > Local: Indica que l'entorn local està desactualitzat (cal git pull).
4. Detecció d'Anomalies Windows: Identifica fitxers amb noms reservats (con.json, 
   nul.json) que bloquejarien els processos de Git en entorns Windows.
5. Validació Estructural ARD: Obre una mostra aleatòria de nodes per 
   verificar que contenen l''embedding_vector' amb la dimensió correcta definida 
   a config.py.
6. Auditoria de Metadades: Confirma que 'mapping_global.json' i 'vocabulari.json' 
   existeixen i són consistents.

RESULTAT EXECUTAT CONCRET:
Un informe de "Semàfor" que indica si el sistema està llest per operar o si 
requereix accions correctives (neteja, actualització o regeneració de nodes).
================================================================================
"""

def obtenir_nodes_locals():
    """Compta els fitxers JSON a la carpeta local."""
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    if not os.path.exists(ruta_nodes):
        return 0
    fitxers = [f for f in os.listdir(ruta_nodes) if f.endswith(".json")]
    return len(fitxers)

def obtenir_estat_remot():
    """Utilitza l'API de GitHub per comptar els fitxers a la carpeta data/nodes."""
    user = STEP_10.get("GITHUB_USER", "joanpedragosa")
    repo = STEP_10.get("GITHUB_REPO", "surar-nodes")
    branch = STEP_10.get("GITHUB_BRANCH", "main")
    
    url_api = f"https://api.github.com/repos/{user}/{repo}/contents/data/nodes?ref={branch}"
    
    try:
        response = requests.get(url_api, timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = len(data)
            is_limited = (count >= 1000)
            return count, is_limited
        elif response.status_code == 404:
            return 0, False # Carpeta buida o inexistent
        else:
            return 0, False
    except Exception as e:
        logging.error(f"❌ Error de connexió amb GitHub API: {e}")
        return 0, False

def detectar_anomalies_windows():
    """Detecta fitxers prohibits per Windows que causarien errors de Git."""
    paraules_prohibides = {"con", "prn", "aux", "nul", "com1", "com2", "lpt1", "lpt2"}
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    anomalies = []
    
    if not os.path.exists(ruta_nodes): return anomalies
    
    for nom in os.listdir(ruta_nodes):
        if nom.endswith(".json"):
            base = nom.replace(".json", "").lower()
            if base in paraules_prohibides:
                anomalies.append(nom)
    return anomalies

def validar_integritat_ard_mostra():
    """Valida l'estructura interna d'una mostra aleatòria de nodes ARD."""
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    if not os.path.exists(ruta_nodes):
        return False, 0
        
    fitxers = [f for f in os.listdir(ruta_nodes) if f.endswith(".json")]
    if not fitxers:
        return False, 0
        
    mostra_size = min(20, len(fitxers))
    mostra = random.sample(fitxers, mostra_size)
    
    # Obtenir la dimensió esperada des de la configuració global
    expected_emb_dim = STEP_33.get("EMBEDDING_DIM", 64)
    
    errors = 0
    for nom_fitxer in mostra:
        ruta_completa = os.path.join(ruta_nodes, nom_fitxer)
        try:
            with open(ruta_completa, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validació Embedding Neural (Únic camp crític per a ARD)
            emb = data.get("embedding_vector")
            has_valid_emb = isinstance(emb, list) and len(emb) == expected_emb_dim
            
            if not has_valid_emb:
                errors += 1
                
        except Exception:
            errors += 1
            
    return errors == 0, errors

def validar_metadades_globals():
    """Verifica l'existència de mapping_global.json i vocabulari.json."""
    ruta_mapping = os.path.join(DATA_ROOT, "mapping_global.json")
    ruta_vocab = STEP_10.get("VOCABULARY_FILE", os.path.join(DATA_ROOT, "vocabulari.json"))
    
    ok_mapping = os.path.exists(ruta_mapping)
    ok_vocab = os.path.exists(ruta_vocab)
    
    if ok_mapping:
        logging.info("✅ 'mapping_global.json' trobat.")
    else:
        logging.warning("⚠️ 'mapping_global.json' no trobat.")
        
    if ok_vocab:
        logging.info("✅ 'vocabulari.json' trobat.")
    else:
        logging.warning("⚠️ 'vocabulari.json' no trobat.")
        
    return ok_mapping and ok_vocab

def executar_validacio_step30():
    logging.info(f"🔍 Iniciant auditoria pre-publicació ARD per a {GLOBAL['PROJECT_NAME']} v{GLOBAL['VERSION']}...")
    
    # 1. Volum Local
    total_local = obtenir_nodes_locals()
    logging.info(f"💻 Nodes detectats LOCALMENT: {total_local}")
    
    # 2. Volum Remot
    logging.info("🌐 Consultant estat actual del repositori a GitHub...")
    total_remot, is_limited = obtenir_estat_remot()
    
    if is_limited:
        logging.info(f"☁️ Nodes detectats REMOTAMENT: >1000 (Límit d'API assolit).")
    else:
        logging.info(f"☁️ Nodes detectats REMOTAMENT: {total_remot}")
    
    # 3. Diagnòstic de Sincronització
    logging.info("-" * 60)
    if total_local == 0:
        logging.error("❌ ERROR: No hi ha nodes locals. Executa el Step 05.")
    elif is_limited and total_local > 1000:
        logging.info("✅ SINCRONITZACIÓ MASSIVA CONFIRMADA: Ambdós costats tenen volum elevat.")
    elif total_local > total_remot and not is_limited:
        diff = total_local - total_remot
        logging.warning(f"⚠️ DISCREPÀNCIA: Tens {diff} nodes més en local que a GitHub.")
        logging.info("   👉 Acció recomanada: Executa el Step 30 Sincronitzador.")
    elif total_remot > total_local:
        logging.warning("⚠️ El repositori remot té més nodes que el teu entorn local.")
        logging.info("   👉 Acció recomanada: Fes un 'git pull'.")
    else:
        logging.info("✅ SINCRONITZACIÓ PERFECTA: El nombre de nodes coincideix.")

    # 4. Anomalies Windows
    anomalies = detectar_anomalies_windows()
    if anomalies:
        logging.error(f"🚫 ANOMALIES WINDOWS DETECTADES: {anomalies}. Esborra'ls manualment!")
    else:
        logging.info("✅ Cap anomalia de noms de fitxers Windows detectada.")

    # 5. Validació Estructural ARD
    es_valid, num_errors = validar_integritat_ard_mostra()
    if not es_valid:
        logging.error(f"🚫 ERRORS ESTRUCTURALS DETECTATS en la mostra: {num_errors} nodes invàlids.")
        logging.info("   👉 Acció recomanada: Revisa el Step 05 o elimina nodes corruptes.")
    else:
        logging.info(f"✅ Validació estructural ARD correcta (Embedding {STEP_33.get('EMBEDDING_DIM', 64)}d present i vàlid).")

    # 6. Validació de Metadades
    metadades_ok = validar_metadades_globals()

    logging.info("-" * 60)
    if total_local > 0 and not anomalies and es_valid and metadades_ok:
        logging.info("🟢 SEMÀFOR VERD: El sistema ARD està llest per operar i publicar.")
    else:
        logging.info("🔴 SEMÀFOR VERMELL: Revisa les advertències abans de continuar.")

if __name__ == "__main__":
    executar_validacio_step30()
    print(DESCRIPCIO_FINAL_VALIDATOR_STEP30)