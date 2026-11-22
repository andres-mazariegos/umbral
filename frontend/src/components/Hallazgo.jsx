// Una puerta abierta, explicada. Se despliega al tocarla.
import { useState } from "react";
import { api, SISTEMAS } from "../api.js";
import { Nivel } from "./Basicos.jsx";

const ESTADOS = { resuelto: "Marcada como cerrada", aceptado: "La necesitas abierta" };

// Dentro de un paso, lo que va despues de "ejecuta:" o parece comando se muestra como codigo.
function Paso({ texto }) {
  const m = texto.match(/^(.*?:\s)((?:sudo |ps |vncserver |Disable-|Stop-).+)$/);
  if (m) return <li>{m[1]}<code>{m[2]}</code></li>;
  if (/^(sudo |ps aux)/.test(texto)) return <li><code>{texto}</code></li>;
  return <li>{texto}</li>;
}

export default function Hallazgo({ h, sistema, alCambiar, abiertoDeInicio = false, todoAbierto = false }) {
  const [abiertoPorClic, setAbierto] = useState(abiertoDeInicio);
  const abierto = abiertoPorClic || todoAbierto;
  const [so, setSo] = useState(sistema === "linux" ? "linux" : "windows");
  const [guardando, setGuardando] = useState(false);

  const marcar = async (estado) => {
    setGuardando(true);
    try {
      alCambiar(await api(`/hallazgos/${h.id}`, { metodo: "PATCH", datos: { estado } }));
    } finally {
      setGuardando(false);
    }
  };

  const atendido = h.estado !== "pendiente";
  return (
    <li className={`puerta puerta-${h.nivel} ${abierto ? "puerta-abierta" : ""} ${atendido ? "puerta-atendida" : ""}`}>
      <button type="button" className="puerta-cara" onClick={() => setAbierto(!abiertoPorClic)} aria-expanded={abierto}>
        <span className="puerta-n">{h.puerto}</span>
        <span className="puerta-titulo">
          <b>{h.titulo}</b>
          <small>{h.alcance === "red" ? "Abierta a tu red" : "Solo dentro de tu equipo"}{h.proceso ? ` · ${h.proceso}` : ""}</small>
        </span>
        {atendido ? <span className="puerta-estado">{ESTADOS[h.estado]}</span> : <Nivel nivel={h.nivel} />}
        <svg className="puerta-giro" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" /></svg>
      </button>

      {abierto && (
        <div className="puerta-dentro">
          <p className="puerta-maquina" title="Así lo reporta el sistema">
            {h.protocolo} {h.direccion}:{h.puerto} {h.proceso || "?"}{h.ruta ? `  ${h.ruta}` : ""}
          </p>
          <div className="puerta-texto">
            <h4>Qué es</h4>
            <p>{h.explicacion}</p>
            <h4>Qué puede pasar</h4>
            <p>{h.riesgo}</p>
            {h.senales.map((s) => <p className="puerta-senal" key={s}>{s}</p>)}
          </div>
          <div className="puerta-pasos">
            <div className="puerta-so" role="tablist" aria-label="Sistema operativo">
              <h4>{h.nivel === "tranquilo" ? "Si quieres revisarla" : "Cómo cerrarla"}</h4>
              {["windows", "linux"].map((s) => (
                <button key={s} type="button" role="tab" aria-selected={so === s} onClick={() => setSo(s)}>{SISTEMAS[s]}</button>
              ))}
            </div>
            <ol>{(h.pasos[so] || []).map((p) => <Paso key={p} texto={p} />)}</ol>
          </div>
          <div className="puerta-acciones">
            {atendido ? (
              <button type="button" className="boton boton-linea" disabled={guardando} onClick={() => marcar("pendiente")}>Volver a pendiente</button>
            ) : (
              <>
                <button type="button" className="boton boton-lleno" disabled={guardando} onClick={() => marcar("resuelto")}>Ya la cerré</button>
                <button type="button" className="boton boton-linea" disabled={guardando} onClick={() => marcar("aceptado")}>La necesito abierta</button>
              </>
            )}
          </div>
        </div>
      )}
    </li>
  );
}
