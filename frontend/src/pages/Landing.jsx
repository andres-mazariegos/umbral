// Pagina de inicio (landing) de Umbral.
// Explico que hace la app y muestro un ejemplo de una revision.
import { Link } from "react-router-dom";
import LluviaCodigo from "../components/LluviaCodigo.jsx";

function Landing() {
  return (
    <>
      <LluviaCodigo />

      <div className="wrap">
        {/* barra de arriba */}
        <header className="top">
          <div className="brand">
            Umbr<span className="b-green">a</span>l<span className="cur"></span>
          </div>
          <nav className="nav">
            <a className="q" href="#traduccion">Qué hace</a>
            <a className="q" href="#niveles">Niveles</a>
            <Link className="enter" to="/login">Entrar</Link>
          </nav>
        </header>

        {/* hero */}
        <section className="hero">
          <div>
            <p className="tag">Consola de seguridad para tu equipo</p>
            <h1 className="h1">
              Revisa la seguridad de tu computadora y entiéndela sin ser experto.
            </h1>
            <p className="lead">
              Umbral analiza los puertos abiertos de tu equipo y te explica, en
              palabras simples, qué encontró, por qué puede ser un riesgo y qué
              puedes hacer al respecto.
            </p>
            <div className="cta-row">
              <Link className="btn btn-primary" to="/login">Revisar mi equipo</Link>
              <a className="btn btn-ghost" href="#traduccion">Ver cómo funciona</a>
            </div>
          </div>

          {/* consola de ejemplo */}
          <div className="console" aria-hidden="true">
            <div className="console-bar">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="console-title">umbral — revisión en curso</span>
            </div>
            <div className="console-body">
              <div className="c-line">
                <span className="c-prompt">umbral@local:~$</span> revisar 127.0.0.1
              </div>
              <div className="c-line c-dim">analizando puertos abiertos...</div>
              <div className="c-line">&nbsp;</div>
              <div className="c-line">
                <span className="c-head">PUERTO     SERVICIO        ESTADO</span>
              </div>
              <div className="c-line">22/tcp     ssh             <span className="c-ok">sin problemas</span></div>
              <div className="c-line">80/tcp     http            <span className="c-warn">requiere revisión</span></div>
              <div className="c-line">445/tcp    microsoft-ds    <span className="c-bad">atención importante</span></div>
              <div className="c-line">&nbsp;</div>
              <div className="c-line c-dim">3 hallazgos · traduciendo a lenguaje claro…</div>
            </div>
          </div>
        </section>

        {/* de lo tecnico a lo humano */}
        <section className="section" id="traduccion">
          <p className="sec-h">De lo técnico a algo que entiendes</p>
          <div className="translate">
            <div className="t-machine">
              <p className="tm-label">lo que ve la máquina</p>
              <pre>{`PUERTO    445/tcp
ESTADO    open
SERVICIO  microsoft-ds
PROTOCOLO SMB`}</pre>
            </div>
            <div className="t-arrow" aria-hidden="true">
              <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#1C8F47" strokeWidth="1.6">
                <path d="M4 12h15M13 6l6 6-6 6" />
              </svg>
            </div>
            <div className="t-human">
              <span className="level bad">
                <span className="bullet-dot"></span>Atención importante
              </span>
              <h3>Compartir archivos de Windows está abierto</h3>
              <p>
                Es el canal que Windows usa para compartir archivos e impresoras
                en una red. Si te conectas a una red pública (una cafetería, la
                escuela), alguien en esa misma red podría intentar entrar a tu
                equipo por aquí.
              </p>
              <p className="rec">
                <b>Qué hacer:</b> desactiva el uso compartido de archivos cuando
                estés en redes públicas y mantén tu Windows actualizado.
              </p>
            </div>
          </div>

          {/* niveles de atencion */}
          <div className="levels" id="niveles">
            <div className="lv ok">
              <span className="bulb"></span>
              <span className="lv-name">Sin problemas</span>
              <p>Lo que encontramos es normal y no requiere que hagas nada.</p>
            </div>
            <div className="lv rev">
              <span className="bulb"></span>
              <span className="lv-name">Requiere revisión</span>
              <p>Conviene que lo mires con calma; no es urgente, pero sí recomendable.</p>
            </div>
            <div className="lv imp">
              <span className="bulb"></span>
              <span className="lv-name">Atención importante</span>
              <p>Vale la pena actuar pronto. Te decimos exactamente cómo.</p>
            </div>
          </div>
        </section>

        <footer className="foot">
          <span className="fb">Umbral · <b>por Andrés Mazariegos</b></span>
          <span className="sig">Seguridad Informática · 7º cuatrimestre</span>
        </footer>
      </div>
    </>
  );
}

export default Landing;
