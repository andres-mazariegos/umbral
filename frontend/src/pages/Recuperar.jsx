// Recuperar la contraseña: pedir el enlace y elegir una nueva.
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api.js";
import { Aviso, Boton, Campo, ReglasClave, reglasClave } from "../components/Basicos.jsx";
import Portal from "../components/Portal.jsx";

export function Olvide() {
  const [email, setEmail] = useState("");
  const [listo, setListo] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return setError("Escribe un correo válido.");
    setCargando(true);
    try {
      setListo(await api("/auth/olvide", { metodo: "POST", datos: { email } }));
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <Portal titulo="Recupera tu acceso" imagen="cerradura" volver="/entrar" frase="Hasta las mejores llaves se pierden. Para eso hay un cerrajero."
      bajada="Escribe tu correo y te mandamos un enlace para elegir una contraseña nueva.">
      {listo ? (
        <>
          <Aviso tipo="bien">{listo.mensaje}</Aviso>
          {listo.dev?.pase && (
            <p className="aviso aviso-dev">Modo desarrollo: <Link to={`/restablecer?pase=${listo.dev.pase}`}>abrir el enlace de recuperación</Link>.</p>
          )}
          <p className="portal-alterno"><Link to="/entrar">Volver a entrar</Link></p>
        </>
      ) : (
        <form onSubmit={enviar} noValidate>
          <Campo etiqueta="Correo" tipo="email" value={email} onChange={(e) => setEmail(e.target.value.trim())} autoComplete="email" maxLength={254} autoFocus />
          <Aviso>{error}</Aviso>
          <Boton cargando={cargando} type="submit">Enviarme el enlace</Boton>
          <p className="portal-alterno"><Link to="/entrar">Ya me acordé</Link></p>
        </form>
      )}
    </Portal>
  );
}

export function Restablecer() {
  const ir = useNavigate();
  const [params] = useSearchParams();
  const pase = params.get("pase") || "";
  const [clave, setClave] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    if (!reglasClave(clave).every((r) => r.ok)) return setError("La contraseña aún no cumple los requisitos.");
    setCargando(true);
    try {
      const r = await api("/auth/restablecer", { metodo: "POST", datos: { pase, clave } });
      ir("/entrar", { replace: true, state: { mensaje: r.mensaje } });
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <Portal titulo="Elige una contraseña nueva" imagen="cerradura" volver="/entrar" frase="Llave nueva. Las copias viejas dejan de servir."
      bajada="Al guardarla se cierran las sesiones abiertas en otros dispositivos.">
      {!pase ? (
        <Aviso>Falta el enlace del correo. <Link to="/olvide">Pide uno nuevo</Link>.</Aviso>
      ) : (
        <form onSubmit={enviar} noValidate>
          <Campo etiqueta="Contraseña nueva" tipo="password" value={clave} onChange={(e) => setClave(e.target.value)} autoComplete="new-password" maxLength={128} autoFocus />
          <ReglasClave clave={clave} />
          <Aviso>{error}</Aviso>
          <Boton cargando={cargando} type="submit">Guardar contraseña</Boton>
        </form>
      )}
    </Portal>
  );
}
