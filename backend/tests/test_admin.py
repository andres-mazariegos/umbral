# Pruebas del rol de administrador.
# Correr desde la carpeta backend:   python -m pytest -q
from tests.test_flujo import CLAVE, cliente, crear_cuenta
from app import config


def test_usuario_normal_no_ve_administracion():
    c = crear_cuenta(cliente(), "normal@mazariegoscarlos.com", "Rosa Pérez")
    assert c.get("/api/auth/yo").json()["usuario"]["es_admin"] is False
    # Responde 404 como si la seccion no existiera.
    for ruta in ("/api/admin/resumen", "/api/admin/cuentas", "/api/admin/bitacora"):
        assert c.get(ruta).status_code == 404


def test_sin_sesion_no_hay_administracion():
    assert cliente().get("/api/admin/resumen").status_code == 401


def test_administrador_ve_cifras_y_correos_enmascarados():
    config.ADMINS.add("jefe@mazariegoscarlos.com")
    try:
        c = crear_cuenta(cliente(), "jefe@mazariegoscarlos.com", "Carlos Admin")
        assert c.get("/api/auth/yo").json()["usuario"]["es_admin"] is True
        resumen = c.get("/api/admin/resumen").json()
        assert resumen["cuentas"] >= 1 and "niveles" in resumen
        cuentas = c.get("/api/admin/cuentas").json()["cuentas"]
        assert all("*" in fila["correo"] for fila in cuentas)
        assert not any("jefe@" in fila["correo"] for fila in cuentas)
        assert c.get("/api/admin/bitacora?solo_alertas=true").status_code == 200
    finally:
        config.ADMINS.discard("jefe@mazariegoscarlos.com")


def test_administrador_desbloquea_una_cuenta():
    config.ADMINS.add("jefa@mazariegoscarlos.com")
    try:
        crear_cuenta(cliente(), "bloqueado@mazariegoscarlos.com", "Luis Gómez")
        otro = cliente()
        for _ in range(config.INTENTOS_LOGIN):
            otro.post("/api/auth/entrar", json={"email": "bloqueado@mazariegoscarlos.com", "clave": "Equivocada2026x"})
        r = otro.post("/api/auth/entrar", json={"email": "bloqueado@mazariegoscarlos.com", "clave": CLAVE})
        assert r.status_code in (423, 429), r.text

        admin = crear_cuenta(cliente(), "jefa@mazariegoscarlos.com", "Ana Admin")
        fila = next(f for f in admin.get("/api/admin/cuentas").json()["cuentas"] if f["nombre"] == "Luis Gómez")
        assert fila["bloqueado"] is True
        assert admin.post(f"/api/admin/cuentas/{fila['id']}/desbloquear").status_code == 200
        r = otro.post("/api/auth/entrar", json={"email": "bloqueado@mazariegoscarlos.com", "clave": CLAVE})
        assert r.status_code == 200, r.text
    finally:
        config.ADMINS.discard("jefa@mazariegoscarlos.com")
