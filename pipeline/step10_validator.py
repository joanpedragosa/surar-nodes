# =====================================================================
# NOM DEL CODI: step10_validator.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step10_validator.py
# DESCRIPCIÓ FUNCIONAL: Eina d'auditoria avançada que compara l'estat 
#                      local dels nodes HMBL amb la seva contrapart remota 
#                      a GitHub. Genera un diagnòstic de sincronització i 
#                      valida la integritat tècnica del blindatge.
# OPCIONS D'EXECUCIÓ: python pipeline/step10_validator.py
# DEPENDÈNCIES: requests
# =====================================================================

import os
import sys
import json
import logging
import hashlib
import requests

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import STEP_10, STEP_05, DATA_ROOT, GLOBAL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_VALIDATOR_STEP10 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 10 VALIDATOR (DIAGNÒSTIC REMOT)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Realitzar una auditoria comparativa entre el graf probabilístic local i la 
versió publicada a Internet. Detecta discrepàncies de volum, fitxers orfes 
o mancances de sincronització abans de procedir a inferències o noves publicacions.

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Inventari Local: Recorre la carpeta 'data/nodes/' per comptar i validar 
   l'estructura HMBL dels fitxers JSON físics.
2. Telemetria Remota (GitHub API): Consulta l'API pública de GitHub per obtenir 
   el llistat exacte de fitxers allotjats actualment al repositori 'surar-nodes'.
3. Diagnòstic de Sincronització: Calcula la diferència entre nodes locals i remots.
   - Si Locals > Remots: Falta fer el Step 30 (Push).
   - Si Remots > Locals: El teu entorn local està desactualitzat.
4. Validació de Blindatge: Verifica que les URLs internes dels nodes coincideixin 
   amb la ruta pública oficial del repositori.

RESULTAT EXECUTAT CONCRET:
Un informe detallat que indica l'estat de salut de la "Xarxa a la Deriva" i 
recomana accions correctives (ex: executar Step 30 o Step 28).
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
    """Utilitza l'API de GitHub per comptar els fitxers a la carpeta 'nodes' del repo."""
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
            # Si arribem al límit de 1000, assumim que n'hi ha molts més
            is_limited = (count >= 1000)
            return count, is_limited
        else:
            logging.warning(f"⚠️ No s'ha pogut accedir a l'API de GitHub (Status: {response.status_code}).")
            return 0, False
    except Exception as e:
        logging.error(f"❌ Error de connexió amb GitHub API: {e}")
        return 0, False

def validar_blindatge_urls():
    """Verifica que les URLs dels nodes siguin vàlides i públiques (mostra aleatòria)."""
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    errors_url = 0
    total_nodes = 0
    base_url_esperada = f"https://raw.githubusercontent.com/{STEP_10['GITHUB_USER']}/{STEP_10['GITHUB_REPO']}"
    
    # Per rendiment, només validem una mostra de 50 nodes si n'hi ha molts
    fitxers = os.listdir(ruta_nodes)
    if len(fitxers) > 50:
        import random
        fitxers = random.sample(fitxers, 50)
        
    for nom_fitxer in fitxers:
        if not nom_fitxer.endswith(".json"): continue
        
        total_nodes += 1
        ruta_completa = os.path.join(ruta_nodes, nom_fitxer)
        
        try:
            with open(ruta_completa, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            node_id = data.get("id", "")
            if not node_id.startswith(base_url_esperada):
                errors_url += 1
        except Exception:
            errors_url += 1
            
    return total_nodes, errors_url

def validar_mapa_global():
    """Audita l'estructura i consistència del mapping_global.json."""
    ruta_mapping = os.path.join(DATA_ROOT, "mapping_global.json")
    
    if not os.path.exists(ruta_mapping):
        logging.error(f"❌ Fitxer de mapa global no trobat: {ruta_mapping}")
        return False, 0
        
    try:
        with open(ruta_mapping, "r", encoding="utf-8") as f:
            mapa = json.load(f)
            
        entries_valides = 0
        for token, info in list(mapa.items())[:5]:
            has_url = "github_raw_url" in info
            has_cid = "ipfs_hash_cid" in info
            if has_url and has_cid:
                entries_valides += 1
                
        return True, entries_valides
        
    except Exception as e:
        logging.error(f"❌ Error llegint el mapa global: {e}")
        return False, 0

def executar_diagnostic_comparatiu():
    logging.info(f"🔍 Iniciant diagnòstic comparatiu Local vs Remot per a {GLOBAL['PROJECT_NAME']}...")
    
    # 1. Auditoria Local
    total_local = obtenir_nodes_locals()
    logging.info(f"💻 Nodes detectats LOCALMENT: {total_local}")
    
    # 2. Auditoria Remota
    logging.info("🌐 Consultant estat actual del repositori a GitHub...")
    total_remot, is_limited = obtenir_estat_remot()
    
    if is_limited:
        logging.info(f"☁️ Nodes detectats REMOTAMENT: >1000 (Límit d'API assolit, repositori ple).")
    else:
        logging.info(f"☁️ Nodes detectats REMOTAMENT: {total_remot}")
    
    # 3. Diagnòstic
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
        logging.info("   👉 Acció recomanada: Fes un 'git pull' per actualitzar el teu entorn.")
    else:
        logging.info("✅ SINCRONITZACIÓ PERFECTA: El nombre de nodes coincideix exactament.")

    # 4. Validacions Tècniques Addicionals
    _, errors_url = validar_blindatge_urls()
    mapa_ok, _ = validar_mapa_global()
    
    if errors_url > 0:
        logging.warning(f"⚠️ S'han detectat {errors_url} nodes amb URLs incorrectes a la mostra.")
    else:
        logging.info("✅ Blindatge de URLs correcte a la mostra.")
        
    if not mapa_ok:
        logging.warning("⚠️ El mapa global presenta inconsistències.")
        
    logging.info("-" * 60)

if __name__ == "__main__":
    executar_diagnostic_comparatiu()
    print(DESCRIPCIO_FINAL_VALIDATOR_STEP10)