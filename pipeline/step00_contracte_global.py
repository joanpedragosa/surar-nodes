# =====================================================================
# NOM DEL CODI: step00_contracte_global.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step00_contracte_global.py
# DESCRIPCIÓ FUNCIONAL: Nucli de normalització lingüística i contracte 
#                      global per a SURAR-AINA. Defineix les regles 
#                      immutables per al tractament del text català 
#                      abans de la seva ingestió al pipeline probabilístic.
# OPCIONS D'EXECUCIÓ: Importat per tots els steps del pipeline.
# =====================================================================

import re
import unicodedata
import logging
from config import STEP_05, STEP_10, STOP_WORDS_CA

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

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

def construir_url_node_oficial(token_net: str) -> str:
    """Construeix de manera indestructible la URL unificada de producció massiva."""
    if not token_net:
        return ""
        
    user = STEP_10.get("GITHUB_USER", "joanpedragosa")
    repo = STEP_10.get("GITHUB_REPO", "surar-nodes")
    
    # PROTECCIÓ MÀXIMA: Reconstrucció immaculada des de zero per bypassar qualsevol truncament
    url_bona = f"https://raw.githubusercontent.com/{user}/{repo}/main/nodes/{token_net}.json"
    
    # Netejar per si s'hagués generat alguna doble barra inclinada accidental
    url_bona = url_bona.replace("https://://", "https://")
    return url_bona

def executar_proves_del_contracte():
    logging.info("Iniciant control de qualitat del Contracte Global (Step 00)...")
    
    # Prova 1: Sanejament lingüístic de caràcters del corpus
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
        
    # Prova 3: Construcció de camins de xarxa reals sense acoblaments de barres
    url_resultat = construir_url_node_oficial("intelligencia")
    logging.info(f"🧪 Test 3 (Xarxa): URL generada de fons: '{url_resultat}'")
    
    if "https://://" in url_resultat or "raw.githubusercontent.com" not in url_resultat or "joanpedragosa" not in url_resultat:
        logging.error("Contracte fallit: S'ha detectat un truncament o duplicitat de barres inclinades.")
        return False
        
    logging.info("🎉 Èxit absolut: El contracte és operacional i els protocols de xarxa estan blindats.")
    return True

if __name__ == "__main__":
    executar_proves_del_contracte()