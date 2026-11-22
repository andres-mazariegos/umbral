// Mis equipos: conectar una computadora (con permiso explicito) y administrarlas.
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, haceCuanto, SISTEMAS } from "../../api.js";
import { Aviso, Boton, Campo, Copiar, Flecha } from "../../components/Basicos.jsx";
import Volver from "../../components/Volver.jsx";

const PERMISOS = [
  "Entiendo que el agente leerá qué puertos están abiertos y qué programa abrió cada uno.",
  "Entiendo que no lee archivos, contraseñas ni historial, y que no cambia nada en mi equipo.",
  "Este equipo es mío o tengo autorización de su dueño para revisarlo.",
];

function Conectar({ alTerminar, alCancelar }) {
  const [paso, setPaso] = useState(1);
  const [nombre, setNombre] = useState("");
  const [marcas, setMarcas] = useState([false, false, false]);
  const [enlace, setEnlace] = useState(null);
  const [estado, setEstado] = useState(null);
  const [so, setSo] = useState(/Linux|X11/.test(navigator.userAgent) && !/Android/.test(navigator.userAgent) ? "linux" : "windows");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const [resta, setResta] = useState(0);
  const reloj = useRef(null);

  const generar = async (e) => {
    e.preventDefault();
    setError("");
    if (!marcas.every(Boolean)) return setError("Marca las tres casillas: sin tu permiso no se conecta nada.");
    setCargando(true);
    try {
      const r = await api("/equipos/enlace", { metodo: "POST", datos: { nombre: nombre.trim(), permiso: true } });
      setEnlace(r);
      setResta(r.minutos * 60);
      setPaso(2);
    } catch (err) {
      setError(err.campos?.nombre || err.message);
    } finally {
      setCargando(false);
    }
  };

  // Mientras se muestra el codigo, se pregunta cada 3 s si el agente ya se conecto.
  useEffect(() => {
    if (paso !== 2 || !enlace) return;
    reloj.current = setInterval(async () => {
      setResta((s) => Math.max(0, s - 3));
      try {
        const r = await api(`/equipos/enlace/${enlace.id}`);
        setEstado(r);
        if (r.conectado && r.revision_id) { clearInterval(reloj.current); setPaso(3); }
      } catch { /* se reintenta en la siguiente vuelta */ }
    }, 3000);
    return () => clearInterval(reloj.current);
  }, [paso, enlace]);

  const servidor = window.location.origin;
  // Windows: agente en PowerShell (no hay que instalar nada).
  // Linux (Kali, Ubuntu, Debian): agente en Python, que ya viene instalado.
  const comando = !enlace ? "" : so === "windows"
    ? `powershell -ExecutionPolicy Bypass -File .\\umbral-agente.ps1 -Servidor ${servidor} -Codigo ${enlace.codigo}`
    : `sudo python3 umbral_agente.py --servidor ${servidor} --codigo ${enlace.codigo}`;

  return (
    <section className="conectar">
      <ol className="conectar-pasos" aria-label="Progreso">
        {["Tu permiso", "Corre el agente", "Listo"].map((t, i) => (
          <li key={t} className={paso === i + 1 ? "es-actual" : paso > i + 1 ? "es-hecho" : ""}><span>{i + 1}</span> {t}</li>
        ))}
      </ol>

      {paso === 1 && (
        <form onSubmit={generar} noValidate>
          <h2>Antes de conectar, lo que vas a permitir</h2>
          <Campo etiqueta="¿Cómo le decimos a este equipo?" value={nombre} maxLength={40} placeholder="Laptop de Carlos"
            onChange={(e) => setNombre(e.target.value.replace(/[^A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ _-]/g, ""))}
            ayuda="Letras, números, espacios y guiones." />
          {PERMISOS.map((p, i) => (
            <label className="casilla" key={p}>
              <input type="checkbox" checked={marcas[i]} onChange={(e) => setMarcas(marcas.map((m, k) => (k === i ? e.target.checked : m)))} />
              <span>{p}</span>
            </label>
          ))}
          <Aviso>{error}</Aviso>
          <div className="fila-botones">
            <Boton cargando={cargando} type="submit" disabled={nombre.trim().length < 2}>Doy mi permiso</Boton>
            <button type="button" className="boton boton-linea" onClick={alCancelar}>Cancelar</button>
          </div>
        </form>
      )}

      {paso === 2 && enlace && (
        <div>
          <h2>Ahora, en la computadora que quieres revisar</h2>
          <div className="codigo-enlace">
            <p>Tu código de conexión</p>
            <strong>{enlace.codigo}</strong>
            <small>{resta > 0 ? `Sirve una sola vez. Vence en ${Math.ceil(resta / 60)} min.` : "El código venció. Cancela y genera otro."}</small>
          </div>

          <div className="so-pestanas" role="tablist" aria-label="Sistema operativo">
            {["windows", "linux"].map((s) => (
              <button key={s} type="button" role="tab" aria-selected={so === s} onClick={() => setSo(s)}>{SISTEMAS[s]}</button>
            ))}
          </div>
          <ol className="instrucciones">
            <li>
              <b>Descarga el agente.</b> Es un solo archivo de texto; puedes abrirlo con el Bloc de notas para leer todo lo que hace.
              {so === "windows"
                ? <a className="boton boton-linea" href="/api/agente/descarga/windows" download>Descargar umbral-agente.ps1</a>
                : <a className="boton boton-linea" href="/api/agente/descarga" download>Descargar umbral_agente.py</a>}
            </li>
            {so === "windows" ? (
              <>
                <li><b>Abre PowerShell.</b> Presiona la tecla Windows, escribe <kbd>powershell</kbd> y pulsa Enter. Para ver todos los programas, elige «Ejecutar como administrador».</li>
                <li><b>Entra a Descargas:</b><Copiar texto="cd $HOME\Downloads" /></li>
              </>
            ) : (
              <>
                <li><b>Abre una terminal</b> (Ctrl + Alt + T).</li>
                <li><b>Entra a Descargas:</b><Copiar texto="cd ~/Descargas || cd ~/Downloads" /></li>
              </>
            )}
            <li><b>Corre el agente</b> con tu código. Te pedirá permiso en pantalla: responde <kbd>s</kbd>.
              <Copiar texto={comando} />
            </li>
          </ol>
          <p className="nota">
            {so === "windows"
              ? <>No necesitas instalar nada: PowerShell ya viene en Windows 10 y 11. «-ExecutionPolicy Bypass» solo vale para esta vez y no cambia la seguridad de tu equipo. Para ver qué enviaría sin enviar nada: <code>powershell -ExecutionPolicy Bypass -File .\umbral-agente.ps1 -Ver</code></>
              : <>Python ya viene en Kali, Ubuntu y Debian. «sudo» sirve para ver el nombre de todos los programas. Para ver qué enviaría sin enviar nada: <code>python3 umbral_agente.py --ver</code></>}
          </p>
          <p className="esperando" role="status">
            <span className="pulso" aria-hidden="true" />
            {estado?.conectado ? "Equipo conectado. Esperando su primera revisión…" : "Esperando a que el agente se conecte…"}
          </p>
          <button type="button" className="volver" onClick={() => { clearInterval(reloj.current); setPaso(1); }}><Flecha dir="izq" /> Regresar al paso 1</button>
          <button type="button" className="enlace" onClick={alCancelar}>Cancelar</button>
        </div>
      )}

      {paso === 3 && (
        <div className="conectado">
          <h2>«{nombre}» ya está conectado.</h2>
          <p>Llegó su primera revisión. Cada vez que quieras otra, vuelve a correr el agente: ya no pide código.</p>
          <div className="fila-botones">
            <Link className="boton boton-lleno" to={`/panel/revision/${estado.revision_id}`}>Leer la revisión <Flecha /></Link>
            <button type="button" className="boton boton-linea" onClick={alTerminar}>Ver mis equipos</button>
          </div>
        </div>
      )}
    </section>
  );
}

export default function Equipos() {
  const [params, setParams] = useSearchParams();
  const [equipos, setEquipos] = useState(null);
  const [error, setError] = useState("");
  const [editando, setEditando] = useState(null);
  const conectando = params.get("conectar") === "1";

  const cargar = useCallback(() => api("/equipos").then((r) => setEquipos(r.equipos)).catch((e) => setError(e.message)), []);
  useEffect(() => { cargar(); }, [cargar]);

  const cerrar = () => { setParams({}); cargar(); };

  const quitar = async (e) => {
    if (!window.confirm(`¿Desconectar «${e.nombre}»? Su agente dejará de poder enviar revisiones. El historial se conserva.`)) return;
    await api(`/equipos/${e.id}`, { metodo: "DELETE" }).catch((err) => setError(err.message));
    cargar();
  };

  const renombrar = async (ev) => {
    ev.preventDefault();
    try {
      await api(`/equipos/${editando.id}`, { metodo: "PATCH", datos: { nombre: editando.nombre.trim() } });
      setEditando(null);
      cargar();
    } catch (err) {
      setError(err.campos?.nombre || err.message);
    }
  };

  if (!equipos) return <div className="cargando">{error || "Cargando equipos…"}</div>;

  return (
    <div className="equipos">
      {conectando && <Volver a="/panel/equipos" texto="Mis equipos" />}
      <header className="cabeza">
        <p className="antetitulo">Mis equipos</p>
        <h1>{equipos.length ? "Las computadoras que Umbral cuida contigo." : "Aún no conectas ninguna computadora."}</h1>
        {!conectando && <button type="button" className="boton boton-lleno" onClick={() => setParams({ conectar: "1" })}>Conectar un equipo <Flecha /></button>}
      </header>
      <Aviso>{error}</Aviso>

      {conectando && <Conectar alTerminar={cerrar} alCancelar={cerrar} />}

      {!conectando && equipos.length > 0 && (
        <ul className="equipos-lista">
          {equipos.map((e) => (
            <li key={e.id}>
              <div className="equipo-quien">
                {editando?.id === e.id ? (
                  <form onSubmit={renombrar} className="renombrar">
                    <input value={editando.nombre} maxLength={40} autoFocus aria-label="Nombre del equipo"
                      onChange={(ev) => setEditando({ ...editando, nombre: ev.target.value.replace(/[^A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ _-]/g, "") })} />
                    <button type="submit" className="enlace">Guardar</button>
                    <button type="button" className="enlace" onClick={() => setEditando(null)}>Cancelar</button>
                  </form>
                ) : (
                  <h2>{e.nombre}</h2>
                )}
                <p>{e.detalle_sistema || SISTEMAS[e.sistema] || "Sistema sin identificar"} · última señal {haceCuanto(e.ultima_senal)}</p>
              </div>
              <div className="equipo-estado">
                {e.ultima_revision ? (
                  <Link to={`/panel/revision/${e.ultima_revision.id}`}>
                    {e.ultima_revision.resumen.por_atender > 0
                      ? <b className="texto-urgente">{e.ultima_revision.resumen.por_atender} por atender</b>
                      : <b className="texto-tranquilo">Nada urgente</b>}
                    <small>{e.ultima_revision.resumen.total} puertas abiertas <Flecha /></small>
                  </Link>
                ) : <small>Sin revisiones todavía</small>}
              </div>
              <div className="equipo-acciones">
                <button type="button" className="enlace" onClick={() => setEditando({ id: e.id, nombre: e.nombre })}>Renombrar</button>
                <button type="button" className="enlace enlace-peligro" onClick={() => quitar(e)}>Desconectar</button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {!conectando && (
        <section className="nota-agente">
          <h2>Para revisar de nuevo un equipo ya conectado</h2>
          <p>Abre la terminal en ese equipo, entra a la carpeta donde guardaste el agente y córrelo sin código.</p>
          <p><b>Windows:</b></p>
          <Copiar texto={"powershell -ExecutionPolicy Bypass -File .\\umbral-agente.ps1"} />
          <p><b>Kali o cualquier Linux:</b></p>
          <Copiar texto="sudo python3 umbral_agente.py" />
          <p>Para que revise solo cada media hora mientras trabajas, agrega <code>-Vigilar 30</code> en Windows o <code>--vigilar 30</code> en Linux.</p>
        </section>
      )}
    </div>
  );
}
