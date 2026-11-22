#!/usr/bin/env bash
# Arranca Umbral en Linux (Kali, Ubuntu, Debian) con un solo comando:
#     ./iniciar.sh
# La primera vez instala todo (tarda unos minutos). Despues abre en segundos.
set -e
cd "$(dirname "$0")"

echo "== 1/3  Preparando el backend (Python) =="
if [ ! -d backend/.venv ]; then
  python3 -m venv backend/.venv
fi
backend/.venv/bin/pip install --quiet --upgrade pip
backend/.venv/bin/pip install --quiet -r backend/requirements.txt

echo "== 2/3  Preparando el sitio (Node) =="
if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm install --no-fund --no-audit)
fi
(cd frontend && npm run build --silent)

echo "== 3/3  Encendiendo Umbral =="
echo
echo "   Abre en tu navegador:   http://localhost:8000"
echo "   Para apagarlo:          Ctrl + C"
echo
cd backend
exec .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
