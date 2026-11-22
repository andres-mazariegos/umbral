// Administracion: solo la ven las cuentas listadas en UMBRAL_ADMINS (lo decide el servidor).
// Sirve para cuidar el sitio: cuantas cuentas hay, que puertos salen urgentes con mas
// frecuencia, quien esta bloqueado y que alertas de seguridad hubo.
import { useCallback, useEffect, useState } from "react";
import { api, fecha, haceCuanto, SISTEMAS } from "../../api.js";
import { Aviso } from "../../components/Basicos.jsx";

function Cifra({ valor, texto, tono }) {
  return (
    <div className={`cifra ${tono ? `cifra-${tono}` : ""}`}>
      <strong>{valor}</strong>
      <span>{texto}</span>
    </div>
  );
}

export default function Admin() {
  const [resumen, setResumen] = useState(null);
  const [cuentas, setCuentas] = useState([]);
  const [eventos, setEventos] = useState([]);
  const [soloAlertas, setSoloAlertas] = useState(false);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  const cargar = useCallback(async () => {
    try {
      const [r, c, b] = await Promise.all([
        api("/admin/resumen"), api("/admin/cuentas"), api(`/admin/bitacora?solo_alertas=${soloAlertas}`),
      ]);
      setResumen(r); setCuentas(c.cuentas); setEventos(b.eventos); setError("");
    } catch (e) {
      setError(e.message);
    }
  }, [soloAlertas]);

  useEffect(() => { cargar(); }, [cargar]);

  const desbloquear = async (cuenta) => {
    if (!window.confirm(`¿Desbloquear la cuenta de ${cuenta.nombre}? Podrá volver a intentar entrar de inmediato.`)) return;
    try {
      setAviso((await api(`/admin/cuentas/${cuenta.id}/desbloquear`, { metodo: "POST" })).mensaje);
      cargar();
    } catch (e) {
      setError(e.message);
    }
  };

  if (!resumen) return <div className="cargando">{error || "Cargando administración…"}</div>;
  const totalHallazgos = resumen.niveles.urgente + resumen.niveles.atento + resumen.niveles.tranquilo;

  return (
    <div className="admin">
      <header className="cabeza">
        <p className="antetitulo">Administración</p>
        <h1>Cómo va <em>Umbral</em> en general.</h1>
        <p className="ajuste-nota">Los correos se muestran tapados a propósito: para cuidar el sitio no hace falta leer los datos de nadie.</p>
      </header>
      <Aviso>{error}</Aviso>
      <Aviso tipo="bien">{aviso}</Aviso>

      <section className="cifras" aria-label="Cifras generales">
        <Cifra valor={resumen.cuentas} texto={`cuentas (${resumen.verificadas} con correo confirmado)`} />
        <Cifra valor={resumen.equipos} texto="equipos conectados" />
        <Cifra valor={resumen.revisiones} texto={`revisiones (${resumen.revisiones_24h} en 24 h)`} />
        <Cifra valor={resumen.bloqueadas} texto="cuentas en pausa por intentos" tono={resumen.bloqueadas ? "brasa" : ""} />
        <Cifra valor={resumen.alertas_24h} texto="alertas de seguridad en 24 h" tono={resumen.alertas_24h ? "lila" : ""} />
      </section>

      <section className="ajuste">
        <h2>Qué tan expuestos están los equipos</h2>
        <p className="ajuste-nota">Todas las puertas encontradas en todas las revisiones: {totalHallazgos}.</p>
        <div className="bitacora-barras barras-grandes" aria-label={`${resumen.niveles.urgente} urgentes, ${resumen.niveles.atento} de atención, ${resumen.niveles.tranquilo} tranquilas`}>
          <i className="b-urgente" style={{ flexGrow: resumen.niveles.urgente }} />
          <i className="b-atento" style={{ flexGrow: resumen.niveles.atento }} />
          <i className="b-tranquilo" style={{ flexGrow: resumen.niveles.tranquilo }} />
        </div>
        <p className="leyenda">
          <span className="punto p-urgente" /> Urgentes {resumen.niveles.urgente}
          <span className="punto p-atento" /> Ojo aquí {resumen.niveles.atento}
          <span className="punto p-tranquilo" /> Tranquilas {resumen.niveles.tranquilo}
        </p>
        {resumen.puertos_urgentes.length > 0 && (
          <p>Los puertos urgentes que más se repiten: {resumen.puertos_urgentes.map((p) => `${p.puerto} (${p.veces})`).join(", ")}.</p>
        )}
        {Object.keys(resumen.sistemas).length > 0 && (
          <p>Equipos por sistema: {Object.entries(resumen.sistemas).map(([s, n]) => `${SISTEMAS[s] || s} ${n}`).join(", ")}.</p>
        )}
      </section>

      <section className="ajuste">
        <h2>Cuentas</h2>
        <div className="tabla-envoltura">
          <table className="tabla">
            <thead>
              <tr><th>Nombre</th><th>Correo</th><th>Estado</th><th>Equipos</th><th>Revisiones</th><th>Último acceso</th><th /></tr>
            </thead>
            <tbody>
              {cuentas.map((c) => (
                <tr key={c.id}>
                  <td>{c.nombre}{c.admin && <small className="etiqueta">admin</small>}</td>
                  <td className="mono">{c.correo}</td>
                  <td>{c.bloqueado ? <span className="t-brasa">En pausa</span> : c.verificado ? "Activa" : <span className="t-niebla">Sin confirmar</span>}</td>
                  <td>{c.equipos}</td>
                  <td>{c.revisiones}</td>
                  <td>{haceCuanto(c.ultimo_acceso)}</td>
                  <td>{c.bloqueado && <button type="button" className="enlace" onClick={() => desbloquear(c)}>Desbloquear</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="ajuste">
        <h2>Bitácora de seguridad del sitio</h2>
        <label className="casilla">
          <input type="checkbox" checked={soloAlertas} onChange={(e) => setSoloAlertas(e.target.checked)} />
          <span>Ver solo alertas (contraseñas incorrectas, códigos fallidos, bloqueos)</span>
        </label>
        <ul className="actividad">
          {eventos.map((ev) => (
            <li key={ev.id} className={ev.alerta ? "actividad-alerta" : ""}>
              <span>{ev.texto} <small className="mono">{ev.cuenta}</small></span>
              <small>{fecha(ev.fecha)} · IP {ev.ip || "—"}</small>
            </li>
          ))}
          {!eventos.length && <li><span>Sin eventos.</span></li>}
        </ul>
      </section>
    </div>
  );
}
