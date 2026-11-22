// Pagina de inicio de Umbral.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Flecha, Marca, Nivel } from "../components/Basicos.jsx";
import Carrusel from "../components/Carrusel.jsx";
import Preguntas from "../components/Preguntas.jsx";
import Puertas from "../components/Puertas.jsx";
import { useSesion } from "../sesion.jsx";

// Lo que escupe una herramienta tecnica vs. lo que Umbral te dice.
const TRADUCCIONES = [
  { maquina: "tcp  0.0.0.0:3389  LISTENING  svchost.exe", nivel: "urgente", puerta: "3389",
    humano: "Cualquiera en tu red puede intentar manejar tu computadora a distancia.",
    hacer: "Apaga «Escritorio remoto» en Configuración. Son dos clics." },
  { maquina: "tcp  0.0.0.0:445  LISTENING  System", nivel: "urgente", puerta: "445",
    humano: "Tus carpetas compartidas están a la vista de toda la red del café.",
    hacer: "Cambia la red a «Pública» y apaga el uso compartido." },
  { maquina: "udp  0.0.0.0:57621  Spotify.exe", nivel: "tranquilo", puerta: "57621",
    humano: "Es Spotify buscando tu celular para que controles la música. Todo bien.",
    hacer: "Nada. Si cierras Spotify, la puerta se cierra sola." },
  { maquina: "tcp  0.0.0.0:4444  LISTENING  actualizador.exe", nivel: "urgente", puerta: "4444",
    humano: "Un programa en tu carpeta temporal abrió la puerta favorita de las herramientas de ataque.",
    hacer: "Ciérralo, pasa el antivirus completo y cambia tus contraseñas." },
];

const CASOS = [
  { n: "3389", nombre: "Escritorio remoto", nivel: "urgente",
    que: "Deja ver tu pantalla y mover tu mouse desde otra computadora.",
    pasa: "Es de las puertas más atacadas del planeta. Muchos secuestros de archivos empiezan con alguien adivinando la contraseña aquí." },
  { n: "445", nombre: "Carpetas compartidas", nivel: "urgente",
    que: "Por aquí Windows comparte archivos e impresoras con otros equipos.",
    pasa: "En 2017 el virus WannaCry entró por esta puerta a más de 200 mil computadoras en un fin de semana." },
  { n: "23", nombre: "Telnet", nivel: "urgente",
    que: "El abuelo del control remoto. Funciona, pero sin ningún candado.",
    pasa: "Tu contraseña cruza la red como una postal sin sobre: quien la vea pasar, la lee." },
  { n: "3306", nombre: "Base de datos MySQL", nivel: "atento",
    que: "Donde los sistemas guardan usuarios, ventas o calificaciones. Suele quedar encendida después de una práctica con XAMPP.",
    pasa: "Si quedó sin contraseña y abierta a la red, cualquiera puede leerla completa." },
  { n: "5900", nombre: "Pantalla compartida (VNC)", nivel: "urgente",
    que: "Otra forma de ver y controlar tu pantalla a distancia.",
    pasa: "Existen buscadores públicos que listan miles de pantallas abiertas. Sí, se pueden ver." },
  { n: "5353", nombre: "Descubrimiento en red", nivel: "tranquilo",
    que: "Así tu computadora encuentra la impresora o la tele sin que configures nada.",
    pasa: "Nada grave. La mayoría de las puertas abiertas son así: normales. Umbral te dice cuáles." },
];

function Traductor() {
  const [i, setI] = useState(0);
  const [pausa, setPausa] = useState(false);
  useEffect(() => {
    if (pausa || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setInterval(() => setI((v) => (v + 1) % TRADUCCIONES.length), 5200);
    return () => clearInterval(t);
  }, [pausa]);
  const t = TRADUCCIONES[i];
  return (
    <div className="traductor" onMouseEnter={() => setPausa(true)} onMouseLeave={() => setPausa(false)}>
      <p className="traductor-rotulo">Lo que dice la máquina</p>
      <p className="traductor-maquina" key={`m${i}`}>{t.maquina}</p>
      <p className="traductor-rotulo">Lo que dice Umbral</p>
      <div className="traductor-humano" key={`h${i}`}>
        <Nivel nivel={t.nivel} />
        <p className="traductor-frase">{t.humano}</p>
        <p className="traductor-hacer"><b>Qué hacer:</b> {t.hacer}</p>
      </div>
      <div className="traductor-puntos" role="tablist" aria-label="Ejemplos">
        {TRADUCCIONES.map((x, k) => (
          <button key={x.puerta} role="tab" aria-selected={k === i} aria-label={`Ejemplo puerta ${x.puerta}`} onClick={() => setI(k)} />
        ))}
      </div>
    </div>
  );
}

export default function Landing() {
  const { usuario } = useSesion();
  const destino = usuario ? "/panel" : "/registro";

  return (
    <div className="landing">
      <header className="tope">
        <Marca />
        <nav aria-label="Principal">
          <a href="#como">Cómo funciona</a>
          <a href="#puertas">Las puertas</a>
          <a href="#permiso">Tu permiso</a>
          <a href="#dudas">Dudas</a>
          {usuario ? <Link to="/panel" className="tope-entrar">Ir a mi panel</Link> : <Link to="/entrar" className="tope-entrar">Entrar</Link>}
        </nav>
      </header>

      <section className="hero">
        <Puertas />
        <div className="hero-velo" />
        <div className="hero-texto">
          <p className="antetitulo">Seguridad informática para quien nunca la estudió</p>
          <h1>Tu computadora tiene <em>65,535 puertas.</em> ¿Sabes cuáles dejaste abiertas?</h1>
          <p className="hero-bajada">
            Umbral las revisa con tu permiso y te explica cada una como te lo explicaría un amigo:
            qué es, qué puede pasar y cómo cerrarla. Sin tecnicismos.
          </p>
          <div className="hero-acciones">
            <Link to={destino} className="boton boton-lleno">Revisar mi computadora <Flecha /></Link>
            <a href="#puertas" className="boton boton-linea">Ver ejemplos</a>
          </div>
          <p className="hero-nota">Gratis. Funciona en Windows y Linux. No instala nada raro.</p>
        </div>
        <Traductor />
      </section>

      <section className="manifiesto" style={{ backgroundImage: "url(/fondos/ciudad.webp)" }}>
        <div className="ancho">
          <p className="manifiesto-frase">
            Nos hicieron creer que la seguridad era cosa de <s>genios</s>, de <s>hackers</s>, de <s>los que saben</s>.
          </p>
          <p className="manifiesto-remate">Es cosa de cualquiera que tenga una computadora. O sea, tuya.</p>
        </div>
      </section>

      <section className="como ancho" id="como">
        <h2>Tres pasos. El segundo lo decides tú.</h2>
        <Carrusel etiqueta="Cómo funciona Umbral" clase="carrusel-pasos">
          <article className="paso">
            <span className="paso-n">1</span>
            <h3>Abres tu cuenta</h3>
            <p>Nombre, correo y una contraseña. Te mandamos un código al correo para confirmar que eres tú. Nada más.</p>
          </article>
          <article className="paso">
            <span className="paso-n">2</span>
            <h3>Le das permiso al agente</h3>
            <p>Un programa pequeño te pregunta, en tu propia pantalla, si puede mirar tus puertos. Si dices que no, no hace nada. Si dices que sí, mira solo eso.</p>
          </article>
          <article className="paso">
            <span className="paso-n">3</span>
            <h3>Lees el resultado en español</h3>
            <p>Cada puerta abierta con tres datos: qué es, qué puede pasar y los pasos para cerrarla en tu sistema. Ordenadas de la más urgente a la más tranquila.</p>
          </article>
          <article className="paso">
            <span className="paso-n">+</span>
            <h3>Vuelves cuando quieras</h3>
            <p>Umbral compara cada revisión con la anterior y te avisa qué puerta se abrió desde la última vez. Ahí es donde se cachan las sorpresas.</p>
          </article>
        </Carrusel>
      </section>

      <section className="casos" id="puertas">
        <div className="ancho">
          <h2>Seis puertas que conviene conocer</h2>
          <p className="seccion-bajada">Usa las flechas. Cada una es un número que tal vez ya tienes abierto.</p>
        </div>
        <Carrusel etiqueta="Puertas comunes" clase="carrusel-casos">
          {CASOS.map((c) => (
            <article className={`caso caso-${c.nivel}`} key={c.n}>
              <p className="caso-n">{c.n}</p>
              <div className="caso-cuerpo">
                <Nivel nivel={c.nivel} />
                <h3>{c.nombre}</h3>
                <p>{c.que}</p>
                <p className="caso-pasa"><b>Qué puede pasar:</b> {c.pasa}</p>
              </div>
            </article>
          ))}
        </Carrusel>
      </section>

      <section className="permiso" id="permiso" style={{ "--foto": "url(/fondos/cerradura.webp)", backgroundImage: "var(--foto)" }}>
        <div className="permiso-rejilla">
          <div>
            <h2>Miramos por la cerradura, no dentro de la casa.</h2>
            <p className="seccion-bajada">
              Antes de revisar, Umbral te pide permiso y te enseña exactamente qué va a enviar.
              Puedes verlo sin enviar nada con un solo comando.
            </p>
          </div>
          <div className="permiso-listas">
            <div>
              <h3>Lo que sí lee</h3>
              <ul>
                <li>Qué puertos están abiertos</li>
                <li>Qué programa abrió cada uno</li>
                <li>Si tu cortafuegos está encendido</li>
                <li>Si usas Windows o Linux</li>
              </ul>
            </div>
            <div className="permiso-no">
              <h3>Lo que nunca lee</h3>
              <ul>
                <li>Tus archivos y fotos</li>
                <li>Tus contraseñas</li>
                <li>Tu historial ni lo que escribes</li>
                <li>Lo que viaja por tu red</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="reglas-casa ancho">
        <h2>Predicamos con el ejemplo</h2>
        <p className="seccion-bajada">Un sitio que habla de seguridad tiene que cuidarse primero. Así cuidamos tu cuenta:</p>
        <dl>
          <div><dt>Tu contraseña no se guarda</dt><dd>Se guarda una huella hecha con Argon2id. Ni nosotros podemos leerla.</dd></div>
          <div><dt>Cinco intentos y pausa</dt><dd>Si alguien falla tu contraseña cinco veces, la cuenta se bloquea quince minutos.</dd></div>
          <div><dt>Códigos de un solo uso</dt><dd>El código de tu correo vence en quince minutos y no sirve dos veces.</dd></div>
          <div><dt>Sesión que no se puede robar con un script</dt><dd>Viaja en una cookie que el navegador no deja leer a ninguna página.</dd></div>
          <div><dt>Tú mandas sobre tus datos</dt><dd>Desconectas un equipo o borras tu cuenta completa cuando quieras, sin pedirle permiso a nadie.</dd></div>
        </dl>
      </section>

      <Preguntas />

      <section className="cierre" style={{ "--foto": "url(/fondos/pasillo.webp)", backgroundImage: "var(--foto)" }}>
        <div className="ancho">
          <h2>Dale una vuelta a tu casa antes de dormir.</h2>
          <Link to={destino} className="boton boton-lleno">Crear mi cuenta <Flecha /></Link>
        </div>
      </section>

      <footer className="pie ancho">
        <Marca />
        <p>Proyecto de Seguridad Informática · Universidad Politécnica de Chiapas · Carlos Andrés Mazariegos Laguna</p>
        <Link to="/privacidad">Aviso de privacidad</Link>
      </footer>
    </div>
  );
}
