// Lluvia de codigo estilo Matrix para el fondo.
// La uso como "motor" visual de Umbral: parece que el sistema esta escaneando.
// Detalle personal: cada tanto caen las palabras UMBRAL y mis iniciales AML.
import { useEffect, useRef } from "react";

function LluviaCodigo() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const glifos = "01<>/{}[]=+*#$%&ﾊﾐﾋｰｳｼﾅﾉﾎｱﾃﾂﾘ".split("");
    const palabras = ["UMBRAL", "AML"];
    const tam = 15;
    let cols, gotas, especial, animId;

    function medir() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      cols = Math.floor(canvas.width / tam);
      gotas = new Array(cols).fill(0).map(() => Math.random() * -50);
      especial = new Array(cols).fill(null);
    }
    medir();
    window.addEventListener("resize", medir);

    function dibujar() {
      ctx.fillStyle = "rgba(10,14,10,0.09)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = tam + "px JetBrains Mono, monospace";

      for (let i = 0; i < cols; i++) {
        let letra;
        let resalta = false;

        if (especial[i] && especial[i].length) {
          letra = especial[i].shift();
          resalta = true;
          if (!especial[i].length) especial[i] = null;
        } else if (Math.random() < 0.0012) {
          // de vez en cuando empieza a caer una palabra escondida
          const palabra = palabras[Math.floor(Math.random() * palabras.length)];
          especial[i] = palabra.split("");
          letra = especial[i].shift();
          resalta = true;
        } else {
          letra = glifos[Math.floor(Math.random() * glifos.length)];
          resalta = Math.random() < 0.06;
        }

        ctx.fillStyle = resalta ? "#B9FFD0" : "#2BD163";
        ctx.fillText(letra, i * tam, gotas[i] * tam);

        if (gotas[i] * tam > canvas.height && Math.random() > 0.975) gotas[i] = 0;
        gotas[i]++;
      }
    }

    if (reduce) {
      dibujar();
    } else {
      let ultimo = 0;
      const loop = (t) => {
        if (t - ultimo > 55) {
          dibujar();
          ultimo = t;
        }
        animId = requestAnimationFrame(loop);
      };
      animId = requestAnimationFrame(loop);
    }

    return () => {
      window.removeEventListener("resize", medir);
      if (animId) cancelAnimationFrame(animId);
    };
  }, []);

  return <canvas id="rain" ref={canvasRef} />;
}

export default LluviaCodigo;
