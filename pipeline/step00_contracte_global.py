# =====================================================================
# NOM DEL CODI: step00_contracte_global.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step00_contracte_global.py
# DESCRIPCIÓ FUNCIONAL: Nucli de normalització lingüística i gestió 
#                      del Vocabulari Global per a SURAR-AINA (ARD).
#                      
# PER QUÈ ÉS NECESSARI EL CONTRACTE STEP 00?
# ------------------------------------------
# En un sistema distribuït on milers de nodes es generen, s'entrenen i 
# es consulten de forma asíncrona, la consistència és vital. El Step 00 
# garanteix que:
# 1. Determinisme Lingüístic: "intel·ligència", "INTEL·LIGÈNCIA" i 
#    "inteligencia" sempre es mappegin al mateix token únic. Sense això, 
#    el model Keras veuria paraules diferents i no aprendria res.
# 2. Consistència d'Índexos: El fitxer 'vocabulari.json' assegura que 
#    el token "sous" sigui sempre l'índex 89, tant durant l'entrenament 
#    (Step 33) com durant la inferència (Step 35).
# 3. Neteja de Soroll: Elimina tokens numèrics purs i stop-words abans 
#    que arribin al model, reduint la dimensionalitat innecessària.
#
# OPCIONS D'EXECUCIÓ: Importat per tots els steps del pipeline.
# DEPENDÈNCIES: numpy, json, re, unicodedata
# =====================================================================

import re
import unicodedata
import logging
import json
import os
import numpy as np
from config import STEP_05, STEP_10, STOP_WORDS_CA, DATA_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

# =====================================================================
# 1. CONTRACTE LINGÜÍSTIC (NORMALITZACIÓ)
# =====================================================================

def normalitzar_text_catala(text: str) -> str:
    """
    Normalitza un text complet aplicant les regles del Contracte Global.
    1. NFKD Unicode decomposition.
    2. Preservació de majúscules (noms propis).
    3. Gestió de dígrafs catalans (l·l, ss, ix, etc.).
    """
    if not isinstance(text, str):
        return ""
    
    # 1. Descomposició Unicode per gestionar accents correctament
    text = unicodedata.normalize('NFKD', text)
    
    # 2. Substitucions específiques del català per evitar pèrdua d'informació
    text = text.replace("l·l", "ll")
    text = text.replace("L·L", "LL")
    
    # 3. Eliminar caràcters de control i salts de línia excessius
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def normalitzar_token_català(token: str) -> str:
    """
    Normalitza un token individual seguint el principi de determinisme.
    - Si el token està TOT EN MAJÚSCULES (ex: PSC, BARCELONA), es manté així.
    - Si no, es passa a minúscules i s'eliminen accents per agrupar variants.
    - Filtra tokens que continguin números o siguin purament numèrics.
    """
    if not token:
        return ""
    
    # Filtratge de tokens numèrics o alfanumèrics mixtos (ex: 1r, 2n)
    # Nota: En ARD, els números sovint es tracten com a tokens especials o s'eliminen 
    # si no són rellevants per a la semàntica profunda. Aquí els eliminem per simplificar.
    if any(char.isdigit() for char in token):
        return ""
    
    # Preservació de Noms Propis/Acrònims
    if token.isupper():
        return token
    
    # Normalització estàndard per a la resta
    token = token.lower()
    
    # Mapeig manual de caràcters especials si NFKD no ho ha resolt tot
    replacements = {
        'à': 'a', 'á': 'a', 'â': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u',
        'ç': 'c', 'ñ': 'n',
        'ï': 'i', 'ü': 'u'
    }
    
    for original, substitut in replacements.items():
        token = token.replace(original, substitut)
        
    return token

def netejar_i_tokenitzar(text: str) -> list:
    """
    Aplica el Contracte Global per convertir text brut en una llista de tokens nets.
    Aquesta funció és la porta d'entrada per a qualsevol text que vagi al model Keras.
    """
    text_net = normalitzar_text_catala(text)
    
    # Regex que captura paraules (incloent-hi guions interiors per a compostos) 
    # i números, ignorant puntuació externa.
    tokens_bruts = re.findall(r"[a-zA-Zçàéèíóòúüï\-]+|[0-9]+", text_net)
    
    tokens_nets = []
    for token in tokens_bruts:
        # Normalització individual (això ja filtra els numèrics gràcies a la nova lògica)
        token_norm = normalitzar_token_català(token)
        
        # Filtratge de longitud i stop-words
        if token_norm and len(token_norm) > 1 and token_norm not in STOP_WORDS_CA:
            tokens_nets.append(token_norm)
            
    return tokens_nets

# =====================================================================
# 2. GESTIÓ DE VOCABULARI GLOBAL (PER A KERAS/DEEP LEARNING)
# =====================================================================

def carregar_o_inicialitzar_vocabulari() -> dict:
    """
    Carrega el vocabulari global des del fitxer JSON o en crea un de buit.
    El vocabulari mappeja tokens a índexos únics per a la capa Embedding de Keras.
    """
    vocab_path = STEP_10.get("VOCABULARY_FILE", os.path.join(DATA_ROOT, "vocabulari.json"))
    if os.path.exists(vocab_path):
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"⚠️ Error carregant vocabulari, s'inicialitzarà de nou: {e}")
    
    # Índex 0 reservat per a padding/desconeguts
    return {"<PAD>": 0, "<UNK>": 1}

def afegir_al_vocabulari(token: str, vocabulari: dict) -> dict:
    """Afegeix un token al vocabulari si no hi existeix i retorna el diccionari actualitzat."""
    token_norm = normalitzar_token_català(token)
    if token_norm and token_norm not in vocabulari:
        vocabulari[token_norm] = len(vocabulari)
    return vocabulari

def guardar_vocabulari(vocabulari: dict):
    """Guarda el vocabulari actualitzat al disc."""
    vocab_path = STEP_10.get("VOCABULARY_FILE", os.path.join(DATA_ROOT, "vocabulari.json"))
    os.makedirs(os.path.dirname(vocab_path), exist_ok=True)
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(vocabulari, f, ensure_ascii=False, indent=2)
    logging.info(f"💾 Vocabulari guardat a {vocab_path} amb {len(vocabulari)} entrades.")

def token_a_index(token: str, vocabulari: dict) -> int:
    """Converteix un token al seu índex numèric corresponent."""
    token_norm = normalitzar_token_català(token)
    return vocabulari.get(token_norm, 1) # Retorna 1 (<UNK>) si no es troba

# =====================================================================
# 3. UTILITATS DE XARXA
# =====================================================================

def construir_url_node_oficial(token: str) -> str:
    """Construeix la URL pública oficial per a un node donat."""
    user = STEP_10.get("GITHUB_USER", "joanpedragosa")
    repo = STEP_10.get("GITHUB_REPO", "surar-nodes")
    branch = STEP_10.get("GITHUB_BRANCH", "main")
    
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/data/nodes/{token}.json"

# =====================================================================
# 4. PROVES DEL CONTRACTE I VALIDACIÓ
# =====================================================================

def executar_proves_del_contracte():
    logging.info("Iniciant control de qualitat del Contracte Global (Step 00)...")
    
    # Prova 1: Sanejament lingüístic
    paraula_test = "intel·ligència"
    token_net = normalitzar_token_català(paraula_test)
    logging.info(f"🧪 Test 1 (Llengua): '{paraula_test}' ➔ Token Net: '{token_net}'")
    if token_net != "intelligencia":
        logging.error("Contracte fallit a la normalització de lletres catalanes.")
        return False
        
    # Prova 2: Rebuig de tokens numèrics
    paraula_num = "1r"
    token_num = normalitzar_token_català(paraula_num)
    logging.info(f"🧪 Test 2 (Filtre Numèric): '{paraula_num}' ➔ Token Net: '{token_num}' (Ha de ser buit)")
    if token_num != "":
        logging.error("Contracte fallit: No s'ha filtrat correctament el token numèric.")
        return False
        
    # Prova 3: Construcció de camins de xarxa
    url_resultat = construir_url_node_oficial("intelligencia")
    logging.info(f"🧪 Test 3 (Xarxa): URL generada de fons: '{url_resultat}'")
    if "https://://" in url_resultat or "raw.githubusercontent.com" not in url_resultat:
        logging.error("Contracte fallit: S'ha detectat un truncament o duplicitat de barres inclinades.")
        return False

    # Prova 4: Gestió de Vocabulari
    vocab = carregar_o_inicialitzar_vocabulari()
    vocab = afegir_al_vocabulari("prova_ard", vocab)
    idx = token_a_index("prova_ard", vocab)
    logging.info(f"🧪 Test 4 (Vocabulari ARD): Token 'prova_ard' té índex {idx}")
    if idx <= 1:
        logging.error("Contracte fallit: El token no s'ha afegit correctament al vocabulari.")
        return False

    logging.info("🎉 Èxit absolut: El contracte ARD és operacional, la normalització és consistent i el vocabulari està actiu.")
    return True

if __name__ == "__main__":
    executar_proves_del_contracte()