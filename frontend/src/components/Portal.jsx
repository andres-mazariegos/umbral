// Marco de las pantallas de cuenta: imagen a un lado, formulario al otro.
import { Marca } from "./Basicos.jsx";
import Volver from "./Volver.jsx";

export default function Portal({ titulo, bajada, frase, imagen = "pasillo", volver = "/", children }) {
  return (
    <div className="portal">
      <aside className="portal-imagen" style={{ backgroundImage: `url(/fondos/${imagen}.webp)` }}>
        <Marca />
        <p className="portal-frase">{frase}</p>
      </aside>
      <main className="portal-forma">
        <div className="portal-movil"><Marca /></div>
        <div className="portal-caja">
          <Volver a={volver} texto={volver === "/" ? "Inicio" : "Regresar"} />
          <h1>{titulo}</h1>
          {bajada && <p className="portal-bajada">{bajada}</p>}
          {children}
        </div>
      </main>
    </div>
  );
}
