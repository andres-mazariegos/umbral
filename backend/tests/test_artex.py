# Pruebas basadas en el articulo "ARTEX: La nueva era de las pruebas de
# penetracion con IA" (Mtro. Jose Alonso Macias Montoya, 18/11/2026).
#
# El articulo dice que lo primero que intentan esos agentes es:
#   1. bajar source maps (.js.map) y archivos de configuracion del frontend
#   2. leer la documentacion Swagger/OpenAPI expuesta
#   3. usar tokens JWT sin firma ("alg": "none")
#   4. averiguar que correos tienen cuenta con el login o la recuperacion
#   5. ver datos de otro usuario cambiando un numero (IDOR)
#   6. mandar rafagas de peticiones donde no hay limite
# Cada prueba de aqui revisa que Umbral aguante uno de esos ataques.
# Correr desde la carpeta backend:   python -m pytest -q
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Primero test_flujo: ahi se apunta a una base de datos temporal antes de cargar la app.
from tests.test_flujo import CLAVE, cliente, crear_cuenta
from app import config, security
from app.main import app

RAIZ = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _sin_limites():
    security.reiniciar_limites()


def _b64(datos):
    return base64.urlsafe_b64encode(json.dumps(datos).encode()).rstrip(b"=").decode()


# ---- 1. source maps y archivos de configuracion -------------------------

def test_vite_no_genera_source_maps():
    texto = (RAIZ / "frontend" / "vite.config.js").read_text(encoding="utf-8")
    assert "sourcemap: false" in texto


def test_sitio_compilado_sin_archivos_map():
    dist = RAIZ / "frontend" / "dist"
    if not dist.exists():
        pytest.skip("Primero compila el sitio (npm run build)")
    assert list(dist.rglob("*.map")) == []


def test_no_se_pueden_leer_archivos_del_servidor():
    # Pedir la .env, el codigo o la base por la direccion del sitio no debe regresarlos.
    c = cliente()
    for ruta in ("/.env", "/backend/.env", "/../backend/app/config.py", "/%2e%2e/backend/umbral.db",
                 "/env.js", "/assets/config.json", "/.git/config"):
        r = c.get(ruta)
        assert "UMBRAL_SECRET_KEY" not in r.text and "SECRET_KEY" not in r.text and "[core]" not in r.text, ruta
        assert "text/html" in r.headers.get("content-type", "") or r.status_code == 404, ruta


# ---- 2. Swagger / OpenAPI -----------------------------------------------

def test_documentacion_de_la_api_apagada_en_produccion():
    # Se arranca la API en otro proceso con el modo de produccion.
    codigo = "from app.main import app; print(app.docs_url, app.openapi_url, app.redoc_url)"
    entorno = {**os.environ, "UMBRAL_MODO_DEV": "0", "UMBRAL_SECRET_KEY": "x" * 48,
               "UMBRAL_DATABASE_URL": "sqlite://"}
    salida = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ / "backend", env=entorno,
                            capture_output=True, text=True, check=True).stdout.split()
    assert salida == ["None", "None", "None"]


# ---- 3. tokens JWT falsificados -----------------------------------------

def test_token_sin_firma_alg_none_no_sirve():
    c = crear_cuenta(cliente(), "jwt@mazariegoscarlos.com", "Elsa Ruiz")
    usuario_id = c.get("/api/auth/yo").json()["usuario"]["id"]
    falso = f'{_b64({"alg": "none", "typ": "JWT"})}.{_b64({"sub": str(usuario_id), "ver": 1, "exp": 9999999999})}.'
    intruso = cliente()
    intruso.cookies.set(config.NOMBRE_COOKIE, falso)
    assert intruso.get("/api/auth/yo").json()["usuario"] is None
    assert intruso.get("/api/panel").status_code == 401


def test_token_firmado_con_otra_llave_no_sirve():
    import jwt
    c = crear_cuenta(cliente(), "jwt2@mazariegoscarlos.com", "Elsa Mora")
    usuario_id = c.get("/api/auth/yo").json()["usuario"]["id"]
    falso = jwt.encode({"sub": str(usuario_id), "ver": 1, "exp": 9999999999}, "llave-adivinada", algorithm="HS256")
    intruso = cliente()
    intruso.cookies.set(config.NOMBRE_COOKIE, falso)
    assert intruso.get("/api/panel").status_code == 401


# ---- 4. enumeracion de usuarios -----------------------------------------

def test_login_no_revela_si_el_correo_existe():
    crear_cuenta(cliente(), "existe@mazariegoscarlos.com", "Ana Paz")
    a = cliente().post("/api/auth/entrar", json={"email": "existe@mazariegoscarlos.com", "clave": "Incorrecta12345"})
    b = cliente().post("/api/auth/entrar", json={"email": "noexiste@mazariegoscarlos.com", "clave": "Incorrecta12345"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_recuperar_contrasena_no_revela_si_el_correo_existe():
    crear_cuenta(cliente(), "recupera@mazariegoscarlos.com", "Luis Paz")
    a = cliente().post("/api/auth/olvide", json={"email": "recupera@mazariegoscarlos.com"}).json()
    b = cliente().post("/api/auth/olvide", json={"email": "nadie@mazariegoscarlos.com"}).json()
    assert a["mensaje"] == b["mensaje"]


# ---- 5. IDOR: datos de otro usuario --------------------------------------

def test_no_se_ven_revisiones_de_otro_usuario_cambiando_el_numero():
    duena = crear_cuenta(cliente(), "duena@mazariegoscarlos.com", "Rosa Vera")
    rid = duena.post("/api/revisiones/ejemplo").json()["revision_id"]
    intruso = crear_cuenta(cliente(), "curioso@mazariegoscarlos.com", "Juan Vera")
    for numero in range(max(1, rid - 3), rid + 4):          # prueba numeros cercanos, como haria un agente
        assert intruso.get(f"/api/revisiones/{numero}").status_code == 404
    assert intruso.delete(f"/api/revisiones/{rid}").status_code == 404
    assert duena.get(f"/api/revisiones/{rid}").status_code == 200


# ---- 6. rafagas de peticiones ---------------------------------------------

def test_rafaga_contra_el_codigo_de_conexion_se_corta():
    agente = cliente()
    respuestas = [agente.post("/api/agente/enlazar", json={"codigo": f"AAAA-{i:04d}".replace("0", "Z").replace("1", "Y"),
                                                          "sistema": "linux"}).status_code for i in range(12)]
    assert respuestas[0] == 400 and 429 in respuestas
