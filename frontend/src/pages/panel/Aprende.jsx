// Aprende: los conceptos basicos en tarjetas y un buscador de puertos.
import { useState } from "react";
import { api } from "../../api.js";
import { Aviso, Boton, Nivel } from "../../components/Basicos.jsx";
import Carrusel from "../../components/Carrusel.jsx";

const IDEAS = [
  { palabra: "Puerto", frase: "Una puerta numerada de tu computadora.",
    texto: "Tu equipo tiene 65,535. Cada programa que quiere recibir visitas de la red abre una y se queda escuchando ahí. El 443 es el de las páginas con candado; el 3389, el del escritorio remoto." },
  { palabra: "Cortafuegos", frase: "El portero del edificio.",
    texto: "Decide qué visitas pueden tocar tus puertas y cuáles se regresan. Aunque una puerta esté abierta, con el portero en su lugar un extraño no llega hasta ella. Por eso lo primero es tenerlo encendido." },
  { palabra: "Dirección IP", frase: "El domicilio de tu equipo en la red.",
    texto: "127.0.0.1 es «mi propia casa»: una puerta que escucha ahí solo sirve para adentro. 0.0.0.0 significa «todas mis entradas»: esa puerta da a la calle." },
  { palabra: "Proceso", frase: "Un programa mientras está corriendo.",
    texto: "Detrás de cada puerta abierta hay un proceso que la abrió. Saber cuál es responde la pregunta importante: ¿la abrí yo o se abrió sola?" },
  { palabra: "Malware", frase: "Un programa que trabaja para alguien más.",
    texto: "Virus, troyanos, secuestradores de archivos. Muchos abren una puerta trasera para recibir órdenes. Una puerta rara, abierta por un programa en una carpeta temporal, es la pista clásica." },
  { palabra: "Phishing", frase: "El engaño para que tú mismo abras.",
    texto: "Un correo o mensaje que se hace pasar por tu banco o tu escuela. No rompe ninguna puerta: te convence de entregar la llave. Desconfía de la prisa y revisa siempre la dirección." },
  { palabra: "Contraseña fuerte", frase: "Larga gana a rara.",
    texto: "«Mi-perro-odia-los-lunes-2026» es más difícil de adivinar que «P@55w0rd!» y más fácil de recordar. Y una distinta para cada sitio: si roban una, no caen todas." },
  { palabra: "Actualizar", frase: "Cambiar la cerradura cuando sale una mejor.",
    texto: "Las actualizaciones tapan agujeros que ya son públicos. El virus WannaCry de 2017 usó una falla que tenía parche desde dos meses antes: cayó quien no había actualizado." },
];

export default function Aprende() {
  const [numero, setNumero] = useState("");
  const [ficha, setFicha] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const buscar = async (e) => {
    e.preventDefault();
    setError(""); setFicha(null);
    const n = Number(numero);
    if (!numero || n < 1 || n > 65535) return setError("Escribe un número del 1 al 65535.");
    setCargando(true);
    try {
      setFicha(await api(`/puertos/${n}`));
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="aprende">
      <header className="cabeza cabeza-imagen" style={{ backgroundImage: "url(/fondos/cerradura.webp)" }}>
        <p className="antetitulo">Aprende</p>
        <h1>Ocho palabras y ya entiendes de qué hablan los que «saben».</h1>
      </header>

      <Carrusel etiqueta="Conceptos básicos" clase="carrusel-ideas">
        {IDEAS.map((i, k) => (
          <article className="idea" key={i.palabra}>
            <span className="idea-n">{String(k + 1).padStart(2, "0")}</span>
            <h2>{i.palabra}</h2>
            <p className="idea-frase">{i.frase}</p>
            <p>{i.texto}</p>
          </article>
        ))}
      </Carrusel>

      <section className="buscador">
        <h2>¿Viste un número y no sabes qué es?</h2>
        <form onSubmit={buscar} noValidate>
          <label htmlFor="puerto">Número de puerto</label>
          <div className="buscador-fila">
            <input id="puerto" inputMode="numeric" maxLength={5} placeholder="3389" value={numero}
              onChange={(e) => setNumero(e.target.value.replace(/\D/g, "").slice(0, 5))} />
            <Boton cargando={cargando} type="submit">Explícamelo</Boton>
          </div>
        </form>
        <Aviso>{error}</Aviso>
        {ficha && (
          <div className={`ficha ficha-${ficha.nivel}`} role="status">
            <p className="ficha-n">{ficha.puerto}</p>
            <div>
              {ficha.conocido && <Nivel nivel={ficha.nivel} />}
              <h3>{ficha.titulo}{ficha.conocido ? ` · ${ficha.servicio}` : ""}</h3>
              <p>{ficha.explicacion}</p>
              <p><b>Qué puede pasar:</b> {ficha.riesgo}</p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
