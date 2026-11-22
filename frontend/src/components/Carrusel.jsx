// Carrusel con flechas, contador y deslizamiento con el dedo.
// Usa el desplazamiento nativo del navegador (scroll-snap): funciona igual
// con mouse, teclado y pantalla tactil.
import { Children, useCallback, useEffect, useRef, useState } from "react";
import { Flecha } from "./Basicos.jsx";

export default function Carrusel({ children, etiqueta, clase = "" }) {
  const pista = useRef(null);
  const [actual, setActual] = useState(0);
  const total = Children.count(children);

  const ir = useCallback((i) => {
    const el = pista.current;
    if (!el) return;
    const destino = Math.max(0, Math.min(total - 1, i));
    const hijo = el.children[destino];
    el.scrollTo({ left: hijo.offsetLeft - el.offsetLeft, behavior: "smooth" });
  }, [total]);

  useEffect(() => {
    const el = pista.current;
    if (!el) return;
    const alMover = () => {
      const centro = el.scrollLeft + el.clientWidth / 2;
      let cerca = 0, mejor = Infinity;
      [...el.children].forEach((h, i) => {
        const d = Math.abs(h.offsetLeft - el.offsetLeft + h.clientWidth / 2 - centro);
        if (d < mejor) { mejor = d; cerca = i; }
      });
      setActual(cerca);
    };
    el.addEventListener("scroll", alMover, { passive: true });
    return () => el.removeEventListener("scroll", alMover);
  }, []);

  const tecla = (e) => {
    if (e.key === "ArrowRight") { e.preventDefault(); ir(actual + 1); }
    if (e.key === "ArrowLeft") { e.preventDefault(); ir(actual - 1); }
  };

  return (
    <div className={`carrusel ${clase}`} role="group" aria-roledescription="carrusel" aria-label={etiqueta}>
      <div className="carrusel-pista" ref={pista} tabIndex={0} onKeyDown={tecla}>
        {Children.map(children, (hijo, i) => (
          <div className="carrusel-hoja" role="group" aria-roledescription="diapositiva" aria-label={`${i + 1} de ${total}`}>{hijo}</div>
        ))}
      </div>
      <div className="carrusel-mando">
        <button type="button" onClick={() => ir(actual - 1)} disabled={actual === 0} aria-label="Anterior"><Flecha dir="izq" /></button>
        <span className="carrusel-cuenta" aria-live="polite">
          <b>{String(actual + 1).padStart(2, "0")}</b> / {String(total).padStart(2, "0")}
        </span>
        <button type="button" onClick={() => ir(actual + 1)} disabled={actual === total - 1} aria-label="Siguiente"><Flecha /></button>
      </div>
    </div>
  );
}
