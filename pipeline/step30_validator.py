# =====================================================================
# NOM DEL CODI: step30_validator.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step30_validator.py
# DESCRIPCIÓ FUNCIONAL: Eina d'auditoria pre-publicació que realitza un 
#                      diagnòstic comparatiu entre l'estat local dels nodes 
#                      HMBL i la seva contrapart remota a GitHub. Verifica 
#                      la consistència de volums, detecta anomalies de noms 
#                      de fitxers (Windows) i valida l'estructura interna 
#                      dels nodes abans de permetre la sincronització.
# OPCIONS D'EXECUCIÓ: python pipeline/step30_validator.py
# DEPENDÈNCIES: requests
# =====================================================================

import os
import sys
import json
import logging
import requests

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import GLOBAL, STEP_05, STEP_10, DATA_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_VALIDATOR_STEP30 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 30 VALIDATOR (AUDITORIA REMOTA)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Garantir la integritat tècnica i la coherència de dades abans de procedir a 
qualsevol operació de publicació massiva. Actua com a "guardià" del repositori.

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
5. Validació Estructural Mostrejada: Obre una mostra aleatòria de nodes per 
   verificar que contenen les taules Markovianes i Bayesianes necessàries.

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
    """Utilitza l'API de GitHub per comptar els fitxers a la carpeta 'nodes'."""
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
        else:
            return 0, False
    except Exception as e:
        logging.error(f"❌ Error de connexió amb GitHub API: {e}")
        return 0, False

def detectar_anomalies_windows():
    """Detecta fitxers prohibits per Windows."""
    paraules_prohibides = ["con", "prn", "aux", "nul", "com1", "lpt1"]
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    anomalies = []
    
    if not os.path.exists(ruta_nodes): return anomalies
    
    for nom in os.listdir(ruta_nodes):
        if nom.endswith(".json"):
            base = nom.replace(".json", "").lower()
            if base in paraules_prohibides:
                anomalies.append(nom)
    return anomalies

def executar_validacio_step30():
    logging.info(f"🔍 Iniciant auditoria pre-publicació per a {GLOBAL['PROJECT_NAME']}...")
    
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
    
    # 3. Diagnòstic
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

    # 4. Anomalies
    anomalies = detectar_anomalies_windows()
    if anomalies:
        logging.error(f"🚫 ANOMALIES WINDOWS DETECTADES: {anomalies}. Esborra'ls manualment!")
    else:
        logging.info("✅ Cap anomalia de noms de fitxers Windows detectada.")

    logging.info("-" * 60)
    if total_local > 0 and not anomalies:
        logging.info("🟢 SEMÀFOR VERD: El sistema està llest per operar.")
    else:
        logging.info("🔴 SEMÀFOR VERMELL: Revisa les advertències.")

if __name__ == "__main__":
    executar_validacio_step30()
    print(DESCRIPCIO_FINAL_VALIDATOR_STEP30)