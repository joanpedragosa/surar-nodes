# =====================================================================
# NOM DEL CODI: download_aina_dataset.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\utilitats\download_aina_dataset.py
# DESCRIPCIÓ FUNCIONAL: Descarrega el dataset CatalanQA del Projecte Aina 
#                      des de Hugging Face, el processa per extreure parelles 
#                      Pregunta-Resposta i les guarda en un fitxer de text 
#                      pla amb el format requerit pel pipeline SURAR-AINA.
# OPCIONS D'EXECUCIÓ: python utilitats/download_aina_dataset.py
# DEPENDÈNCIES: datasets, pandas
# =====================================================================

import os
import sys
import logging

# Assegurar que podem importar config des de l'arrel
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import DATA_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

def descarregar_i_formatar_aina():
    """
    Descarrega el dataset 'projecte-aina/catalanqa' de Hugging Face,
    extreu les columnes de pregunta i resposta, i les guarda en un fitxer .txt
    amb el format: "Pregunta? Resposta"
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logging.error("❌ La llibreria 'datasets' no està instal·lada. Executa: pip install datasets")
        return

    # Ruta de sortida definida al config (o fallback a la carpeta data general)
    output_dir = os.path.join(DATA_ROOT, "corpus")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "aina_corpus.txt")

    logging.info(f"📥 Iniciant descàrrega del dataset 'projecte-aina/catalanqa'...")
    
    try:
        # Carregar el dataset (només la part de train per simplificar)
        dataset = load_dataset("projecte-aina/catalanqa", split="train")
        
        logging.info(f"✅ Dataset carregat. Total d'exemples: {len(dataset)}")
        logging.info("🔄 Processant i formatant dades...")
        
        with open(output_file, "w", encoding="utf-8") as f:
            count = 0
            for item in dataset:
                # Adapta aquestes claus segons l'estructura real del dataset CatalanQA
                # Normalment són 'question' i 'answer' o 'context'
                pregunta = item.get("question", "")
                resposta = item.get("answer", "")
                
                # Neteja bàsica per evitar salts de línia dins de la mateixa frase
                if pregunta and resposta:
                    pregunta_neta = str(pregunta).replace("\n", " ").strip()
                    resposta_neta = str(resposta).replace("\n", " ").strip()
                    
                    # Format requerit: Pregunta? Resposta
                    # Afegim un signe d'interrogació si no el té ja
                    if not pregunta_neta.endswith("?"):
                        pregunta_neta += "?"
                        
                    linea = f"{pregunta_neta} {resposta_neta}\n"
                    f.write(linea)
                    count += 1
                    
        logging.info(f"💾 Fitxer guardat a: {output_file}")
        logging.info(f"📝 Total de línies QA generades: {count}")
        
    except Exception as e:
        logging.error(f"❌ Error durant la descàrrega o processament: {e}")

if __name__ == "__main__":
    descarregar_i_formatar_aina()