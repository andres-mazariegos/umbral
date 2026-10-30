// Pantalla de acceso (login) de Umbral.
// Por ahora solo guardo lo que el usuario escribe. Cuando conecte el backend,
// aqui voy a mandar el correo y la contraseña para iniciar sesion con JWT.
import { useState } from "react";
import { Link } from "react-router-dom";
import LluviaCodigo from "../components/LluviaCodigo.jsx";

function Login() {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");

  function entrar(e) {
    e.preventDefault();
    // TODO: conectar con el backend (POST /api/auth/login)
    console.log("intento de acceso:", correo);
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
            <span className="console-title">umbral — acceso</span>
          </div>

          <div className="card-body">
            <p className="intro">
              umbral@local:~$ <span className="c-dim">entrar</span>
            </p>
            <h1>Entra a tu consola</h1>
            <p className="sub">Revisa tu equipo y consulta el historial de tus revisiones.</p>

            <form onSubmit={entrar}>
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
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <button className="btn btn-primary auth-btn" type="submit">
                Entrar
              </button>
            </form>

            <p className="alt">
              ¿Aún no tienes cuenta? <Link to="/login">Créala aquí</Link>
            </p>
          </div>
        </div>

        <p className="auth-foot">Umbral · por Andrés Mazariegos</p>
      </div>
    </>
  );
}

export default Login;
