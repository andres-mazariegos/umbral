// Crear cuenta. Valida lo mismo que el servidor, pero mientras escribes.
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { Aviso, Boton, Campo, ReglasClave, reglasClave } from "../components/Basicos.jsx";
import Portal from "../components/Portal.jsx";

const SOLO_LETRAS = /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]/g;

export default function Registro() {
  const ir = useNavigate();
  const [f, setF] = useState({ nombre: "", email: "", clave: "", acepta: false });
  const [errores, setErrores] = useState({});
  const [general, setGeneral] = useState("");
  const [cargando, setCargando] = useState(false);
  const [quitado, setQuitado] = useState(false);

  const cambiarNombre = (e) => {
    // Los simbolos y numeros ni siquiera llegan a escribirse.
    const limpio = e.target.value.replace(SOLO_LETRAS, "").replace(/\s{2,}/g, " ").slice(0, 60);
    setQuitado(limpio !== e.target.value);
    setF({ ...f, nombre: limpio });
  };

  const enviar = async (e) => {
    e.preventDefault();
    const er = {};
    if (f.nombre.trim().length < 2) er.nombre = "Escribe tu nombre (solo letras).";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(f.email)) er.email = "Escribe un correo válido, como nombre@dominio.com.";
    if (!reglasClave(f.clave, f.nombre, f.email).every((r) => r.ok)) er.clave = "La contraseña aún no cumple los requisitos.";
    if (!f.acepta) er.acepta = "Necesitas aceptar el aviso para continuar.";
    setErrores(er);
    setGeneral("");
    if (Object.keys(er).length) return;

    setCargando(true);
    try {
      const r = await api("/auth/registro", { metodo: "POST", datos: { ...f, nombre: f.nombre.trim(), email: f.email.trim() } });
      ir("/confirmar", { state: { email: f.email.trim().toLowerCase(), dev: r.dev, correoReal: r.correo_real } });
    } catch (err) {
      setErrores(err.campos || {});
      setGeneral(err.campos && Object.keys(err.campos).length ? "" : err.message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <Portal titulo="Abre tu cuenta" bajada="Un minuto. Después revisas tu primera computadora."
      frase="Toda casa segura empieza por saber cuántas puertas tiene.">
      <form onSubmit={enviar} noValidate>
        <Campo etiqueta="Tu nombre" value={f.nombre} onChange={cambiarNombre} autoComplete="name" maxLength={60}
          error={errores.nombre} ayuda={quitado ? "Solo letras y espacios: lo demás se quita solo." : "Como quieres que te llamemos."} />
        <Campo etiqueta="Correo" tipo="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value.trim() })}
          autoComplete="email" maxLength={254} inputMode="email" error={errores.email} ayuda="Ahí te llega el código de confirmación." />
        <Campo etiqueta="Contraseña" tipo="password" value={f.clave} onChange={(e) => setF({ ...f, clave: e.target.value })}
          autoComplete="new-password" maxLength={128} error={errores.clave}
          ayuda="Consejo: una frase larga que solo tú entiendas vale más que símbolos raros." />
        <ReglasClave clave={f.clave} nombre={f.nombre} email={f.email} />
        <label className={`casilla ${errores.acepta ? "casilla-mal" : ""}`}>
          <input type="checkbox" checked={f.acepta} onChange={(e) => setF({ ...f, acepta: e.target.checked })} />
          <span>Leí y acepto el <Link to="/privacidad" target="_blank">aviso de privacidad</Link>.</span>
        </label>
        <Aviso>{errores.acepta || general}</Aviso>
        <Boton cargando={cargando} type="submit">Crear cuenta</Boton>
      </form>
      <p className="portal-alterno">¿Ya tienes cuenta? <Link to="/entrar">Entrar</Link></p>
    </Portal>
  );
}
