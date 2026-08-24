# =====================================================================
# NOM DEL CODI: step05_ingestio_probabilistica.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step05_ingestio_probabilistica.py
# DESCRIPCIÓ FUNCIONAL: Motor d'ingestió industrial que descarrega el 
#                      dataset CatalanQA, el processa amb NER i genera 
#                      nodes JSON amb intel·ligència estadística local 
#                      (Model HMBL: Markov + Bayes).
# OPCIONS D'EXECUCIÓ: python pipeline/step05_ingestio_probabilistica.py
# DEPENDÈNCIES: datasets, pandas
# =====================================================================

import os
import sys
import json
import math
import logging
import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import STEP_05, DATA_ROOT, STOP_WORDS_CA
from pipeline.step00_contracte_global import normalitzar_token_català, construir_url_node_oficial

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_STEP05 = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 05 (INGESTIÓ PROBABILÍSTICA HMBL)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Descarregar el dataset 'projecte-aina/catalanqa' de Hugging Face, transformar-lo 
en un corpus de text pla formatat (Pregunta? Resposta) i generar una xarxa de 
nodes atomitzats (JSON) enriquits amb probabilitats locals (Model HMBL).

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Ingestió Telemàtica: Descarrega el dataset des de HF i extreu parelles QA.
2. Pre-processament NER: Detecta i uneix noms propis compostos (ex: Angel_Guimera).
3. Generació de Corpus Immutable: Guarda les dades netes a 'data/aina_corpus.txt' 
   en el format natural requerit pel sistema.
4. Càlcul de Probabilitats Markovianes: Analitza la seqüència de tokens per determinar 
   P(B|A), aportant coherència sintàctica al graf.
5. Inferència de Context Bayesià: Calcula la força d'associació temàtica dins d'una 
   finestra de context, generant factors de 'posterior_boost' per a la inferència.
6. Volcat Atomitzat: Genera fitxers JSON independents amb taules de transició i 
   context bayesià, preparats per ser publicats a la xarxa distribuïda.

RESULTAT EXECUTAT CONCRET:
Un fitxer de corpus massiu a l'arrel de 'data/' i una carpeta 'data/nodes/' plena 
de fitxers JSON intel·ligents, capaços de suportar inferències semàntiques complexes.
================================================================================
"""

def extreure_text_resposta(answers_raw):
    """Funció robusta per extreure el text net de qualsevol estructura de resposta del dataset."""
    if not answers_raw:
        return ""
        
    if isinstance(answers_raw, dict):
        text_field = answers_raw.get("text", [])
        if isinstance(text_field, list) and len(text_field) > 0:
            return str(text_field[0]).strip()
        elif isinstance(text_field, str):
            return text_field.strip()
            
    if isinstance(answers_raw, list):
        if len(answers_raw) > 0:
            primer_element = answers_raw[0]
            if isinstance(primer_element, dict):
                return str(primer_element.get("text", "")).strip()
            else:
                return str(primer_element).strip()
                
    if isinstance(answers_raw, str):
        return answers_raw.strip()
        
    return ""

def detectar_i_unir_noms_propis(text: str) -> str:
    """Detecta seqüències de paraules que comencen per majúscula i les uneix amb '_'."""
    patro = r'\b([A-ZÀÈÍÒÚÇ][a-zàèíòuç]*)\s+([A-ZÀÈÍÒÚÇ][a-zàèíòuç]*)\b'
    while re.search(patro, text):
        text = re.sub(patro, r'\1_\2', text)
    return text

def netejar_i_tokenitzar_text(text: str) -> list:
    """Aplica NER, normalització i filtratge de stop-words."""
    text_amb_entitats = detectar_i_unir_noms_propis(text)
    text_net = re.sub(r"[^\w\sçàéèíóòúü_]", " ", text_amb_entitats.lower(), flags=re.UNICODE)
    
    tokens_nets = []
    for p in text_net.split():
        if len(p) < 2 or p.isdigit(): continue
        if p not in STOP_WORDS_CA:
            token_segur = normalitzar_token_català(p)
            if token_segur and token_segur not in STOP_WORDS_CA:
                tokens_nets.append(token_segur)
    return tokens_nets

def calcular_estadistiques_hmbll(tokens_sequencia: List[str]) -> Tuple[Dict, Dict, Dict]:
    """Calcula freqüències, transicions Markovianes i co-ocurrències Bayesianes."""
    freq_absoluta = Counter()
    transicions_markov = defaultdict(lambda: defaultdict(int))
    coocorrencia_bayes = defaultdict(lambda: defaultdict(int))
    
    finestra = STEP_05["FINESTRA_CONTEXT_HEBBIAN"]
    
    for i, token_actual in enumerate(tokens_sequencia):
        freq_absoluta[token_actual] += 1
        
        if i + 1 < len(tokens_sequencia):
            seguent_token = tokens_sequencia[i+1]
            if seguent_token != token_actual:
                transicions_markov[token_actual][seguent_token] += 1
                
        inici_finestra = max(0, i - finestra)
        fi_finestra = min(len(tokens_sequencia), i + finestra + 1)
        
        for j in range(inici_finestra, fi_finestra):
            if i == j: continue
            token_vei = tokens_sequencia[j]
            if token_vei != token_actual:
                coocorrencia_bayes[token_actual][token_vei] += 1
                
    return freq_absoluta, transicions_markov, coocorrencia_bayes

def normalitzar_pesos_markov(transicions: Dict) -> Dict:
    """Converteix comptatges de transició en probabilitats P(B|A)."""
    probs_markov = {}
    for token_a, veins in transicions.items():
        total_transicions = sum(veins.values())
        if total_transicions == 0: continue
        
        probs_markov[token_a] = {}
        for token_b, count in veins.items():
            probs_markov[token_a][token_b] = round(count / total_transicions, 4)
            
    return probs_markov

def calcular_context_bayesia(coocorrencia: Dict, freq_total: Dict) -> Dict:
    """Calcula likelihoods i posterior boosts per al context bayesià."""
    context_bayes = {}
    total_tokens_corpus = sum(freq_total.values())
    
    for token_a, veins in coocorrencia.items():
        freq_a = freq_total.get(token_a, 1)
        context_bayes[token_a] = {}
        
        for token_b, count_cooc in veins.items():
            freq_b = freq_total.get(token_b, 1)
            
            likelihood = count_cooc / (freq_a * STEP_05["FINESTRA_CONTEXT_HEBBIAN"] * 2)
            
            esperat_atzar = (freq_a * freq_b) / total_tokens_corpus if total_tokens_corpus > 0 else 1
            if esperat_atzar > 0:
                ratio_forca = count_cooc / esperat_atzar
                boost = max(1.0, round(math.log10(ratio_forca + 1) + 1, 2))
            else:
                boost = 1.0
                
            if likelihood > 0.01 or boost > 1.2:
                context_bayes[token_a][token_b] = {
                    "likelihood": round(likelihood, 4),
                    "posterior_boost": boost
                }
                
    return context_bayes

def generar_nodes_hmbll():
    """Funció principal que executa tot el pipeline d'ingestió probabilística."""
    logging.info("🚀 Iniciant Ingestió Probabilística HMBL des de Hugging Face...")
    
    try:
        from datasets import load_dataset
        logging.info(f"🌐 Carregant dataset '{STEP_05['DATASET_ID']}'...")
        dataset = load_dataset(STEP_05["DATASET_ID"], split=STEP_05["SPLIT"])
    except ImportError:
        logging.error("❌ Error: La llibreria 'datasets' no està instal·lada. Executa: pip install datasets")
        return
    except Exception as e:
        logging.error(f"❌ Error carregant dataset: {e}")
        return

    # Preparar directoris (DATA_ROOT és D:\...\data)
    output_dir = STEP_05["OUTPUT_LOCAL_DIR"] # D:\...\data\nodes
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(DATA_ROOT, exist_ok=True) # Assegurar que data/ existeix

    co_ocurrencies_global = defaultdict(lambda: defaultdict(int))
    frequencies_global = Counter()
    transicions_global = defaultdict(lambda: defaultdict(int))
    
    linies_corpus = []
    mostres_a_processar = min(len(dataset), STEP_05["MAX_SAMPLES_INGESTIO"])
    
    logging.info(f"Processant {mostres_a_processar} mostres del dataset...")

    for idx in range(mostres_a_processar):
        try:
            mostra = dataset[idx]
            question = str(mostra.get("question", "")).strip()
            text_resposta = extreure_text_resposta(mostra.get("answers"))
            
            if question and text_resposta:
                linea_neta = f"{question} {text_resposta}"
                linies_corpus.append(linea_neta)
                
                tokens = netejar_i_tokenitzar_text(linea_neta)
                
                freq, trans, cooc = calcular_estadistiques_hmbll(tokens)
                frequencies_global.update(freq)
                
                for t, veins_t in trans.items():
                    for v, c in veins_t.items():
                        transicions_global[t][v] += c
                        
                for t, veins_c in cooc.items():
                    for v, c in veins_c.items():
                        co_ocurrencies_global[t][v] += c
                        
        except Exception as e:
            continue

    # Guardar Corpus Directament a DATA_ROOT
    if linies_corpus:
        with open(STEP_05["CORPUS_FILE_TXT"], "w", encoding="utf-8") as f:
            for linea in linies_corpus:
                f.write(linea + "\n")
        logging.info(f"✅ Corpus guardat a: {STEP_05['CORPUS_FILE_TXT']} ({len(linies_corpus)} línies)")

    logging.info("🧮 Calculant probabilitats globals HMBL...")
    probs_markov = normalitzar_pesos_markov(transicions_global)
    context_bayes = calcular_context_bayesia(co_ocurrencies_global, frequencies_global)

    logging.info("💾 Generant nodes JSON enriquits...")
    nodes_generats = 0
    max_nodes = STEP_05["MAX_NODES_PRODUCCIO"]
    nodes_seleccionats = frequencies_global.most_common(max_nodes)
    
    for token, freq_val in nodes_seleccionats:
        if freq_val < STEP_05["MIN_FREQ_THRESHOLD"]: continue
        
        node_data = {
            "concept": token,
            "frequency": freq_val,
            "edges": [],
            "markov_transitions": probs_markov.get(token, {}),
            "bayesian_context": context_bayes.get(token, {})
        }
        
        ruta_node = os.path.join(output_dir, f"{token}.json")
        with open(ruta_node, "w", encoding="utf-8") as f:
            json.dump(node_data, f, ensure_ascii=False, indent=2)
            
        nodes_generats += 1
        
    logging.info(f"🏁 Procés finalitzat. {nodes_generats} nodes generats a {output_dir}")

if __name__ == "__main__":
    generar_nodes_hmbll()
    print(DESCRIPCIO_FINAL_STEP05)