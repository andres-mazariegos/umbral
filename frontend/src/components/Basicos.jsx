// Piezas pequeñas que se repiten en todo Umbral.
import { useId, useState } from "react";
import { Link } from "react-router-dom";
import { NIVELES } from "../api.js";

export function Marca({ a = "/" }) {
  return (
    <Link to={a} className="marca" aria-label="Umbral, inicio">
      <svg viewBox="0 0 28 36" aria-hidden="true">
        <path d="M3 34V3h22v31" fill="none" stroke="currentColor" strokeWidth="2.4" />
        <path className="marca-hoja" d="M7 34V7l12 4.5V34z" />
      </svg>
      <span>umbral</span>
    </Link>
  );
}

export function Flecha({ dir = "der" }) {
  return (
    <svg className="flecha" viewBox="0 0 24 24" aria-hidden="true" style={dir === "izq" ? { transform: "scaleX(-1)" } : undefined}>
      <path d="M4 12h15M13 5.5 19.5 12 13 18.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
    </svg>
  );
}

export function Nivel({ nivel, corto }) {
  const n = NIVELES[nivel] || NIVELES.atento;
  return <span className={`nivel nivel-${nivel}`}>{corto ? n.corto : n.nombre}</span>;
}

export function Campo({ etiqueta, error, ayuda, tipo = "text", ...resto }) {
  const id = useId();
  const [ver, setVer] = useState(false);
  const esClave = tipo === "password";
  return (
    <div className={`campo ${error ? "campo-mal" : ""}`}>
      <label htmlFor={id}>{etiqueta}</label>
      <div className="campo-caja">
        <input id={id} type={esClave && ver ? "text" : tipo} aria-invalid={!!error} aria-describedby={`${id}-nota`} {...resto} />
        {esClave && (
          <button type="button" className="campo-ver" onClick={() => setVer(!ver)} aria-pressed={ver}>
            {ver ? "Ocultar" : "Ver"}
          </button>
        )}
      </div>
      <p id={`${id}-nota`} className="campo-nota" role={error ? "alert" : undefined}>{error || ayuda || " "}</p>
    </div>
  );
}

export function Aviso({ tipo = "mal", children }) {
  if (!children) return null;
  return <p className={`aviso aviso-${tipo}`} role={tipo === "mal" ? "alert" : "status"}>{children}</p>;
}

export function Boton({ cargando, children, variante = "lleno", ...resto }) {
  return (
    <button className={`boton boton-${variante}`} disabled={cargando || resto.disabled} {...resto}>
      {cargando ? "Un momento…" : children}
    </button>
  );
}

// Las mismas reglas que valida el servidor, mostradas mientras escribes.
export function reglasClave(clave, nombre = "", email = "") {
  const baja = clave.toLowerCase();
  const partes = [email.split("@")[0], ...nombre.split(" ")].map((p) => p.toLowerCase()).filter((p) => p.length >= 4);
  return [
    { ok: clave.length >= 10, texto: "10 caracteres o más" },
    { ok: /[a-zñ]/.test(clave) && /[A-ZÑ]/.test(clave), texto: "Mayúsculas y minúsculas" },
    { ok: /\d/.test(clave), texto: "Al menos un número" },
    { ok: clave.length > 0 && !partes.some((p) => baja.includes(p)), texto: "Sin tu nombre ni tu correo" },
  ];
}

export function ReglasClave({ clave, nombre, email }) {
  return (
    <ul className="reglas" aria-label="Requisitos de la contraseña">
      {reglasClave(clave, nombre, email).map((r) => (
        <li key={r.texto} className={r.ok ? "regla-ok" : ""}>
          <span aria-hidden="true">{r.ok ? "■" : "□"}</span> {r.texto}
        </li>
      ))}
    </ul>
  );
}

export function Copiar({ texto }) {
  const [hecho, setHecho] = useState(false);
  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(texto);
      setHecho(true);
      setTimeout(() => setHecho(false), 1600);
    } catch {
      /* el navegador no dio permiso: el texto sigue visible para copiarlo a mano */
    }
  };
  return (
    <div className="copiar">
      <code>{texto}</code>
      <button type="button" onClick={copiar}>{hecho ? "Copiado" : "Copiar"}</button>
    </div>
  );
}
