# Umbral en un solo contenedor: primero se compila el sitio, luego corre la API
# (que tambien sirve el sitio ya compilado).
# Sirve igual para Railway (lo detecta solo) y para un servidor propio con docker compose.

FROM node:22-alpine AS sitio
WORKDIR /sitio
COPY frontend/package*.json ./
RUN npm ci --no-fund --no-audit
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /umbral
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY agent/ agent/
COPY --from=sitio /sitio/dist frontend/dist
# El proceso no corre como root dentro del contenedor.
RUN useradd --create-home umbral && mkdir -p /datos && chown -R umbral /datos /umbral
USER umbral
ENV UMBRAL_DATABASE_URL=sqlite:////datos/umbral.db
EXPOSE 8000
WORKDIR /umbral/backend
# Railway decide el puerto y lo pasa en la variable PORT; si no existe se usa 8000.
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]
