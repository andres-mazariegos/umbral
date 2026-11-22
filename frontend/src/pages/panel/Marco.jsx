// El marco del panel: navegacion lateral en computadora, barra inferior en celular.
import { NavLink } from "react-router-dom";
import { Marca } from "../../components/Basicos.jsx";
import { useSesion } from "../../sesion.jsx";

const SECCIONES = [
  { a: "/panel", texto: "Inicio", fin: true, d: "M4 11 12 4l8 7v9h-5v-6H9v6H4z" },
  { a: "/panel/equipos", texto: "Equipos", d: "M3 5h18v11H3zM8 20h8M12 16v4" },
  { a: "/panel/historial", texto: "Historial", d: "M12 7v5l3 2M4 12a8 8 0 1 0 2.6-5.9M4 4v4h4" },
  { a: "/panel/aprende", texto: "Aprende", d: "M4 5h7a3 3 0 0 1 3 3v12a3 3 0 0 0-3-3H4zM20 5h-3a3 3 0 0 0-3 3" },
  { a: "/panel/cuenta", texto: "Cuenta", d: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0" },
];

const ADMIN = { a: "/panel/admin", texto: "Admin", d: "M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6zM9 12l2 2 4-4" };

export default function Marco({ children }) {
  const { usuario, salir } = useSesion();
  const secciones = usuario.es_admin ? [...SECCIONES, ADMIN] : SECCIONES;
  return (
    <div className="panel">
      <aside className="riel">
        <Marca a="/panel" />
        <nav aria-label="Panel">
          {secciones.map((s) => (
            <NavLink key={s.a} to={s.a} end={s.fin}>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d={s.d} fill="none" stroke="currentColor" strokeWidth="1.8" /></svg>
              <span>{s.texto}</span>
            </NavLink>
          ))}
        </nav>
        <div className="riel-pie">
          <p>{usuario.nombre}</p>
          <button type="button" className="enlace" onClick={salir}>Cerrar sesión</button>
        </div>
      </aside>
      <main className="panel-cuerpo">{children}</main>
    </div>
  );
}
