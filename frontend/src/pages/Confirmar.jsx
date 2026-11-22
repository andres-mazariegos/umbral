// Confirmar el correo: escribiendo el codigo de 6 numeros o llegando
// directo desde el boton del correo (trae ?pase=... en la direccion).
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api.js";
import { Aviso, Boton, Campo } from "../components/Basicos.jsx";
import Portal from "../components/Portal.jsx";
import { useSesion } from "../sesion.jsx";

export default function Confirmar() {
  const ir = useNavigate();
  const { state } = useLocation();
  const [params] = useSearchParams();
  const { setUsuario } = useSesion();
  const pase = params.get("pase");
  const [email, setEmail] = useState(state?.email || "");
  const [codigo, setCodigo] = useState("");
  const [dev, setDev] = useState(state?.dev || null);
  const [error, setError] = useState("");
  const [nota, setNota] = useState("");
  const [cargando, setCargando] = useState(false);
  const [espera, setEspera] = useState(30);
  const intentado = useRef(false);

  const entrar = (r) => { setUsuario(r.usuario); ir("/panel", { replace: true, state: { bienvenida: true } }); };

  // Llego por el boton del correo
  useEffect(() => {
    if (!pase || intentado.current) return;
    intentado.current = true;
    setCargando(true);
    api("/auth/confirmar", { metodo: "POST", datos: { pase } }).then(entrar)
      .catch((e) => setError(e.message)).finally(() => setCargando(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pase]);

  useEffect(() => {
    if (espera <= 0) return;
    const t = setTimeout(() => setEspera(espera - 1), 1000);
    return () => clearTimeout(t);
  }, [espera]);

  const enviar = async (e) => {
    e.preventDefault();
    setError(""); setNota("");
    if (!/^\d{6}$/.test(codigo)) return setError("El código son 6 números.");
    setCargando(true);
    try {
      entrar(await api("/auth/confirmar", { metodo: "POST", datos: { email, codigo } }));
    } catch (err) {
      setError(err.message);
      setCodigo("");
    } finally {
      setCargando(false);
    }
  };

  const reenviar = async () => {
    setError(""); setNota("");
    try {
      const r = await api("/auth/reenviar", { metodo: "POST", datos: { email } });
      setNota(r.mensaje);
      if (r.dev) setDev(r.dev);
      setEspera(60);
    } catch (err) {
      setError(err.message);
    }
  };

  if (pase) {
    return (
      <Portal titulo={error ? "Ese enlace ya no sirve" : "Confirmando tu correo…"} imagen="cerradura"
        frase="Un código, una sola vez. Así nadie más abre tu cuenta.">
        <Aviso>{error}</Aviso>
        {error && <p className="portal-alterno"><Link to="/entrar">Ir a entrar</Link> y pide un código nuevo.</p>}
      </Portal>
    );
  }

  return (
    <Portal titulo="Revisa tu correo" imagen="cerradura" volver="/registro"
      bajada={email ? <>Mandamos un código de 6 números a <b>{email}</b>. Vence en 15 minutos.</> : "Escribe tu correo y el código de 6 números que te enviamos."}
      frase="Un código, una sola vez. Así nadie más abre tu cuenta.">
      {dev?.codigo && (
        <p className="aviso aviso-dev">
          Modo desarrollo: no hay correo configurado, así que el código es <b>{dev.codigo}</b>.
          También aparece en la consola del servidor.
        </p>
      )}
      <form onSubmit={enviar} noValidate>
        {!state?.email && (
          <Campo etiqueta="Correo" tipo="email" value={email} onChange={(e) => setEmail(e.target.value.trim())} autoComplete="email" maxLength={254} />
        )}
        <div className="campo">
          <label htmlFor="codigo">Código</label>
          <input id="codigo" className="codigo" value={codigo} inputMode="numeric" autoComplete="one-time-code" maxLength={6}
            autoFocus placeholder="······" onChange={(e) => setCodigo(e.target.value.replace(/\D/g, "").slice(0, 6))} />
        </div>
        <Aviso>{error}</Aviso>
        <Aviso tipo="bien">{nota}</Aviso>
        <Boton cargando={cargando} type="submit">Confirmar y entrar</Boton>
      </form>
      <p className="portal-alterno">
        ¿No llegó? Mira en spam o{" "}
        <button type="button" className="enlace" onClick={reenviar} disabled={espera > 0 || !email}>
          {espera > 0 ? `pide otro en ${espera} s` : "pide otro código"}
        </button>
      </p>
    </Portal>
  );
}
