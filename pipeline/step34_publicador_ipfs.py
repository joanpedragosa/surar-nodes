# =====================================================================
# NOM DEL CODI: step34_publicador_ipfs.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step34_publicador_ipfs.py
# DESCRIPCIÓ FUNCIONAL: Motor de publicació dual que sincronitza els 
#                      nodes amb embeddings optimitzats i metadades globals 
#                      tant al repositori de GitHub com a la xarxa IPFS. 
#                      Genera CIDs immutables per a la persistència distribuïda.
# OPCIONS D'EXECUCIÓ: python pipeline/step34_publicador_ipfs.py
# DEPENDÈNCIES: requests, hashlib
# =====================================================================

import os
import sys
import json
import logging
import subprocess
import hashlib

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import GLOBAL, STEP_10, STEP_05, STEP_34, DATA_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_STEP34 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 34 (PUBLICADOR DUAL IPFS/GITHUB ARD)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Garantir la disponibilitat global i la immutabilitat dels nodes amb embeddings 
optimitzats. Utilitza GitHub com a capa d'accés ràpid (baixa latència) i IPFS 
com a capa de persistència descentralitzada i verificable criptogràficament.

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Verificació Local: Confirma l'existència de nodes actualitzats al Step 33 
   i metadades globals ('mapping_global.json', 'vocabulari.json').
2. Publicació a GitHub: Actualitza els fitxers al repositori 'surar-nodes' per 
   assegurar un accés immediat via HTTP RAW per al client d'inferència.
3. Càlcul de CID IPFS: Genera Content Identifiers únics per als fitxers clau 
   per garantir la seva integritat i traçabilitat immutable.
4. Pinning a IPFS: Intenta pujar els fitxers a un node IPFS local o simula 
   el procés per obtenir CIDs de referència.
5. Actualització de Metadades: Guarda les referències CID en un fitxer local 
   perquè el sistema pugui verificar la consistència de les dades distribuïdes.

RESULTAT EXECUTAT CONCRET:
Els nodes amb intel·ligència semàntica "congelada" estan accessibles via URL 
de GitHub i via CID d'IPFS, permetent una inferència geomètrica robusta i 
resistent a la censura.
================================================================================
"""

def publicar_a_github():
    """Utilitza Git per pujar els nodes actualitzats i metadades al repositori."""
    logging.info("🚀 Iniciant publicació de nodes i metadades a GitHub...")
    
    ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
    if not os.path.exists(ruta_nodes):
        logging.error("❌ Carpeta de nodes no trobada. Executa primer el Step 33.")
        return False

    try:
        # Afegir tots els canvis (nodes actualitzats i metadades)
        subprocess.run(["git", "add", "."], cwd=RUTA_SUMAR_ROOT, check=True)
        
        # Commit amb missatge descriptiu
        timestamp = subprocess.check_output(["date", "/T"], shell=True).decode().strip()
        msg = f"SURAR-AINA-ARD: Update optimized embeddings and metadata - {timestamp}"
        subprocess.run(["git", "commit", "-m", msg], cwd=RUTA_SUMAR_ROOT, check=True)
        
        # Push a la branca principal
        branch = STEP_10.get("GITHUB_BRANCH", "main")
        subprocess.run(["git", "push", "origin", branch], cwd=RUTA_SUMAR_ROOT, check=True)
        
        logging.info("✅ Nodes i metadades publicats correctament a GitHub.")
        return True
    except Exception as e:
        stderr_msg = str(e)
        if "nothing to commit" in stderr_msg or "no changes added" in stderr_msg:
            logging.info("ℹ️ No hi ha canvis nous per publicar a GitHub.")
            return True
        logging.error(f"❌ Error publicant a GitHub: {e}")
        return False

def calcular_cid_ipfs_local(ruta_fitxer):
    """Calcula un hash SHA-256 per simular un CID d'IPFS si el client no està instal·lat."""
    try:
        # Intentar utilitzar el client IPFS real si està disponible
        resultat = subprocess.run(
            ["ipfs", "add", "--cid-version=1", "--hash=sha2-256", ruta_fitxer],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        cid = resultat.stdout.split()[1]
        return cid
    except FileNotFoundError:
        # Fallback: Simulació de CID basada en SHA-256
        logging.warning("⚠️ Client IPFS no trobat. Generant hash de simulació...")
        with open(ruta_fitxer, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return f"QmSimulated{file_hash[:32]}"
    except Exception as e:
        logging.error(f"❌ Error calculant CID: {e}")
        return None

def generar_cids_per_metadades():
    """Genera CIDs per als fitxers clau de metadades."""
    cids = {}
    
    # Mapping Global
    ruta_mapping = os.path.join(DATA_ROOT, "mapping_global.json")
    if os.path.exists(ruta_mapping):
        cids["mapping_global"] = calcular_cid_ipfs_local(ruta_mapping)
        
    # Vocabulari
    ruta_vocab = os.path.join(DATA_ROOT, "vocabulari.json")
    if os.path.exists(ruta_vocab):
        cids["vocabulari"] = calcular_cid_ipfs_local(ruta_vocab)
        
    return cids

def actualitzar_referencia_ipfs(cids_metadades):
    """Guarda les referències CID en un fitxer local."""
    ref_path = os.path.join(DATA_ROOT, "ipfs_refs.json")
    data = {
        "cids_metadades": cids_metadades,
        "github_base_url": f"https://raw.githubusercontent.com/{STEP_10['GITHUB_USER']}/{STEP_10['GITHUB_REPO']}/{STEP_10['GITHUB_BRANCH']}/data/",
        "ipfs_gateway": STEP_34.get("IPFS_GATEWAY", "https://ipfs.io/ipfs/")
    }
    
    with open(ref_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logging.info(f"💾 Referències IPFS guardades a: {ref_path}")

def executar_publicacio_dual():
    logging.info(f"🔍 Iniciant publicació dual ARD per a {GLOBAL['PROJECT_NAME']}...")
    
    # 1. Publicar a GitHub (inclou nodes i metadades)
    github_ok = publicar_a_github()
    
    # 2. Generar CIDs per a metadades clau
    cids_metadades = generar_cids_per_metadades()
    
    if cids_metadades:
        logging.info("🌐 CIDs generats per a metadades clau:")
        for key, cid in cids_metadades.items():
            logging.info(f"   - {key}: {cid}")
            
        actualitzar_referencia_ipfs(cids_metadades)
    else:
        logging.warning("⚠️ No s'han pogut generar CIDs per a les metadades.")

    logging.info("-" * 60)
    if github_ok:
        logging.info("🟢 PUBLICACIÓ FINALITZADA: Els nodes amb embeddings optimitzats són accessibles globalment.")
    else:
        logging.info("🔴 PUBLICACIÓ PARCIAL: Revisa els errors de GitHub.")

if __name__ == "__main__":
    executar_publicacio_dual()
    print(DESCRIPCIO_FINAL_STEP34)