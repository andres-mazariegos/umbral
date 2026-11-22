// Entrar a la cuenta.
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { Aviso, Boton, Campo } from "../components/Basicos.jsx";
import Portal from "../components/Portal.jsx";
import { useSesion } from "../sesion.jsx";

export default function Login() {
  const ir = useNavigate();
  const { state } = useLocation();
  const { setUsuario } = useSesion();
  const [email, setEmail] = useState("");
  const [clave, setClave] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    if (!email || !clave) return setError("Escribe tu correo y tu contraseña.");
    setCargando(true);
    try {
      const r = await api("/auth/entrar", { metodo: "POST", datos: { email, clave } });
      setUsuario(r.usuario);
      ir(state?.volver || "/panel", { replace: true });
    } catch (err) {
      if (err.motivo === "sin-confirmar") {
        const r = await api("/auth/reenviar", { metodo: "POST", datos: { email } }).catch(() => ({}));
        return ir("/confirmar", { state: { email: email.toLowerCase(), dev: r.dev } });
      }
      setError(err.message);
      setClave("");
    } finally {
      setCargando(false);
    }
  };

  return (
    <Portal titulo="Qué bueno verte" bajada="Entra para ver cómo amaneció tu computadora."
      frase="Las puertas no se cuidan solas. Pero tampoco se necesita un experto.">
      <Aviso tipo="bien">{state?.mensaje}</Aviso>
      <form onSubmit={enviar} noValidate>
        <Campo etiqueta="Correo" tipo="email" value={email} onChange={(e) => setEmail(e.target.value.trim())}
          autoComplete="email" maxLength={254} inputMode="email" autoFocus />
        <Campo etiqueta="Contraseña" tipo="password" value={clave} onChange={(e) => setClave(e.target.value)}
          autoComplete="current-password" maxLength={128} />
        <Aviso>{error}</Aviso>
        <Boton cargando={cargando} type="submit">Entrar</Boton>
      </form>
      <p className="portal-alterno"><Link to="/olvide">¿Olvidaste tu contraseña?</Link></p>
      <p className="portal-alterno">¿Primera vez? <Link to="/registro">Abre tu cuenta</Link></p>
    </Portal>
  );
}
