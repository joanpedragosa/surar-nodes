# =====================================================================
# NOM DEL CODI: config.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\config.py
# DESCRIPCIÓ FUNCIONAL: Definició centralitzada de paràmetres, constants,
#                      rutes absolutes d'alta seguretat i configuració 
#                      del model de Representació Distribuïda (ARD) 
#                      per a SURAR-AINA. Inclou configuració per a Deep Learning (Keras).
# =====================================================================

import os

# TOPOLOGIA ARQUITECTÒNICA CENTRALITZADA INDUSTRIAL (MODEL ARD)
SURAR_ROOT = r"D:\Notebook\Transformer\surar_probabilistic"
DATA_ROOT = os.path.join(SURAR_ROOT, "data")

GLOBAL = {
    "PROJECT_NAME": "SURAR-AINA-ARD",
    "VERSION": "5.0.0-ARD", # Versió actualitzada per reflectir l'arquitectura de Deep Learning Puro
    "DEBUG_MODE": False,
    "LANGUAGE": "ca"
}

# FASE A: INGESTIÓ DE DADES BRUTES I INICIALITZACIÓ (STEP 05)
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
    
    # PARÀMETRES LINGÜÍSTICS BASE
    "FINESTRA_CONTEXT_HEBBIAN": 15,                # Mida de la finestra desllisant (tokens) - útil per a estadístiques auxiliars
}

# FASE B: INDEXACIÓ I BLINDATGE (STEP 10)
STEP_10 = {
    "GITHUB_USER": "joanpedragosa",
    "GITHUB_REPO": "surar-nodes",
    "GITHUB_BRANCH": "main",
    "BASE_REMOTE_URL": "https://raw.githubusercontent.com/joanpedragosa/surar-nodes/main/data/nodes",
    "MAPPING_FILE": os.path.join(DATA_ROOT, "mapping_global.json"),
    "VOCABULARY_FILE": os.path.join(DATA_ROOT, "vocabulari.json"), # Fitxer clau per a Keras
    "USE_IPFS": False,
    "IPFS_GATEWAY": "https://ipfs.io/ipfs/"
}

# FASE C: CONFIGURACIÓ GIT IMPERATIVA (STEP 28)
STEP_28 = {
    "GITHUB_USER": "joanpedragosa",
    "GITHUB_EMAIL": "joan.pedragosa@gmail.com",
    "GITHUB_REPO": "surar-nodes",
    "VERIFY_ACCOUNT_ONLINE": True
}

# FASE D: SINCRONITZACIÓ I PUBLICACIÓ (STEP 30)
STEP_30 = {
    "AUTO_COMMIT_LOCAL_REPLACE": True,
    "GITHUB_BRANCH": "main",
    "BATCH_SIZE_COMMITS": 500,
    "ENABLE_INCREMENTAL_PUSH": False
}

# FASE E: ENTRENAMENT PROFUND I OPTIMITZACIÓ D'EMBEDDINGS (STEP 33 - KERAS)
STEP_33 = {
    # Paràmetres del Model Keras
    "MODEL_TYPE": "Siamese_LSTM",          # Arquitectura de xarxa neuronal
    "MAX_SEQ_LENGTH": 20,                  # Longitud màxima de seqüència per a padding
    "VOCAB_SIZE": 25000,                    # Mida del vocabulari per a la capa Embedding (augmentat per cobrir millor el corpus)
    "EMBEDDING_DIM": 64,                   # Dimensions dels vectors d'embedding (CLAU PER STEP 05 i 35)
    "LEARNING_RATE": 0.01,                 # Eta (η): Velocitat d'aprenentatge (ajustada per sortir de mínims locals)
    "EPOCHS": 100,                         # Nombre d'iteracions d'entrenament (reduït amb Early Stopping)
    "BATCH_SIZE_TRAIN": 16,                # Mida del lot per a entrenament Keras
    
    # Funció de Pèrdua i Optimització
    "LOSS_FUNCTION": "binary_crossentropy", # Funció de pèrdua per a classificació de parelles
    "OPTIMIZER": "adam",                   # Optimitzador adaptatiu
    
    # Fitxers de Sortida
    "MODEL_OUTPUT_FILE": os.path.join(DATA_ROOT, "surar_semantic_model.keras"),
    # Nota: Ja no generem optimized_weights.json per a inferència lineal, 
    # sinó que actualitzem els embedding_vector dins dels nodes JSON.
    
    # Conjunt de Validació
    "VALIDATION_SET_SIZE": 50,             
    "MARGIN_SCORE": 1.2                    
}

# FASE E-BIS: PUBLICACIÓ DUAL IPFS/GITHUB (STEP 34)
STEP_34 = {
    "IPFS_GATEWAY": "https://ipfs.io/ipfs/",
    "PINNING_SERVICE": "local"
}

# FASE F: INFERÈNCIA GEOMÈTRICA LLEUGERA (STEP 35)
STEP_35 = {
    "INITIAL_ENERGY": 10.0,
    "ENERGY_DECAY_FACTOR": 0.85,
    "MAX_HOPS": 3,
    "LATENCY_PENALTY_WEIGHT": 0.1,
    "MIN_ENERGY_THRESHOLD": 0.01,
    "MIN_CONFIDENCE_SCORE": 0.5,
    "CACHE_ENABLED": True,
    "CACHE_MAX_SIZE": 1000,
    
    # Configuració ARD (Sense fusió híbrida complexa)
    "INFERENCE_METHOD": "cosine_similarity", # Mètode principal de scoring
    "USE_EMBEDDINGS": True                   # Activar l'ús d'embeddings optimitzats distribuïts
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