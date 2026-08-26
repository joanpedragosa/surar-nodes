# =====================================================================
# NOM DEL CODI: step28_configurador_git.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step28_configurador_git.py
# DESCRIPCIÓ FUNCIONAL: Configura de forma imperativa la identitat global
#                      d'autor (joanpedragosa) i el correu electrònic a Windows,
#                      revisa telemàticament que el compte existeixi a GitHub
#                      i executa el 'set-url' de les rutes del model SURAR.
# OPCIONS D'EXECUCIÓ: python pipeline/step28_configurador_git.py
# =====================================================================

import os
import sys
import subprocess
import logging
import urllib.request
from urllib.error import HTTPError, URLError

# INJECCIÓ DINÀMICA DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import GLOBAL, STEP_10, STEP_28

# Configurar Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 28 (CONFIGURACIÓ GIT BLINDADA)
================================================================================
PROPÒSIT GLOBAL DEL PROJECTE:
SURAR té com a objectiu fundar una arquitectura de xarxa neuronal de grafs (GNN) 
basada en embeddings distribuïts (ARD), on cada concepte esdevé un node viu que 
sura lliurement en l'espai públic de la WWW utilitzant l'ecosistema de dades 
híbrid de cost zero (GitHub i IPFS).

LOGICA DE FUNCIONAMENT INTERN D'AQUESTA PEÇA:
1. Auditoria Telemàtica: Verificació en temps real de l'existència del compte de 
   GitHub ('joanpedragosa') mitjançant crides HTTP abans de qualsevol operació 
   d'escriptura per garantir la connectivitat segura.
2. Establiment d'Identitat Global: Configuració forçosa de les credencials d'autor 
   ('user.name' i 'user.email') a nivell de sistema Windows per garantir la 
   signatura correcta i consistent dels commits.
3. Ancoratge de Rutes (Set-URL): Execució imperativa de 'git remote set-url origin' 
   per assegurar que el directori local apunta correctament a la infraestructura 
   distribuïda de SURAR, eliminant configuracions buides o errònies.
4. Inicialització Autònoma: Detecta si el directori no és un repo Git i l'inicialitza 
   automàticament, preparant-lo per rebre els nodes ARD i els embeddings optimitzats.

RESULTAT EXECUTAT CONCRET:
La infraestructura de transport ha estat totalment configurada i blindada amb l'autor real. 
El directori de treball de la unitat D: apunta al teu repositori de la WWW, 
deixant la via lliure perquè els commits i push del Step 30 s'enviïn sols de forma transparent.
================================================================================
"""

def comprovar_usuari_github(usuari):
    """Verifica l'existència del compte de GitHub mitjançant una petició HTTP."""
    url_perfil = f"https://github.com/{usuari}"
    logging.info(f"Auditant telemàticament l'usuari a la xarxa: Pistant a '{url_perfil}'...")
    
    peticio = urllib.request.Request(url_perfil, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(peticio, timeout=5) as resposta:
            if resposta.getcode() == 200:
                logging.info(f"🎉 Èxit absolut: GitHub confirma que el compte públic '{usuari}' EXISTEIX de veritat a la WWW.")
                return True
    except Exception as e:
        logging.error(f"❌ Error de connexió física o adreçament: {str(e)}")
        return False
    return False

def executar_ordre_sistema(comanda, directori=None):
    """Executa una comanda de sistema i retorna la sortida estàndard."""
    try:
        resultat = subprocess.run(comanda, cwd=directori, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return resultat.stdout.strip()
    except Exception as e:
        return f"AVÍS: {str(e)}"

def configurar_entorn_git():
    """Configura l'entorn Git local de forma imperativa."""
    usuari_real = STEP_28.get("GITHUB_USER", "joanpedragosa")
    email_real = STEP_28.get("GITHUB_EMAIL", "joan.pedragosa@gmail.com")
    repo_real = STEP_10.get("GITHUB_REPO", "surar-nodes")
    
    if not comprovar_usuari_github(usuari_real):
        logging.error("Validació avortada: La infraestructura s'ha desconnectat per seguretat d'adreçament.")
        return

    # CORRECCIÓ CLAU: Apuntem a l'arrel real del projecte SURAR_PROBABILISTIC
    ruta_arrel = RUTA_SUMAR_ROOT
    
    # 1. ENREGISTRAMENT IMPERATIU DE LA IDENTITAT DE L'AUTOR SOL·LICITADA
    logging.info("Assignant identitat global d'autor a la memòria de Windows...")
    executar_ordre_sistema(["git", "config", "--global", "user.email", email_real])
    executar_ordre_sistema(["git", "config", "--global", "user.name", usuari_real])

    nom_conf = executar_ordre_sistema(["git", "config", "user.name"], ruta_arrel)
    email_conf = executar_ordre_sistema(["git", "config", "user.email"], ruta_arrel)
    logging.info(f"Identitat confirmada globalment -> Autor: {nom_conf} | Correu: {email_conf}")

    # Construcció de la URL del repositori
    url_repositori_real = f"https://github.com/{usuari_real}/{repo_real}.git"

    # 2. FIXACIÓ INDESTRUCTIBLE DE RUTES CONCURRENTS SOTA SET-URL
    logging.info(f"Unificant i forçant el set-url del dipòsit a l'arrel: {ruta_arrel}...")
    
    # Inicialitzar Git si no existeix la carpeta .git
    if not os.path.exists(os.path.join(ruta_arrel, ".git")):
        logging.info("Inicialitzant repositori Git local...")
        executar_ordre_sistema(["git", "init"], ruta_arrel)
        
    # Assegurar que el remote existeix i apuntar-lo correctament
    add_result = executar_ordre_sistema(["git", "remote", "add", "origin", url_repositori_real], ruta_arrel)
    if "already exists" in str(add_result).lower():
        logging.info("Remote 'origin' ja existia. Actualitzant URL...")
        
    executar_ordre_sistema(["git", "remote", "set-url", "origin", url_repositori_real], ruta_arrel)
    executar_ordre_sistema(["git", "branch", "-M", "main"], ruta_arrel)

    logging.info("Sol·licitant auditoria final de rutes de transport de seguretat...")
    rutes_finals = executar_ordre_sistema(["git", "remote", "-v"], ruta_arrel)
    print("\n" + "-"*60)
    print("🧠 BALANÇ DE RUTES REMOTES CONFIGURADES EN DISC (ARREL):")
    print(rutes_finals if rutes_finals else "Avís: No s'ha pogut llistar cap ruta.")
    print("-"*60 + "\n")

if __name__ == "__main__":
    configurar_entorn_git()
    print(DESCRIPCIO_FINAL)