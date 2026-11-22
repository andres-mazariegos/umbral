# Arranca Umbral en Windows con un solo comando (desde PowerShell):
#     .\iniciar.ps1
# La primera vez instala todo (tarda unos minutos). Despues abre en segundos.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "== 1/3  Preparando el backend (Python) =="
if (-not (Test-Path "backend\.venv")) {
    python -m venv backend\.venv
}
& backend\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& backend\.venv\Scripts\python.exe -m pip install --quiet -r backend\requirements.txt

Write-Host "== 2/3  Preparando el sitio (Node) =="
Push-Location frontend
if (-not (Test-Path "node_modules")) {
    npm install --no-fund --no-audit
}
npm run build --silent
Pop-Location

Write-Host "== 3/3  Encendiendo Umbral =="
Write-Host ""
Write-Host "   Abre en tu navegador:   http://localhost:8000"
Write-Host "   Para apagarlo:          Ctrl + C"
Write-Host ""
Set-Location backend
& .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
