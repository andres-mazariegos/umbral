// Pantalla de registro de Umbral.
// Creo la cuenta del usuario. Por ahora solo guardo los datos en el estado;
// mas adelante los mando al backend (POST /api/auth/register).
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import LluviaCodigo from "../components/LluviaCodigo.jsx";

function Registro() {
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [error, setError] = useState("");

  function crearCuenta(e) {
    e.preventDefault();
    // validacion sencilla antes de mandar al backend
    if (password !== confirmar) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setError("");
    // TODO: conectar con el backend (POST /api/auth/register)
    console.log("crear cuenta:", { nombre, correo });
    // despues de registrarse, paso a confirmar el correo con el codigo
    navigate("/confirmar", { state: { correo } });
  }

  return (
    <>
      <LluviaCodigo />

      <div className="auth-wrap">
        <Link to="/" style={{ textDecoration: "none", color: "var(--paper)" }}>
          <div className="auth-brand">
            Umbr<span className="b-green">a</span>l
          </div>
        </Link>

        <div className="card">
          <div className="console-bar">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="console-title">umbral — crear cuenta</span>
          </div>

          <div className="card-body">
            <p className="intro">
              umbral@local:~$ <span className="c-dim">registrar</span>
            </p>
            <h1>Crea tu cuenta</h1>
            <p className="sub">Regístrate para revisar tu equipo y guardar tu historial.</p>

            <form onSubmit={crearCuenta}>
              <div className="field">
                <label htmlFor="nombre">Nombre</label>
                <input
                  id="nombre"
                  type="text"
                  placeholder="Tu nombre"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="correo">Correo</label>
                <input
                  id="correo"
                  type="email"
                  placeholder="tucorreo@ejemplo.com"
                  autoComplete="email"
                  value={correo}
                  onChange={(e) => setCorreo(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="password">Contraseña</label>
                <input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="confirmar">Confirmar contraseña</label>
                <input
                  id="confirmar"
                  type="password"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  value={confirmar}
                  onChange={(e) => setConfirmar(e.target.value)}
                />
              </div>

              {error && <p className="form-error">{error}</p>}

              <button className="btn btn-primary auth-btn" type="submit">
                Crear cuenta
              </button>
            </form>

            <p className="alt">
              ¿Ya tienes cuenta? <Link to="/login">Entra aquí</Link>
            </p>
          </div>
        </div>

        <p className="auth-foot">Umbral · por Andrés Mazariegos</p>
      </div>
    </>
  );
}

export default Registro;
