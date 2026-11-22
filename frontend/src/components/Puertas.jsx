// El fondo vivo de Umbral: una fachada de puertas numeradas.
// Cada puerta es un puerto. Casi todas estan cerradas; algunas se abren y
// dejan salir luz. Las que brillan en naranja son las que no deberian estarlo.
import { useEffect, useRef } from "react";

const CONOCIDOS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 1433, 1900, 3000, 3306, 3389,
  4444, 5000, 5353, 5432, 5900, 6379, 7680, 8000, 8080, 8443, 9050, 27017, 31337, 49152, 51820, 57621];
const PELIGRO = new Set([21, 23, 445, 3389, 4444, 5900, 31337]);

export default function Puertas() {
  const lienzo = useRef(null);

  useEffect(() => {
    const canvas = lienzo.current;
    const ctx = canvas.getContext("2d");
    const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let puertas = [], ancho = 0, alto = 0, cuadro = 0, ultimo = 0, raton = null;

    const armar = () => {
      const r = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      ancho = r.width; alto = r.height;
      canvas.width = ancho * dpr; canvas.height = alto * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const pw = ancho < 700 ? 34 : 46, ph = pw * 2.05, gx = pw * 0.95, gy = ph * 0.62;
      const cols = Math.ceil(ancho / (pw + gx)) + 1, filas = Math.ceil(alto / (ph + gy)) + 1;
      puertas = [];
      for (let f = 0; f < filas; f++) {
        for (let c = 0; c < cols; c++) {
          const n = CONOCIDOS[(f * 7 + c * 3 + f * c) % CONOCIDOS.length];
          const abierta = Math.random() < 0.13;
          puertas.push({ x: c * (pw + gx) + (f % 2 ? pw * 0.9 : 0) - 10, y: f * (ph + gy) + 26, w: pw, h: ph, n,
            a: abierta ? 0.5 + Math.random() * 0.5 : 0, meta: abierta ? 1 : 0, mala: PELIGRO.has(n) });
        }
      }
    };

    const pintar = () => {
      ctx.clearRect(0, 0, ancho, alto);
      ctx.font = "10px Arial, Arimo, sans-serif";
      for (const p of puertas) {
        p.a += (p.meta - p.a) * 0.045;
        const color = p.mala ? "255,91,46" : "200,240,60";
        if (p.a > 0.02) {
          // luz que se derrama al piso
          const g = ctx.createLinearGradient(0, p.y + p.h, 0, p.y + p.h + p.h * 0.9);
          g.addColorStop(0, `rgba(${color},${0.22 * p.a})`);
          g.addColorStop(1, `rgba(${color},0)`);
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y + p.h); ctx.lineTo(p.x + p.w, p.y + p.h);
          ctx.lineTo(p.x + p.w * (1 + 0.9 * p.a), p.y + p.h * 1.9); ctx.lineTo(p.x - p.w * 0.25, p.y + p.h * 1.9);
          ctx.fill();
          // el hueco iluminado
          ctx.fillStyle = `rgba(${color},${0.16 + 0.74 * p.a})`;
          ctx.fillRect(p.x, p.y, p.w, p.h);
        }
        // la hoja de la puerta: se angosta al abrirse
        const hoja = p.w * (1 - 0.78 * p.a), sesgo = p.h * 0.07 * p.a;
        ctx.fillStyle = p.a > 0.02 ? "#12110e" : "rgba(241,234,219,0.022)";
        ctx.beginPath();
        ctx.moveTo(p.x, p.y); ctx.lineTo(p.x + hoja, p.y + sesgo);
        ctx.lineTo(p.x + hoja, p.y + p.h - sesgo); ctx.lineTo(p.x, p.y + p.h);
        ctx.fill();
        ctx.strokeStyle = `rgba(241,234,219,${0.13 + 0.1 * p.a})`;
        ctx.lineWidth = 1;
        ctx.strokeRect(p.x + 0.5, p.y + 0.5, p.w, p.h);
        ctx.fillStyle = p.a > 0.3 ? `rgba(${color},0.95)` : "rgba(241,234,219,0.26)";
        ctx.fillText(String(p.n), p.x, p.y - 7);
      }
    };

    const ciclo = (t) => {
      cuadro = requestAnimationFrame(ciclo);
      if (t - ultimo > 900) {
        ultimo = t;
        const p = puertas[Math.floor(Math.random() * puertas.length)];
        if (p) p.meta = p.meta ? 0 : Math.random() < 0.55 ? 1 : 0;
      }
      if (raton) {
        for (const p of puertas) {
          if (raton.x > p.x && raton.x < p.x + p.w && raton.y > p.y && raton.y < p.y + p.h) p.meta = 1;
        }
      }
      pintar();
    };

    const mover = (e) => {
      const r = canvas.getBoundingClientRect();
      raton = { x: e.clientX - r.left, y: e.clientY - r.top };
    };

    armar();
    if (quieto) { puertas.forEach((p) => { p.a = p.meta; }); pintar(); }
    else cuadro = requestAnimationFrame(ciclo);
    window.addEventListener("resize", armar);
    window.addEventListener("pointermove", mover, { passive: true });
    return () => {
      cancelAnimationFrame(cuadro);
      window.removeEventListener("resize", armar);
      window.removeEventListener("pointermove", mover);
    };
  }, []);

  return <canvas ref={lienzo} className="puertas" aria-hidden="true" />;
}
