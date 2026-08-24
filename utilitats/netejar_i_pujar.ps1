# SCRIPT DE NETEJA I PRIMERA PUJADA NETA PER A SURAR-AINA PROBABILISTIC

Write-Host "Iniciant procés de neteja del repositori remot..." -ForegroundColor Cyan

# 1. Assegurar-nos que som a la carpeta correcta
Set-Location "D:\Notebook\Transformer\surar_probabilistic"

# 2. Esborrar el fitxer problemàtic 'con.json' si existeix
if (Test-Path "data\nodes\con.json") {
    Write-Host "Eliminant fitxer prohibit con.json..." -ForegroundColor Yellow
    Remove-Item "data\nodes\con.json" -Force
}

# 3. Descarregar l'estat actual de GitHub
Write-Host "Descarregant estat actual de GitHub..." -ForegroundColor Cyan
git fetch origin main

# 4. Forçar la fusió amb historials no relacionats
Write-Host "Fusionant històries locals i remotes..." -ForegroundColor Cyan
git pull origin main --allow-unrelated-histories --no-edit

# 5. Esborrar TOTS els fitxers antics de la carpeta data/nodes localment
Write-Host "Netegant carpeta local de nodes antics..." -ForegroundColor Yellow
Get-ChildItem "data\nodes" -Filter "*.json" | Remove-Item -Force
if (Test-Path "data\mapping_global.json") { Remove-Item "data\mapping_global.json" -Force }
if (Test-Path "data\mapping_ipfs.json") { Remove-Item "data\mapping_ipfs.json" -Force }

# 6. Afegir aquesta "neteja" a Git
git add -A
git commit -m "Clean up old Hebbian nodes to prepare for HMBL Probabilistic Graph"

# 7. Pujar la neteja a GitHub
Write-Host "Pujant la neteja a GitHub..." -ForegroundColor Green
git push origin main

Write-Host "REPOSITORI REMOT NETEJAT. Ara pots executar el Step 30." -ForegroundColor Green