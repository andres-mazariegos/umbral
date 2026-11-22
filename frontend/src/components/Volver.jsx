// Flecha para regresar.
// Si le pasas "a" va a esa pagina; si no, regresa a la pagina anterior.
import { Link, useNavigate } from "react-router-dom";
import { Flecha } from "./Basicos.jsx";

export default function Volver({ a, texto = "Regresar" }) {
  const ir = useNavigate();

  const regresar = (e) => {
    if (!a) {
      e.preventDefault();
      ir(-1);
    }
  };

  return (
    <Link to={a || "/"} onClick={regresar} className="volver">
      <Flecha dir="izq" /> {texto}
    </Link>
  );
}
