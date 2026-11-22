# Pruebas de punta a punta de la API de Umbral.
# Correr desde la carpeta backend:   python -m pytest -q
import os
import tempfile

os.environ["UMBRAL_DATABASE_URL"] = os.environ.get("PRUEBA_DB") or "sqlite:///" + os.path.join(tempfile.mkdtemp(), "prueba.db").replace("\\", "/")
os.environ["UMBRAL_MODO_DEV"] = "1"
os.environ["UMBRAL_SMTP_HOST"] = ""
os.environ["UMBRAL_REVISION_LOCAL"] = "1"

import pytest
from fastapi.testclient import TestClient

from app import security
from app.main import app

WEB = {"X-Umbral": "web"}
CLAVE = "Tapachula2026Segura"


@pytest.fixture(autouse=True)
def _sin_limites():
    security.reiniciar_limites()


def cliente():
    return TestClient(app, headers=WEB)


def crear_cuenta(c, email="carlos@mazariegoscarlos.com", nombre="Carlos Mazariegos"):
    r = c.post("/api/auth/registro", json={"nombre": nombre, "email": email, "clave": CLAVE, "acepta": True})
    assert r.status_code == 201, r.text
    codigo = r.json()["dev"]["codigo"]
    r = c.post("/api/auth/confirmar", json={"email": email, "codigo": codigo})
    assert r.status_code == 200, r.text
    return c


def test_registro_rechaza_datos_peligrosos():
    c = cliente()
    base = {"nombre": "Carlos", "email": "a@mazariegoscarlos.com", "clave": CLAVE, "acepta": True}
    for cambio in ({"nombre": "<script>alert(1)</script>"}, {"nombre": "Carlos'; DROP TABLE usuarios;--"},
                   {"nombre": "Carlos123"}, {"email": "no-es-correo"}, {"clave": "corta1A"},
                   {"clave": "sinmayusculas123"}, {"clave": "Password123"}, {"clave": "Carlos2026Segura"},
                   {"acepta": False}, {"rol": "admin"}):
        r = c.post("/api/auth/registro", json={**base, **cambio})
        assert r.status_code == 422, (cambio, r.text)


def test_csrf_sin_cabecera_se_bloquea():
    r = TestClient(app).post("/api/auth/entrar", json={"email": "x@mazariegoscarlos.com", "clave": "x"})
    assert r.status_code == 403


def test_flujo_completo_de_cuenta():
    c = cliente()
    email = "flujo@mazariegoscarlos.com"
    r = c.post("/api/auth/registro", json={"nombre": "Ana Ruiz", "email": email, "clave": CLAVE, "acepta": True})
    codigo = r.json()["dev"]["codigo"]

    # sin confirmar no entra
    assert c.post("/api/auth/entrar", json={"email": email, "clave": CLAVE}).status_code == 403
    # codigo malo
    malo = "000000" if codigo != "000000" else "111111"
    assert c.post("/api/auth/confirmar", json={"email": email, "codigo": malo}).status_code == 400
    # codigo bueno: queda con sesion
    assert c.post("/api/auth/confirmar", json={"email": email, "codigo": codigo}).status_code == 200
    assert c.get("/api/auth/yo").json()["usuario"]["email"] == email
    # el mismo codigo no sirve dos veces
    assert c.post("/api/auth/confirmar", json={"email": email, "codigo": codigo}).status_code == 400
    # la cookie es HttpOnly y SameSite=Strict
    c.post("/api/auth/salir")
    r = c.post("/api/auth/entrar", json={"email": email, "clave": CLAVE})
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    # registrar el mismo correo responde igual (no revela que existe)
    r2 = cliente().post("/api/auth/registro", json={"nombre": "Otro", "email": email, "clave": CLAVE, "acepta": True})
    assert r2.status_code == 201 and "dev" not in r2.json()


def test_bloqueo_tras_cinco_fallos():
    email = "bloqueo@mazariegoscarlos.com"
    crear_cuenta(cliente(), email, "Luis Mora")
    c = cliente()
    for _ in range(5):
        assert c.post("/api/auth/entrar", json={"email": email, "clave": "Incorrecta12345"}).status_code == 401
    assert c.post("/api/auth/entrar", json={"email": email, "clave": CLAVE}).status_code == 423


def test_limite_de_intentos_por_ip():
    c = cliente()
    codigos = [c.post("/api/auth/entrar", json={"email": "nadie@mazariegoscarlos.com", "clave": "x"}).status_code for _ in range(14)]
    assert codigos[0] == 401 and codigos[-1] == 429


def test_restablecer_cierra_sesiones():
    email = "olvido@mazariegoscarlos.com"
    c = crear_cuenta(cliente(), email, "Marta Solis")
    pase = cliente().post("/api/auth/olvide", json={"email": email}).json()["dev"]["pase"]
    assert cliente().post("/api/auth/restablecer", json={"pase": pase, "clave": "OtraClaveLarga2026"}).status_code == 200
    assert c.get("/api/auth/yo").json()["usuario"] is None            # la sesion vieja ya no sirve
    assert cliente().post("/api/auth/restablecer", json={"pase": pase, "clave": "OtraClaveLarga2027"}).status_code == 400
    assert cliente().post("/api/auth/entrar", json={"email": email, "clave": "OtraClaveLarga2026"}).status_code == 200


def test_agente_y_revisiones():
    c = crear_cuenta(cliente(), "equipo@mazariegoscarlos.com", "Rosa Lima")
    # sin permiso no hay codigo
    assert c.post("/api/equipos/enlace", json={"nombre": "Laptop 243790", "permiso": False}).status_code == 422
    assert c.post("/api/equipos/enlace", json={"nombre": "Laptop<script>", "permiso": True}).status_code == 422
    enlace = c.post("/api/equipos/enlace", json={"nombre": "Laptop 243790", "permiso": True}).json()

    agente = TestClient(app)        # el agente no manda cookies ni cabecera web
    assert agente.post("/api/agente/enlazar", json={"codigo": "AAAA-BBBB", "sistema": "linux"}).status_code == 400
    r = agente.post("/api/agente/enlazar", json={"codigo": enlace["codigo"], "sistema": "windows", "detalle_sistema": "Windows 11"})
    llave = r.json()["llave"]
    assert agente.post("/api/agente/enlazar", json={"codigo": enlace["codigo"], "sistema": "windows"}).status_code == 400   # un solo uso

    reporte = {"sistema": "windows", "detalle_sistema": "Windows 11", "cortafuegos": "apagado", "puertos": [
        {"puerto": 3389, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "svchost.exe", "ruta": ""},
        {"puerto": 3389, "protocolo": "tcp", "direccion": "::", "proceso": "svchost.exe", "ruta": ""},
        {"puerto": 5432, "protocolo": "tcp", "direccion": "127.0.0.1", "proceso": "postgres.exe", "ruta": ""},
        {"puerto": 4444, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "x.exe", "ruta": "~\\AppData\\Local\\Temp\\x.exe"}]}
    assert agente.post("/api/agente/revisiones", json=reporte).status_code == 401
    assert agente.post("/api/agente/revisiones", json=reporte, headers={"Authorization": "Bearer llave-falsa"}).status_code == 401
    r = agente.post("/api/agente/revisiones", json=reporte, headers={"Authorization": f"Bearer {llave}"})
    assert r.status_code == 200 and r.json()["resumen"]["urgente"] == 2, r.text
    rid = r.json()["revision_id"]

    detalle = c.get(f"/api/revisiones/{rid}").json()
    assert len(detalle["hallazgos"]) == 3                                   # 3389 llego dos veces y se junto
    assert detalle["hallazgos"][0]["nivel"] == "urgente"
    postgres = next(h for h in detalle["hallazgos"] if h["puerto"] == 5432)
    assert postgres["alcance"] == "interno" and postgres["nivel"] == "tranquilo"

    # marcar y comparar con una segunda revision
    rdp = next(h for h in detalle["hallazgos"] if h["puerto"] == 3389)
    assert c.patch(f"/api/hallazgos/{rdp['id']}", json={"estado": "aceptado"}).json()["estado"] == "aceptado"
    reporte["puertos"] = reporte["puertos"][:2] + [{"puerto": 21, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "ftp.exe", "ruta": ""}]
    rid2 = agente.post("/api/agente/revisiones", json=reporte, headers={"Authorization": f"Bearer {llave}"}).json()["revision_id"]
    d2 = c.get(f"/api/revisiones/{rid2}").json()
    assert [n["puerto"] for n in d2["cambios"]["nuevas"]] == [21]
    assert sorted(n["puerto"] for n in d2["cambios"]["cerradas"]) == [4444, 5432]
    assert next(h for h in d2["hallazgos"] if h["puerto"] == 3389)["estado"] == "aceptado"   # se respeta la decision

    # otra persona no puede ver esta revision ni tocar sus hallazgos
    otro = crear_cuenta(cliente(), "intruso@mazariegoscarlos.com", "Pedro Paz")
    assert otro.get(f"/api/revisiones/{rid}").status_code == 404
    assert otro.patch(f"/api/hallazgos/{rdp['id']}", json={"estado": "resuelto"}).status_code == 404

    # al quitar el equipo, su llave deja de servir
    equipo_id = c.get("/api/equipos").json()["equipos"][0]["id"]
    assert c.delete(f"/api/equipos/{equipo_id}").status_code == 200
    assert agente.post("/api/agente/revisiones", json=reporte, headers={"Authorization": f"Bearer {llave}"}).status_code == 401
    assert c.get(f"/api/revisiones/{rid}").status_code == 200              # el historial se conserva


def test_directa_ejemplo_y_panel():
    c = crear_cuenta(cliente(), "panel@mazariegoscarlos.com", "Sara Luna")
    assert c.post("/api/revisiones/directa").status_code == 201
    r = c.post("/api/revisiones/ejemplo")
    assert r.status_code == 201 and r.json()["resumen"]["urgente"] >= 4
    panel = c.get("/api/panel").json()
    assert panel["revisiones"] == 2 and len(panel["pendientes"]) >= 4
    assert c.get("/api/puertos/3389").json()["nivel"] == "urgente"
    assert c.get("/api/puertos/70000").status_code == 422


def test_cuenta_cambiar_clave_y_eliminar():
    email = "ajustes@mazariegoscarlos.com"
    c = crear_cuenta(cliente(), email, "Iris Vera")
    assert c.post("/api/cuenta/clave", json={"actual": "mala", "nueva": "NuevaClaveLarga2026"}).status_code == 400
    assert c.post("/api/cuenta/clave", json={"actual": CLAVE, "nueva": "NuevaClaveLarga2026"}).status_code == 200
    assert c.get("/api/auth/yo").json()["usuario"]["email"] == email
    assert any(e["tipo"] == "clave_cambiada" for e in c.get("/api/cuenta/actividad").json()["eventos"])
    assert c.post("/api/cuenta/eliminar", json={"clave": "NuevaClaveLarga2026"}).status_code == 200
    assert cliente().post("/api/auth/entrar", json={"email": email, "clave": "NuevaClaveLarga2026"}).status_code == 401


def test_cabeceras_de_seguridad():
    r = cliente().get("/api/salud")
    assert r.headers["x-frame-options"] == "DENY" and "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["cache-control"] == "no-store"
