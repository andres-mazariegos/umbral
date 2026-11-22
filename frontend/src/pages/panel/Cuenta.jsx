// Cuenta: tus datos, tu contraseña, quien ha entrado y como borrar todo.
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, fecha } from "../../api.js";
import { Aviso, Boton, Campo, ReglasClave, reglasClave } from "../../components/Basicos.jsx";
import { useSesion } from "../../sesion.jsx";

export default function Cuenta() {
  const ir = useNavigate();
  const { usuario, setUsuario, salir } = useSesion();
  const [nombre, setNombre] = useState(usuario.nombre);
  const [claves, setClaves] = useState({ actual: "", nueva: "" });
  const [borrar, setBorrar] = useState("");
  const [eventos, setEventos] = useState([]);
  const [msg, setMsg] = useState({});
  const [ocupado, setOcupado] = useState("");

  const cargarActividad = () => api("/cuenta/actividad").then((r) => setEventos(r.eventos)).catch(() => {});
  useEffect(() => { cargarActividad(); }, []);

  const accion = async (clave, fn) => {
    setOcupado(clave); setMsg({});
    try {
      const texto = await fn();
      setMsg({ [clave]: { bien: texto } });
      cargarActividad();
    } catch (e) {
      setMsg({ [clave]: { mal: e.campos?.nombre || e.message } });
    } finally {
      setOcupado("");
    }
  };

  const guardarNombre = (e) => {
    e.preventDefault();
    accion("nombre", async () => {
      const r = await api("/cuenta/nombre", { metodo: "PATCH", datos: { nombre: nombre.trim() } });
      setUsuario(r.usuario);
      return "Nombre actualizado.";
    });
  };

  const guardarClave = (e) => {
    e.preventDefault();
    if (!reglasClave(claves.nueva, usuario.nombre, usuario.email).every((r) => r.ok)) {
      return setMsg({ clave: { mal: "La contraseña nueva aún no cumple los requisitos." } });
    }
    accion("clave", async () => {
      const r = await api("/cuenta/clave", { metodo: "POST", datos: claves });
      setClaves({ actual: "", nueva: "" });
      return r.mensaje;
    });
  };

  const eliminar = (e) => {
    e.preventDefault();
    if (!window.confirm("Esto borra tu cuenta, tus equipos y todas tus revisiones. No se puede deshacer. ¿Continuar?")) return;
    accion("borrar", async () => {
      await api("/cuenta/eliminar", { metodo: "POST", datos: { clave: borrar } });
      setUsuario(null);
      ir("/", { replace: true });
    });
  };

  return (
    <div className="cuenta">
      <header className="cabeza">
        <p className="antetitulo">Cuenta</p>
        <h1>{usuario.email}</h1>
        <button type="button" className="boton boton-linea" onClick={salir}>Cerrar sesión</button>
      </header>

      <section className="ajuste">
        <h2>Tu nombre</h2>
        <form onSubmit={guardarNombre} noValidate>
          <Campo etiqueta="Nombre" value={nombre} maxLength={60} autoComplete="name"
            onChange={(e) => setNombre(e.target.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]/g, ""))} ayuda="Solo letras y espacios." />
          <Aviso>{msg.nombre?.mal}</Aviso><Aviso tipo="bien">{msg.nombre?.bien}</Aviso>
          <Boton variante="linea" cargando={ocupado === "nombre"} type="submit" disabled={nombre.trim() === usuario.nombre}>Guardar nombre</Boton>
        </form>
      </section>

      <section className="ajuste">
        <h2>Contraseña</h2>
        <form onSubmit={guardarClave} noValidate>
          <Campo etiqueta="Contraseña actual" tipo="password" value={claves.actual} maxLength={128} autoComplete="current-password"
            onChange={(e) => setClaves({ ...claves, actual: e.target.value })} />
          <Campo etiqueta="Contraseña nueva" tipo="password" value={claves.nueva} maxLength={128} autoComplete="new-password"
            onChange={(e) => setClaves({ ...claves, nueva: e.target.value })} />
          <ReglasClave clave={claves.nueva} nombre={usuario.nombre} email={usuario.email} />
          <Aviso>{msg.clave?.mal}</Aviso><Aviso tipo="bien">{msg.clave?.bien}</Aviso>
          <Boton variante="linea" cargando={ocupado === "clave"} type="submit" disabled={!claves.actual || !claves.nueva}>Cambiar contraseña</Boton>
        </form>
      </section>

      <section className="ajuste">
        <h2>Actividad reciente</h2>
        <p className="ajuste-nota">Si ves una entrada que no reconoces, cambia tu contraseña y cierra las demás sesiones.</p>
        <ul className="actividad">
          {eventos.map((ev, i) => (
            <li key={i} className={ev.alerta ? "actividad-alerta" : ""}>
              <span>{ev.texto}{ev.detalle ? `: ${ev.detalle}` : ""}</span>
              <small>{fecha(ev.fecha)} · IP {ev.ip || "—"}</small>
            </li>
          ))}
        </ul>
        <Aviso tipo="bien">{msg.sesiones?.bien}</Aviso><Aviso>{msg.sesiones?.mal}</Aviso>
        <Boton variante="linea" cargando={ocupado === "sesiones"}
          onClick={() => accion("sesiones", async () => (await api("/cuenta/cerrar-sesiones", { metodo: "POST" })).mensaje)}>
          Cerrar sesión en los demás dispositivos
        </Boton>
      </section>

      <section className="ajuste ajuste-peligro">
        <h2>Borrar mi cuenta</h2>
        <p className="ajuste-nota">Se eliminan de inmediato tu cuenta, tus equipos, tus revisiones y tu bitácora. No guardamos copia.</p>
        <form onSubmit={eliminar} noValidate>
          <Campo etiqueta="Escribe tu contraseña para confirmar" tipo="password" value={borrar} maxLength={128} autoComplete="current-password"
            onChange={(e) => setBorrar(e.target.value)} />
          <Aviso>{msg.borrar?.mal}</Aviso>
          <Boton variante="peligro" cargando={ocupado === "borrar"} type="submit" disabled={!borrar}>Borrar todo</Boton>
        </form>
      </section>
    </div>
  );
}
