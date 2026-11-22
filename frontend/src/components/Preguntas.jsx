// Preguntas frecuentes de la pagina de inicio.
// Se usa <details>, que el navegador ya sabe abrir y cerrar solo.
const PREGUNTAS = [
  { p: "¿Necesito saber de computación para usarlo?",
    r: "No. Si sabes instalar un programa y copiar un comando, puedes. Umbral te va diciendo qué hacer en cada paso." },
  { p: "¿Umbral cierra los puertos por mí?",
    r: "No. Umbral no cambia nada en tu equipo: te explica qué encontró y te da los pasos. La decisión de cerrar es tuya." },
  { p: "¿Tener un puerto abierto significa que me hackearon?",
    r: "Casi nunca. La mayoría de los puertos abiertos son normales. Lo importante es saber cuáles tienes y por qué." },
  { p: "¿Sirve en el celular?",
    r: "Desde el celular puedes leer las revisiones de tus computadoras. El celular no deja que una página revise sus puertos." },
  { p: "¿Cada cuánto conviene revisar?",
    r: "Una vez por semana está bien, y siempre después de instalar un programa nuevo o de conectarte a una red que no es tuya." },
  { p: "¿Qué pasa con mis datos si borro la cuenta?",
    r: "Se borra todo en ese momento: tu cuenta, tus equipos y tus revisiones. No se guarda copia." },
];

export default function Preguntas() {
  return (
    <section className="dudas ancho" id="dudas">
      <h2>Preguntas que nos hacen seguido</h2>
      {PREGUNTAS.map((d) => (
        <details key={d.p}>
          <summary>{d.p}</summary>
          <p>{d.r}</p>
        </details>
      ))}
    </section>
  );
}
