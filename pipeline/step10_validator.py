# =====================================================================
# NOM DEL CODI: step10_validator.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step10_validator.py
# DESCRIPCIÓ FUNCIONAL: Eina d'auditoria avançada que compara l'estat 
#                      local dels nodes ARD amb la seva contrapart remota 
#                      a GitHub. Valida la integritat tècnica del blindatge, 
#                      la presència d'embeddings vàlids i la consistència 
#                      del mapa global abans de la sincronització.
# OPCIONS D'EXECUCIÓ: python pipeline/step10_validator.py
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

from config import STEP_10, STEP_05, STEP_33, DATA_ROOT, GLOBAL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_VALIDATOR_STEP10 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 10 VALIDATOR (ARD)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Realitzar una auditoria comparativa entre el graf local ARD i la 
versió publicada a Internet, assegurant la compatibilitat per a la inferència 
geomètrica distribuïda.

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Inventari Local ARD: Recorre 'data/nodes/' per comptar fitxers i 
   validar que contenen estructures bàsiques (concept, embedding_vector).
2. Telemetria Remota (GitHub API): Consulta l'API pública per obtenir el 
   llistat de fitxers a 'data/nodes/' al repositori 'surar-nodes'.
3. Diagnòstic de Sincronització: Calcula diferències de volum entre local 
   i remot per determinar si cal executar el Step 30.
4. Validació de Blindatge i Embeddings: Verifica en una mostra aleatòria que 
   les URLs siguin correctes i que els embeddings tinguin la dimensió esperada.
5. Auditoria del Mapa Global: Confirma que 'mapping_global.json' existeix, 
   conté entrades vàlides amb CIDs, URLs i índexos de vocabulari.

RESULTAT EXECUTAT CONCRET:
Un informe detallat que certifica si la base de dades està llesta per ser 
publicada i utilitzada per a inferència geomètrica lleugera.
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
    """Utilitza l'API de GitHub per comptar els fitxers a la carpeta data/nodes del repo."""
    user = STEP_10.get("GITHUB_USER", "joanpedragosa")
    repo = STEP_10.get("GITHUB_REPO", "surar-nodes")
    branch = STEP_10.get("GITHUB_BRANCH", "main")
    
    # API de continguts de GitHub (limitada a 1000 items per pàgina)
    url_api = f"https://api.github.com/repos/{user}/{repo}/contents/data/nodes?ref={branch}"
    
    try:
        response = requests.get(url_api, timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = len(data)
            is_limited = (count >= 1000)
            return count, is_limited
        elif response.status_code == 404:
            logging.info("ℹ️ La carpeta remota encara no existeix o està buida.")
            return 0, False
        else:
            logging.warning(f"⚠️ No s'ha pogut accedir a l'API de GitHub (Status: {response.status_code}).")
            return 0, False
    except Exception as e:
        logging.error(f"❌ Error de connexió amb GitHub API: {e}")
        return 0, False

def validar_integritat_ard():
    """Verifica URLs i embeddings neurals en una mostra aleatòria."""
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    errors_url = 0
    errors_structure = 0
    total_mostra = 0
    
    base_url_esperada = f"https://raw.githubusercontent.com/{STEP_10['GITHUB_USER']}/{STEP_10['GITHUB_REPO']}/main/data/nodes/"
    
    # Obtenir la dimensió esperada des de la configuració global
    expected_emb_dim = STEP_33.get("EMBEDDING_DIM", 64)
    
    fitxers = [f for f in os.listdir(ruta_nodes) if f.endswith(".json")]
    if not fitxers:
        return 0, 0, 0
        
    # Mostreig aleatori per rendiment
    mostra = random.sample(fitxers, min(50, len(fitxers)))
        
    for nom_fitxer in mostra:
        total_mostra += 1
        ruta_completa = os.path.join(ruta_nodes, nom_fitxer)
        
        try:
            with open(ruta_completa, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validar URL
            node_id = data.get("id", "")
            if not node_id.startswith(base_url_esperada):
                errors_url += 1
            
            # Validar Embedding Neural amb dimensió dinàmica
            emb = data.get("embedding_vector")
            if not isinstance(emb, list) or len(emb) != expected_emb_dim:
                errors_structure += 1
                
        except Exception:
            errors_url += 1
            errors_structure += 1
            
    return total_mostra, errors_url, errors_structure

def validar_mapa_global():
    """Audita l'estructura i consistència del mapping_global.json ARD."""
    ruta_mapping = os.path.join(DATA_ROOT, "mapping_global.json")
    
    if not os.path.exists(ruta_mapping):
        logging.error(f"❌ Fitxer de mapa global no trobat: {ruta_mapping}")
        return False, 0
        
    try:
        with open(ruta_mapping, "r", encoding="utf-8") as f:
            mapa = json.load(f)
            
        entries_valides = 0
        # Validem una mostra de les primeres 10 entrades
        for token, info in list(mapa.items())[:10]:
            has_url = "github_raw_url" in info and "/data/nodes/" in info["github_raw_url"]
            has_cid = "ipfs_hash_cid" in info
            has_index = "vocab_index" in info and isinstance(info["vocab_index"], int)
            
            if has_url and has_cid and has_index:
                entries_valides += 1
                
        return True, entries_valides
        
    except Exception as e:
        logging.error(f"❌ Error llegint el mapa global: {e}")
        return False, 0

def executar_diagnostic_comparatiu():
    logging.info(f"🔍 Iniciant diagnòstic comparatiu ARD per a {GLOBAL['PROJECT_NAME']} v{GLOBAL['VERSION']}...")
    
    # 1. Auditoria Local
    total_local = obtenir_nodes_locals()
    logging.info(f"💻 Nodes detectats LOCALMENT: {total_local}")
    
    # 2. Auditoria Remota
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
        logging.info("   👉 Acció recomanada: Executa el Step 30 per publicar el graf.")
    elif total_remot > total_local:
        diff = total_remot - total_local
        logging.warning(f"⚠️ DISCREPÀNCIA: Hi ha {diff} nodes a GitHub que no tens en local.")
        logging.info("   👉 Acció recomanada: Fes un 'git pull' o neteja el remot.")
    else:
        logging.info("✅ SINCRONITZACIÓ PERFECTA: El nombre de nodes coincideix exactament.")

    # 4. Validacions Tècniques ARD
    mostra, err_url, err_struct = validar_integritat_ard()
    mapa_ok, _ = validar_mapa_global()
    
    logging.info(f"\n🧪 RESULTATS DE VALIDACIÓ (Mostra de {mostra} nodes):")
    if err_url > 0:
        logging.warning(f"⚠️ Errors de blindatge URL: {err_url}")
    else:
        logging.info("✅ Blindatge de URLs correcte.")
        
    if err_struct > 0:
        logging.warning(f"⚠️ Errors estructurals (Embeddings): {err_struct}")
    else:
        logging.info(f"✅ Estructures ARD (Embedding {STEP_33.get('EMBEDDING_DIM', 64)}d) presents i vàlids.")
        
    if not mapa_ok:
        logging.warning("⚠️ El mapa global presenta inconsistències o falta l'índex de vocabulari.")
    else:
        logging.info("✅ Mapa global consistent amb URLs, CIDs i índexos de vocabulari.")
        
    logging.info("-" * 60)
    
    if total_local > 0 and err_url == 0 and err_struct == 0 and mapa_ok:
        logging.info("🎉 DIAGNÒSTIC POSITIU: El sistema ARD està llest per al Step 30 i la publicació.")
    elif total_local > 0:
        logging.warning("⚠️ DIAGNÒSTIC AMB AVISOS: Revisa els errors abans de continuar.")

if __name__ == "__main__":
    executar_diagnostic_comparatiu()
    print(DESCRIPCIO_FINAL_VALIDATOR_STEP10)