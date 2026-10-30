// Pantalla para confirmar el correo con un codigo de 6 digitos.
// El codigo lo genera y envia el backend por correo. Aqui el usuario lo escribe
// y lo verifico (POST /api/auth/verify) cuando conecte el backend.
import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import LluviaCodigo from "../components/LluviaCodigo.jsx";

function Confirmar() {
  const location = useLocation();
  const navigate = useNavigate();
  const correo = location.state?.correo || "tu correo";

  const [codigo, setCodigo] = useState("");
  const [error, setError] = useState("");

  function confirmar(e) {
    e.preventDefault();
    if (codigo.length !== 6) {
      setError("El código debe tener 6 dígitos.");
      return;
    }
    setError("");
    // TODO: verificar el codigo con el backend (POST /api/auth/verify)
    console.log("confirmar codigo:", codigo);
    navigate("/login");
  }

  function reenviar() {
    // TODO: pedir al backend que reenvie el codigo (POST /api/auth/resend)
    console.log("reenviar codigo a:", correo);
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
            <span className="console-title">umbral — confirmar correo</span>
          </div>

          <div className="card-body">
            <p className="intro">
              umbral@local:~$ <span className="c-dim">confirmar</span>
            </p>
            <h1>Confirma tu correo</h1>
            <p className="sub">
              Te enviamos un código de 6 dígitos a <b style={{ color: "var(--paper)" }}>{correo}</b>. Escríbelo aquí para activar tu cuenta.
            </p>

            <form onSubmit={confirmar}>
              <div className="field">
                <label htmlFor="codigo">Código de verificación</label>
                <input
                  id="codigo"
                  className="code-input"
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="______"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value.replace(/\D/g, ""))}
                />
              </div>

              {error && <p className="form-error">{error}</p>}

              <button className="btn btn-primary auth-btn" type="submit">
                Confirmar
              </button>
            </form>

            <p className="alt">
              ¿No te llegó?{" "}
              <button type="button" className="link-btn" onClick={reenviar}>
                Reenviar código
              </button>
            </p>
          </div>
        </div>

        <p className="auth-foot">Umbral · por Andrés Mazariegos</p>
      </div>
    </>
  );
}

export default Confirmar;
