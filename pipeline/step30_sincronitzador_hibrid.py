# =====================================================================
# NOM DEL CODI: step30_sincronitzador_hibrid.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step30_sincronitzador_hibrid.py
# DESCRIPCIÓ FUNCIONAL: Motor de publicació massiva que sincronitza el graf 
#                      ARD local amb el repositori remot de GitHub mitjançant 
#                      una estratègia de commits incrementals per lots (batching). 
#                      Aquesta tècnica evita el col·lapse de memòria de Git i 
#                      garanteix la persistència de dades en entorns Windows.
# OPCIONS D'EXECUCIÓ: python pipeline/step30_sincronitzador_hibrid.py
# =====================================================================

import os
import sys
import subprocess
import logging
from datetime import datetime

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import GLOBAL, STEP_05, STEP_10, STEP_30, DATA_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_STEP30 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 30 (SINCRONITZACIÓ INCREMENTAL ARD)
================================================================================
PROPÒSIT GLOBAL DEL PROJECTE:
Materialitzar la "Xarxa a la Deriva" convertint els càlculs locals en intel·ligència 
pública accessible. Aquest mòdul tanca el cicle evolutiu publicant els artefactes 
JSON (nodes amb embeddings optimitzats, mapes i vocabulari) a Internet sense dependre de 
servidors privats ni costos de manteniment.

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Fragmentació de Càrrega (Batching): Divideix el total de nodes (ex: 24.000) en 
   grups manejables definits per 'BATCH_SIZE_COMMITS' (ex: 500 fitxers per lot).
2. Indexació Selectiva per Lot: Afegeix a Git únicament els fitxers del lot actual, 
   reduint dràsticament l'ús de RAM i evitant errors de buffer del sistema operatiu.
3. Commit Atòmic Incremental: Realitza un punt de control històric per cada lot amb 
   un missatge descriptiu i segell temporal, creant un rastre auditable de la pujada.
4. Push Final Unificat: Un cop tots els lots estan consolidats localment, executa 
   una única operació de 'git push' per enviar tota la nova estructura a GitHub.
5. Sincronització de Metadades ARD: Assegura que el 'mapping_global.json' i el 
   'vocabulari.json' també es publiquin per permetre la resolució d'URLs i la 
   consistència dels índexos en la inferència geomètrica.
6. Registre d'Auditoria Persistent: Actualitza el fitxer 'generation_history.log' 
   amb el resultat de la sincronització i el nombre total de nodes publicats.

RESULTAT EXECUTAT CONCRET:
El graf de coneixement SURAR-AINA queda publicat, versionat i accessible via URLs Raw 
públiques. Qualsevol canvi en els embeddings o metadades és immediatament visible 
per a altres agents o usuaris, permetent la inferència distribuïda en temps real.
================================================================================
"""

def executar_comando_git(comanda: list, directori: str):
    """Executa una ordre de Git gestionant codificació UTF-8."""
    try:
        resultat = subprocess.run(
            comanda, 
            cwd=directori, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding='utf-8',
            errors='ignore',
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr.strip()
        if "nothing to commit" in stderr_msg or "no changes added to commit" in stderr_msg:
            return True
        logging.warning(f"⚠️ Avís Git: {stderr_msg}")
        return False

def sincronitzar_graf_probabilistic():
    logging.info("🚀 Iniciant sincronització global del graf ARD cap a Internet...")

    ruta_sumar_root = RUTA_SUMAR_ROOT
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    ruta_log = os.path.join(DATA_ROOT, "generation_history.log")
    
    batch_size = STEP_30.get("BATCH_SIZE_COMMITS", 500)

    if not os.path.exists(ruta_nodes):
        logging.error(f"❌ Error crític: Carpeta de nodes no trobada a '{ruta_nodes}'.")
        return

    fitxers_json = [f for f in os.listdir(ruta_nodes) if f.endswith(".json")]
    total_fitxers = len(fitxers_json)

    if total_fitxers == 0:
        logging.warning("⚠️ No hi ha cap node pendent de sincronització.")
        return

    logging.info(f"📦 Preparant pujada massiva de {total_fitxers} nodes en lots de {batch_size}...")

    # 1. Afegir primer les metadades globals (Mapping i Vocabulari)
    ruta_mapping = os.path.join(DATA_ROOT, "mapping_global.json")
    if os.path.exists(ruta_mapping):
        logging.info("🗺️ Incloent 'mapping_global.json' en la sincronització...")
        executar_comando_git(["git", "add", "data/mapping_global.json"], ruta_sumar_root)
        
    ruta_vocab = STEP_10.get("VOCABULARY_FILE", os.path.join(DATA_ROOT, "vocabulari.json"))
    if os.path.exists(ruta_vocab):
        logging.info("📚 Incloent 'vocabulari.json' en la sincronització...")
        executar_comando_git(["git", "add", "data/vocabulari.json"], ruta_sumar_root)

    # 2. Processar els nodes per lots
    for i in range(0, total_fitxers, batch_size):
        batch = fitxers_json[i:i + batch_size]
        num_lot = (i // batch_size) + 1
        total_lots = (total_fitxers + batch_size - 1) // batch_size
        
        logging.info(f"🔄 Processant Lot {num_lot}/{total_lots} ({len(batch)} fitxers)...")

        for nom_fitxer in batch:
            # Utilitzem la ruta relativa correcta dins del repo
            ruta_relativa = f"data/nodes/{nom_fitxer}"
            executar_comando_git(["git", "add", ruta_relativa], ruta_sumar_root)
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        missatge = f"SURAR-AINA-ARD: Batch upload [{i+1}-{i+len(batch)}] of {total_fitxers} - {timestamp}"
        executar_comando_git(["git", "commit", "-m", missatge], ruta_sumar_root)

    logging.info("🌍 Llançant push final de tots els lots acumulats cap a GitHub...")
    ok_push = executar_comando_git(["git", "push", "origin", STEP_30.get("GITHUB_BRANCH", "main")], ruta_sumar_root)

    ara = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ok_push:
        log_missatge = f"[{ara}] - ÈXIT - Sincronització Incremental Completada. Nodes publicats: {total_fitxers}\n"
        logging.info(f"🎉 Èxit de transport: El graf ARD ({total_fitxers} nodes) ja és públic a Internet!")
    else:
        log_missatge = f"[{ara}] - TRAÇA LOCAL - Records consolidats en local, push pendent.\n"
    
    try:
        with open(ruta_log, "a", encoding="utf-8") as f:
            f.write(log_missatge)
        logging.info(f"📝 Històric actualitzat a: '{ruta_log}'")
    except Exception as e:
        logging.error(f"❌ Error escribint el log: {e}")

if __name__ == "__main__":
    logging.info(f"Executant Step 30 - Sincronitzador Híbrid Incremental per a {GLOBAL['PROJECT_NAME']}")
    sincronitzar_graf_probabilistic()
    print(DESCRIPCIO_FINAL_STEP30)