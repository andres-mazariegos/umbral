import { Link } from "react-router-dom";
import { Marca } from "../components/Basicos.jsx";
import Volver from "../components/Volver.jsx";

export default function NoEncontrada() {
  return (
    <div className="perdida" style={{ backgroundImage: "url(/fondos/pasillo.webp)" }}>
      <Marca />
      <p className="perdida-n">404</p>
      <h1>Esta puerta no lleva a ningún lado.</h1>
      <Volver texto="Regresar a donde estaba" />
      <Link to="/" className="boton boton-lleno">Ir al inicio</Link>
    </div>
  );
}
