// Inicio del panel: como esta tu equipo hoy y que sigue.
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, haceCuanto, plural, SISTEMAS } from "../../api.js";
import { Aviso, Boton, Flecha, Nivel } from "../../components/Basicos.jsx";
import Carrusel from "../../components/Carrusel.jsx";
import { useSesion } from "../../sesion.jsx";

const GUIA = [
  { t: "Tu computadora es una casa", p: "Cada programa que espera conexiones abre una puerta numerada: un puerto. Hay 65,535. La mayoría están cerradas; algunas necesitan estar abiertas." },
  { t: "No toda puerta abierta es mala", p: "Spotify abre una para hablar con tu celular. Tu impresora, otra. El problema son las que quedaron abiertas sin que lo sepas." },
  { t: "Umbral las cuenta por ti", p: "El agente mira cuáles están abiertas y qué programa abrió cada una. No entra a ninguna: solo anota el número y el dueño." },
  { t: "Y te dice qué hacer", p: "Tres niveles: Tranquilo, Ojo aquí y Atiéndelo ya. Cada una con pasos para tu sistema. Tú decides cuáles cierras." },
];

function saludo() {
  const h = new Date().getHours();
  return h < 12 ? "Buenos días" : h < 19 ? "Buenas tardes" : "Buenas noches";
}

export default function Inicio() {
  const ir = useNavigate();
  const { usuario, servidor } = useSesion();
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");
  const [ocupado, setOcupado] = useState("");
  const esCelular = /Android|iPhone|iPad/i.test(navigator.userAgent);

  const cargar = useCallback(() => api("/panel").then(setDatos).catch((e) => setError(e.message)), []);
  useEffect(() => { cargar(); }, [cargar]);

  const revisar = async (tipo) => {
    setOcupado(tipo); setError("");
    try {
      const r = await api(`/revisiones/${tipo}`, { metodo: "POST" });
      ir(`/panel/revision/${r.revision_id}`);
    } catch (e) {
      setError(e.message);
      setOcupado("");
    }
  };

  if (!datos) return <div className="cargando">{error || "Cargando tu panel…"}</div>;
  const nombre = usuario.nombre.split(" ")[0];
  const urgentes = datos.pendientes.length;

  // ---------- primera vez ----------
  if (datos.revisiones === 0) {
    return (
      <div className="inicio">
        <header className="cabeza cabeza-imagen" style={{ backgroundImage: "url(/fondos/pasillo.webp)" }}>
          <p className="antetitulo">{saludo()}, {nombre}</p>
          <h1>Todavía no sabemos cuántas puertas tienes abiertas. Vamos a contarlas.</h1>
        </header>
        <Aviso>{error}</Aviso>

        <section className="primeros">
          <div className="primero primero-fuerte">
            <h2>Conecta tu computadora</h2>
            <p>Descargas el agente, le das permiso y en un minuto tienes tu primera revisión. Funciona en Windows y Linux.</p>
            <Link to="/panel/equipos?conectar=1" className="boton boton-lleno">Conectar un equipo <Flecha /></Link>
          </div>
          {servidor.revision_directa && !esCelular && (
            <div className="primero">
              <h2>Revisar este equipo ahora</h2>
              <p>Umbral está corriendo en esta misma computadora, así que puede revisarla directo, sin agente.</p>
              <Boton variante="linea" cargando={ocupado === "directa"} onClick={() => revisar("directa")}>Revisar ahora</Boton>
            </div>
          )}
          <div className="primero">
            <h2>{esCelular ? "Estás en el celular" : "Solo quiero ver cómo es"}</h2>
            <p>{esCelular
              ? "Los celulares no dejan revisar sus puertos, pero desde aquí puedes leer las revisiones de tus computadoras. Mira un ejemplo:"
              : "Abre una revisión de ejemplo de una laptop descuidada, con todo y sorpresa."}</p>
            <Boton variante="linea" cargando={ocupado === "ejemplo"} onClick={() => revisar("ejemplo")}>Ver un ejemplo</Boton>
          </div>
        </section>

        <section className="guia">
          <h2>Antes de empezar: la idea en cuatro pantallas</h2>
          <Carrusel etiqueta="Guía rápida" clase="carrusel-guia">
            {GUIA.map((g, i) => (
              <article className="guia-hoja" key={g.t}>
                <span className="guia-n">{i + 1}</span>
                <h3>{g.t}</h3>
                <p>{g.p}</p>
              </article>
            ))}
          </Carrusel>
        </section>
      </div>
    );
  }

  // ---------- con revisiones ----------
  const total = datos.recientes.reduce((s, r) => s + r.resumen.total, 0);
  return (
    <div className="inicio">
      <header className={`cabeza ${urgentes ? "cabeza-alerta" : "cabeza-calma"}`}>
        <p className="antetitulo">{saludo()}, {nombre}</p>
        <h1>
          {urgentes
            ? <>De {plural(total, "puerta abierta", "puertas abiertas")}, <em>{urgentes === 1 ? "una necesita" : `${urgentes} necesitan`}</em> que la{urgentes === 1 ? "" : "s"} atiendas hoy.</>
            : <>Tienes {plural(total, "puerta abierta", "puertas abiertas")} y <em>ninguna urgente.</em> Así se ve una casa cuidada.</>}
        </h1>
        <div className="cabeza-acciones">
          {servidor.revision_directa && !esCelular && (
            <Boton cargando={ocupado === "directa"} onClick={() => revisar("directa")}>Revisar este equipo ahora</Boton>
          )}
          <Link to="/panel/equipos" className="boton boton-linea">Mis equipos</Link>
        </div>
      </header>
      <Aviso>{error}</Aviso>

      {urgentes > 0 && (
        <section className="bloque">
          <h2>Por atender</h2>
          <ul className="pendientes">
            {datos.pendientes.map((h) => (
              <li key={h.id}>
                <Link to={`/panel/revision/${h.revision_id}?abrir=${h.id}`}>
                  <span className="puerta-n">{h.puerto}</span>
                  <span className="puerta-titulo"><b>{h.titulo}</b><small>{h.nombre_equipo} · {h.riesgo.split(". ")[0].replace(/\.$/, "")}.</small></span>
                  <Flecha />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="bloque">
        <h2>Última revisión de cada equipo</h2>
        <ul className="recientes">
          {datos.recientes.map((r) => (
            <li key={r.id}>
              <Link to={`/panel/revision/${r.id}`}>
                <span className="reciente-nombre"><b>{r.nombre_equipo || "Equipo"}</b><small>{SISTEMAS[r.sistema] || r.sistema} · {haceCuanto(r.creado)}</small></span>
                <span className="reciente-cuenta">
                  {r.resumen.urgente > 0 && <span className="conteo conteo-urgente">{r.resumen.urgente} <Nivel nivel="urgente" corto /></span>}
                  {r.resumen.atento > 0 && <span className="conteo conteo-atento">{r.resumen.atento} <Nivel nivel="atento" corto /></span>}
                  <span className="conteo conteo-tranquilo">{r.resumen.tranquilo} <Nivel nivel="tranquilo" corto /></span>
                </span>
                <Flecha />
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
