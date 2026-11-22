// Todas las revisiones, de la mas reciente a la mas vieja.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, dia, SISTEMAS } from "../../api.js";
import { Aviso, Flecha } from "../../components/Basicos.jsx";

const HORA = new Intl.DateTimeFormat("es-MX", { hour: "numeric", minute: "2-digit" });
const ORIGEN = { agente: "Agente", directa: "Directa", ejemplo: "Ejemplo" };

export default function Historial() {
  const [lista, setLista] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/revisiones").then((r) => setLista(r.revisiones)).catch((e) => setError(e.message));
  }, []);

  if (!lista) return <div className="cargando">{error || "Cargando historial…"}</div>;

  // Agrupa por dia para leerlo como una bitacora.
  const dias = [];
  for (const r of lista) {
    const clave = dia(r.creado);
    if (!dias.length || dias[dias.length - 1].clave !== clave) dias.push({ clave, items: [] });
    dias[dias.length - 1].items.push(r);
  }

  return (
    <div className="historial">
      <header className="cabeza">
        <p className="antetitulo">Historial</p>
        <h1>{lista.length ? "Cada vez que contaste tus puertas." : "Aún no hay revisiones."}</h1>
      </header>
      <Aviso>{error}</Aviso>
      {!lista.length && <p>Cuando hagas tu primera revisión aparecerá aquí. <Link to="/panel">Ir al inicio</Link></p>}
      {dias.map((d) => (
        <section className="bitacora" key={d.clave}>
          <h2>{d.clave}</h2>
          <ul>
            {d.items.map((r) => (
              <li key={r.id}>
                <Link to={`/panel/revision/${r.id}`}>
                  <time>{HORA.format(new Date(r.creado))}</time>
                  <span className="bitacora-equipo"><b>{r.nombre_equipo || "Equipo"}</b><small>{SISTEMAS[r.sistema] || r.sistema} · {ORIGEN[r.origen]}</small></span>
                  <span className="bitacora-barras" aria-label={`${r.resumen.urgente} urgentes, ${r.resumen.atento} de atención, ${r.resumen.tranquilo} tranquilas`}>
                    <i className="b-urgente" style={{ flexGrow: r.resumen.urgente }} />
                    <i className="b-atento" style={{ flexGrow: r.resumen.atento }} />
                    <i className="b-tranquilo" style={{ flexGrow: r.resumen.tranquilo }} />
                  </span>
                  <span className="bitacora-total">{r.resumen.total} <small>puertas</small></span>
                  <Flecha />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
