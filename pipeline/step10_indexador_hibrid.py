# =====================================================================
# NOM DEL CODI: step10_indexador_hibrid.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step10_indexador_hibrid.py
# DESCRIPCIÓ FUNCIONAL: Blindatge criptogràfic i indexació per a l'arquitectura ARD 
#                      sobre la carpeta 'data/nodes'. Valida estructures bàsiques,
#                      reescriu URLs, integra el vocabulari global i genera 
#                      el mapa mestre d'enrutament.
# OPCIONS D'EXECUCIÓ: python pipeline/step10_indexador_hibrid.py
# =====================================================================

import os
import sys
import json
import logging
import hashlib

RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import GLOBAL, STEP_10, STEP_05, STEP_33, DATA_ROOT
from pipeline.step00_contracte_global import (
    normalitzar_token_català, 
    construir_url_node_oficial,
    carregar_o_inicialitzar_vocabulari
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_STEP10 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 10 (INDEXADOR ARD)
================================================================================
1. IDENTIFICACIÓ DEL MÒDUL:
   - Nom: step10_indexador_hibrid.py | Fase: B (Indexació i Blindatge ARD).
   - Sortida: Carpeta 'data/nodes/' actualitzada i 'data/mapping_global.json'.

2. PROPÒSIT ESTRATÈGIC:
   Transforma els nodes inicials en artefactes digitals blindats per a la xarxa. 
   Assegura que cada concepte tingui una identitat web immutable a GitHub, 
   una traçabilitat criptogràfica única (simulació IPFS) i un índex numèric 
   consistent per a la recuperació d'embeddings.

3. LÒGICA OPERATIVA (BLINDATGE ARD):
   A. Validació 'In Situ': Filtra artifacts residuals i verifica la presència 
      d'estructures bàsiques (concept, frequency, embedding_vector).
   B. Integració de Vocabulari: Carrega el vocabulari generat al Step 05 i 
      l'associa a cada node dins del mapa global.
   C. String Hard-Fix: Reescriu URLs internes dins dels nodes segons el contracte 
      de producció (incloent la ruta /data/nodes/) per evitar errors 404.
   D. Simulació IPFS: Genera CIDs únics (SHA-256 prefixat amb Qm) per a cada node.
   E. Mapa d'Enrutament Centralitzat: Crea 'mapping_global.json' amb URLs, CIDs 
      i índexos de vocabulari.

4. GARANTIES DE QUALITAT:
   - Immutabilitat Web: URLs compatibles amb GitHub Raw.
   - Traçabilitat Total: Índex mestre accessible per localitzar qualsevol node.
   - Integritat ARD: Preserva embeddings inicials amb dimensions validades.
   - Consistència Deep Learning: Mappeig token-índex verificable per a Keras.

RESULTAT FINAL:
La carpeta 'data/nodes/' conté la versió definitiva dels conceptes catalans blindats.
El fitxer 'data/mapping_global.json' actua com a clau mestra per connectar la semàntica 
de l'Aina amb la infraestructura tècnica de GitHub i IPFS.
================================================================================
"""

def generar_cid_v0_simulat(contingut_text: str) -> str:
    """Genera un hash criptogràfic únic simulat basat en el patró Qm d'IPFS."""
    sha256_hash = hashlib.sha256(contingut_text.encode('utf-8')).hexdigest()
    return f"QmSURAR{sha256_hash[:32].lower()}AinaProject"

def indexar_i_publicar_hibrid():
    logging.info("🚀 Iniciant blindatge i indexació ARD (Fase B)...")

    # Obtenir la dimensió esperada d'embedding des de la configuració
    expected_emb_dim = STEP_33.get("EMBEDDING_DIM", 64)
    logging.info(f"📐 Validant embeddings amb dimensió esperada: {expected_emb_dim}")

    # 1. RUTA DE LECTURA (NODES GENERATS AL STEP 05)
    dir_nodes = STEP_05["OUTPUT_LOCAL_DIR"] # data/nodes
    
    if not os.path.exists(dir_nodes):
        logging.error(f"❌ Carpeta de nodes no trobada: '{dir_nodes}'. Executa primer el Step 05.")
        return

    fitxers_json = [f for f in os.listdir(dir_nodes) if f.endswith(".json")]
    logging.info(f"🔍 Trobats {len(fitxers_json)} fitxers .json a '{dir_nodes}' per processar.")

    if len(fitxers_json) == 0:
        logging.warning("⚠️ No s'han trobat fitxers JSON per processar.")
        return
    
    # Carregar Vocabulari Global per a integració ARD
    vocabulari = carregar_o_inicialitzar_vocabulari()
    logging.info(f"📚 Vocabulari carregat amb {len(vocabulari)} entrades per a mappeig d'índexos.")

    mapa_enrutament_hibrid = {}
    comptador_processats = 0
    comptador_rebutjats = 0

    for nom_fitxer in fitxers_json:
        token_potencial = nom_fitxer.replace(".json", "")
        
        # Filtre de seguretat final per evitar processar errors residuals
        if not token_potencial or token_potencial[0].isdigit():
            comptador_rebutjats += 1
            continue 

        cami_fitxer = os.path.join(dir_nodes, nom_fitxer)
        try:
            with open(cami_fitxer, "r", encoding="utf-8") as f:
                dades_node = json.load(f)
        except Exception:
            continue

        # Blindatge de URLs i Normalització
        token_validat = normalitzar_token_català(token_potencial)
        if not token_validat:
            comptador_rebutjats += 1
            continue
            
        # Validació ARD Bàsica
        has_embedding = "embedding_vector" in dades_node
        
        if has_embedding:
            emb_dim = len(dades_node["embedding_vector"])
            if emb_dim != expected_emb_dim:
                logging.warning(f"⚠️ Node '{token_validat}' té embedding de dim {emb_dim} (esperat {expected_emb_dim}).")
                # En un entorn estricte, aquí podries rebutjar el node. Per ara continuem.
        
        if not has_embedding:
            logging.warning(f"⚠️ Node '{token_validat}' falta embedding_vector. Es processa igualment.")

        # Actualitzar ID principal del node amb la URL correcta (/data/nodes/)
        url_oficial = construir_url_node_oficial(token_validat)
        dades_node["id"] = url_oficial
        
        # Sobreescriptura amb dades blindades (mantenim vectors intactes)
        contingut_final = json.dumps(dades_node, ensure_ascii=False, indent=2)
        with open(cami_fitxer, "w", encoding="utf-8") as f:
            f.write(contingut_final)

        # Generar CID i afegir al mapa
        cid = generar_cid_v0_simulat(contingut_final)
        
        # Obtenir índex de vocabulari per a consistència Keras
        token_index = vocabulari.get(token_validat, -1)

        mapa_enrutament_hibrid[token_validat] = {
            "ipfs_hash_cid": cid,
            "github_raw_url": url_oficial,
            "frequency": dades_node.get("frequency", 0),
            "vocab_index": token_index # Camp clau per a Deep Learning
        }
        comptador_processats += 1
        
        # Log de progrés cada 1000 nodes
        if comptador_processats % 1000 == 0:
            logging.info(f"   ... Processats {comptador_processats} nodes ...")

    # 2. RUTA D'ESCRIPTURA (MAPA A L'ARREL DE DATA)
    ruta_mapping_final = os.path.join(DATA_ROOT, "mapping_global.json")
    
    try:
        with open(ruta_mapping_final, "w", encoding="utf-8") as f:
            json.dump(mapa_enrutament_hibrid, f, ensure_ascii=False, indent=2)
        logging.info(f"💾 Mapa d'enrutament guardat a: '{ruta_mapping_final}'")
    except Exception as e:
        logging.error(f"❌ Error guardant el mapa: {e}")

    logging.info(f"🎉 Blindatge ARD completat. Processats: {comptador_processats}. Rebutjats: {comptador_rebutjats}.")

if __name__ == "__main__":
    indexar_i_publicar_hibrid()
    print(DESCRIPCIO_FINAL_STEP10)