cd D:\Notebook\Transformer\surar_probabilistic

# 1. Força l'addició de tots els JSONs de la carpeta nodes, ignorant el .gitignore
git add -f data/nodes/*.json

# 2. Afegeix també el mapa global forçadament
git add -f data/mapping_global.json

# 3. Comprova l'estat (ara hauries de veure milers de fitxers en verd)
git status

# 4. Fes el commit
git commit -m "FORCED UPLOAD: Ignoring gitignore to push 24k HMBL nodes"

# 5. Pujada forçada
git push origin main --force