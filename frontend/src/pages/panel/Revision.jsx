// Detalle de una revision: todas las puertas, de la mas urgente a la mas tranquila.
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, fecha, plural, SISTEMAS } from "../../api.js";
import { Aviso, Nivel } from "../../components/Basicos.jsx";
import Volver from "../../components/Volver.jsx";
import Hallazgo from "../../components/Hallazgo.jsx";

const CORTAFUEGOS = {
  activo: { clase: "tranquilo", texto: "Tu cortafuegos está encendido: es el portero que decide quién puede tocar estas puertas desde fuera." },
  apagado: { clase: "urgente", texto: "Tu cortafuegos está apagado. Sin portero, cualquier equipo de tu red puede tocar las puertas abiertas. Enciéndelo antes que nada." },
  desconocido: { clase: "atento", texto: "No pudimos ver si tu cortafuegos está encendido. Ejecuta el agente como administrador para saberlo." },
};
const FILTROS = [["todas", "Todas"], ["urgente", "Atiéndelo ya"], ["atento", "Ojo aquí"], ["tranquilo", "Tranquilo"]];

export default function Revision() {
  const { id } = useParams();
  const ir = useNavigate();
  const [params] = useSearchParams();
  const [r, setR] = useState(null);
  const [error, setError] = useState("");
  const [filtro, setFiltro] = useState("todas");
  const [imprimiendo, setImprimiendo] = useState(false);

  // Al imprimir se abren todas las puertas para que el reporte salga completo.
  useEffect(() => {
    const antes = () => setImprimiendo(true);
    const despues = () => setImprimiendo(false);
    window.addEventListener("beforeprint", antes);
    window.addEventListener("afterprint", despues);
    return () => {
      window.removeEventListener("beforeprint", antes);
      window.removeEventListener("afterprint", despues);
    };
  }, []);

  useEffect(() => {
    setR(null);
    api(`/revisiones/${id}`).then(setR).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <div className="cargando"><Aviso>{error}</Aviso><Link to="/panel">Volver al inicio</Link></div>;
  if (!r) return <div className="cargando">Abriendo la revisión…</div>;

  const cambiar = (nuevo) => setR({ ...r, hallazgos: r.hallazgos.map((h) => (h.id === nuevo.id ? nuevo : h)) });
  const borrar = async () => {
    if (!window.confirm("¿Borrar esta revisión? No se puede deshacer.")) return;
    await api(`/revisiones/${id}`, { metodo: "DELETE" });
    ir("/panel/historial");
  };

  const cuenta = (n) => r.hallazgos.filter((h) => h.nivel === n).length;
  const porAtender = r.hallazgos.filter((h) => h.nivel === "urgente" && h.estado === "pendiente").length;
  const visibles = r.hallazgos.filter((h) => filtro === "todas" || h.nivel === filtro);
  const cf = CORTAFUEGOS[r.cortafuegos] || CORTAFUEGOS.desconocido;
  const abrir = Number(params.get("abrir"));

  return (
    <div className="revision">
      <Volver />
      <header className={`cabeza ${porAtender ? "cabeza-alerta" : ""}`}>
        <p className="antetitulo">
          {r.nombre_equipo || "Equipo"} · {SISTEMAS[r.sistema] || r.sistema} · {fecha(r.creado)}
          {r.origen === "ejemplo" && " · Datos de ejemplo"}
        </p>
        <h1>
          {r.hallazgos.length === 0 ? "No encontramos ninguna puerta abierta."
            : porAtender ? <>{plural(r.hallazgos.length, "puerta abierta", "puertas abiertas")}. <em>{porAtender === 1 ? "Una pide" : `${porAtender} piden`} atención.</em></>
            : <>{plural(r.hallazgos.length, "puerta abierta", "puertas abiertas")}, <em>nada urgente pendiente.</em></>}
        </h1>
        <p className={`portero portero-${cf.clase}`}>{cf.texto}</p>
      </header>

      {r.cambios && (r.cambios.nuevas.length > 0 || r.cambios.cerradas.length > 0) && (
        <section className="cambios">
          <h2>Qué cambió desde el {fecha(r.cambios.fecha)}</h2>
          <div className="cambios-dos">
            {r.cambios.nuevas.length > 0 && (
              <div>
                <h3>Se abrieron</h3>
                <ul>{r.cambios.nuevas.map((c) => <li key={`n${c.puerto}${c.protocolo}`}><b>{c.puerto}</b> {c.titulo} <Nivel nivel={c.nivel} corto /></li>)}</ul>
              </div>
            )}
            {r.cambios.cerradas.length > 0 && (
              <div>
                <h3>Se cerraron</h3>
                <ul>{r.cambios.cerradas.map((c) => <li key={`c${c.puerto}${c.protocolo}`}><b>{c.puerto}</b> {c.titulo}</li>)}</ul>
              </div>
            )}
          </div>
        </section>
      )}
      {r.cambios && r.cambios.nuevas.length === 0 && r.cambios.cerradas.length === 0 && (
        <p className="sin-cambios">Sin cambios desde la revisión del {fecha(r.cambios.fecha)}: las mismas puertas, ni una más.</p>
      )}

      {r.hallazgos.length > 0 && (
        <>
          <div className="filtros" role="tablist" aria-label="Filtrar por nivel">
            {FILTROS.map(([clave, texto]) => {
              const n = clave === "todas" ? r.hallazgos.length : cuenta(clave);
              return (
                <button key={clave} type="button" role="tab" aria-selected={filtro === clave} disabled={n === 0} onClick={() => setFiltro(clave)}>
                  {texto} <b>{n}</b>
                </button>
              );
            })}
          </div>
          <ul className="puertas-lista">
            {visibles.map((h) => (
              <Hallazgo key={h.id} h={h} sistema={r.sistema} alCambiar={cambiar} abiertoDeInicio={h.id === abrir} todoAbierto={imprimiendo} />
            ))}
          </ul>
        </>
      )}

      <p className="revision-pie">
        <button type="button" className="boton boton-linea" onClick={() => window.print()}>Imprimir o guardar en PDF</button>
        <button type="button" className="enlace enlace-peligro" onClick={borrar}>Borrar esta revisión</button>
      </p>
    </div>
  );
}
