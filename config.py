# =====================================================================
# NOM DEL CODI: config.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\config.py
# DESCRIPCIÓ FUNCIONAL: Definició centralitzada de paràmetres, constants,
#                      i rutes absolutes d'alta seguretat unificades a
#                      la unitat D: per a l'escala industrial de SURAR-AINA.
# =====================================================================

import os

# TOPOLOGIA ARQUITECTÒNICA CENTRALITZADA INDUSTRIAL (MODEL HMBL)
SURAR_ROOT = r"D:\Notebook\Transformer\surar_probabilistic"
DATA_ROOT = os.path.join(SURAR_ROOT, "data")

GLOBAL = {
    "PROJECT_NAME": "SURAR-AINA-PROB",
    "VERSION": "2.0.0-HMBL",
    "DEBUG_MODE": False,
    "LANGUAGE": "ca"
}

# FASE A: INGESTIÓ I EXTRACCIÓ PROBABILÍSTICA (STEP 05)
STEP_05 = {

    "DATASET_ID": "projecte-aina/catalanqa",       # Identificador del corpus base
    "SPLIT": "train",
    "CORPUS_FILE_TXT": os.path.join(DATA_ROOT, "aina_corpus.txt"), 
    "FETS_EXTRA_FILE": os.path.join(DATA_ROOT, "fets_extra.txt"),
    "OUTPUT_LOCAL_DIR": os.path.join(DATA_ROOT, "nodes"),
    
    # PARÀMETRES DE PROCESSAMENT MASSIU
    "MAX_NODES_PRODUCCIO": 50000,                  # Límit màxim de nodes a generar
    "MIN_FREQ_THRESHOLD": 1,                       # Freqüència mínima perquè un token esdevingui node
    "BATCH_SIZE": 500,                             # Mida del lot per a processament en memòria
    "MAX_SAMPLES_INGESTIO": 20000,                 # Màxim de mostres/linies a processar (per proves ràpides)
    
    # PARÀMETRES DEL MODEL HMBL (PROBABILÍSTIC)
    "FINESTRA_CONTEXT_HEBBIAN": 15,                # Mida de la finestra desllisant (tokens)
    "WINDOW_DIRECTIONAL": True,                    # Activar càlcul direccional per a Markov (A->B)
    "CALCULATE_MARKOV": True,                      # Generar taules de transició sintàctica
    "CALCULATE_BAYES": True,                       # Generar context bayesià semàntic
    "IDF_SMOOTHING_FACTOR": 1.0,                   # Factor k per a suavitzat IDF (log(freq + k))
    
    # LLINDARS DE QUALITAT ESTADÍSTICA
    "MIN_MARKOV_PROB": 0.05,                       # Probabilitat mínima per guardar una transició
    "MIN_BAYESIAN_LIKELIHOOD": 0.01,               # Likelihood mínima per guardar un context
    "MIN_POSTERIOR_BOOST": 1.2                     # Boost mínim per considerar una relació rellevant
}

# ... (resta del config.py) ...
# FASE B: INDEXACIÓ HÍBRIDA I BLINDATGE (STEP 10)
STEP_10 = {
    "GITHUB_USER": "joanpedragosa",
    "GITHUB_REPO": "surar-nodes",
    "GITHUB_BRANCH": "main",
    "BASE_REMOTE_URL": "https://raw.githubusercontent.com/joanpedragosa/surar-nodes/main/nodes",
    "MAPPING_FILE": os.path.join(DATA_ROOT, "mapping", "mapping_global.json"),
    "USE_IPFS": False,
    "IPFS_GATEWAY": "https://ipfs.io/ipfs/"
}

# FASE C: SINCRONITZACIÓ I PUBLICACIÓ (STEP 30)
STEP_30 = {
    "AUTO_COMMIT_LOCAL_REPLACE": True,
    "GITHUB_BRANCH": "main",
    "BATCH_SIZE_COMMITS": 500,  # <--- NOU PARÀMETRE: Commits cada 500 nodes
    "ENABLE_INCREMENTAL_PUSH": False # Si és True, fa push cada batch (més lent però més segur)
}


# FASE D: INFERÈNCIA CONCURRENT I XAT INTERACTIU (STEP 35)
STEP_35 = {
    "INITIAL_ENERGY": 10.0,
    "ENERGY_DECAY_FACTOR": 0.85,
    "MAX_HOPS": 3,
    "LATENCY_PENALTY_WEIGHT": 0.1,
    "MIN_ENERGY_THRESHOLD": 0.01,
    "MIN_CONFIDENCE_SCORE": 0.5,
    "MARKOV_WEIGHT": 0.4,
    "BAYESIAN_WEIGHT": 0.6,
    "CACHE_ENABLED": True,
    "CACHE_MAX_SIZE": 1000
}

# LLISTA GLOBAL DE STOP-WORDS (Necessària per Step 00 i Step 05)
STOP_WORDS_CA = {
    "a", "abans", "ací", "ah", "així", "això", "al", "aleshores", "algun", "alguna", 
    "algunes", "alguns", "allà", "allí", "allò", "als", "altra", "altre", "altres", 
    "amb", "ambdós", "anar", "anc", "ans", "apa", "aquell", "aquella", "aquelles", 
    "aquells", "aquest", "aquesta", "aquestes", "aquests", "aquí", "baix", "bé", 
    "cada", "cadascú", "cadascuna", "cadascunes", "cadascuns", "com", "consegueixo", 
    "conseguim", "conseguir", "consigueix", "consigueixen", "consigueixes", "contra", 
    "d'un", "d'una", "d'unes", "d'uns", "dalt", "de", "del", "dels", "des", "després", 
    "dins", "dintre", "donat", "doncs", "durant", "e", "eh", "el", "els", "em", "en", 
    "encara", "ens", "entre", "érem", "eren", "eres", "es", "és", "esta", "està", 
    "estàvem", "estaven", "estat", "estava", "estem", "esteu", "estic", "esto", "ets", 
    "fins", "fora", "gairebé", "ha", "han", "has", "havia", "he", "hem", "heu", "hi", 
    "ho", "i", "igual", "iguals", "inclòs", "ja", "jo", "l'hi", "la", "les", "li", 
    "li'n", "llarg", "llavors", "m'he", "ma", "mal", "malgrat", "mateix", "mateixa", 
    "mateixes", "mateixos", "me", "mentre", "meu", "meva", "meves", "mi", "molt", 
    "molta", "moltes", "molts", "mon", "mons", "n'he", "n'hi", "ne", "ni", "no", 
    "nogensmenys", "només", "nosaltres", "nostra", "nostre", "nostres", "o", "oh", 
    "oi", "on", "pas", "pel", "pels", "per", "perquè", "però", "poc", "poca", "pocs", 
    "poques", "potser", "propi", "qual", "quals", "quan", "quant", "que", "què", 
    "quelcom", "qui", "quin", "quina", "quines", "quins", "què", "s'ha", "s'han", 
    "sa", "semblant", "semblants", "ses", "seu", "seus", "seva", "seves", "si", 
    "sobre", "sobretot", "sóc", "solament", "sols", "som", "son", "sota", "sou", 
    "t'ha", "t'han", "t'he", "ta", "tal", "també", "tampoc", "tan", "tant", "tanta", 
    "tantes", "te", "tenim", "tenir", "tens", "tercer", "teu", "teva", "teves", "ti", 
    "ton", "tot", "tota", "totes", "tots", "un", "una", "unes", "uns", "ús", "us", 
    "va", "vaig", "vam", "van", "vas", "veu", "vosaltres", "vostra", "vostre", 
    "vostres", "x", "xq", "text", "resposta", "questio", "pregunta", "answer_start", "acord"
}