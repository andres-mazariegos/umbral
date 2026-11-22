// Una sola puerta de salida hacia la API.
// - La sesion viaja en una cookie HttpOnly: el JavaScript nunca toca el token.
// - Toda peticion lleva la cabecera X-Umbral, que el backend exige contra CSRF.
export class ErrorApi extends Error {
  constructor(mensaje, estado, campos, motivo) {
    super(mensaje);
    this.estado = estado;
    this.campos = campos || {};
    this.motivo = motivo;
  }
}

export async function api(ruta, { metodo = "GET", datos } = {}) {
  let respuesta;
  try {
    respuesta = await fetch(`/api${ruta}`, {
      method: metodo,
      credentials: "same-origin",
      headers: { "X-Umbral": "web", ...(datos ? { "Content-Type": "application/json" } : {}) },
      body: datos ? JSON.stringify(datos) : undefined,
    });
  } catch {
    throw new ErrorApi("No hay conexión con Umbral. Revisa que el servidor esté encendido.", 0);
  }
  let cuerpo = {};
  try {
    cuerpo = await respuesta.json();
  } catch {
    /* respuesta sin cuerpo */
  }
  if (!respuesta.ok) {
    const mensaje = typeof cuerpo.detail === "string" ? cuerpo.detail : "Algo salió mal. Intenta de nuevo.";
    if (respuesta.status === 401 && !ruta.startsWith("/auth/")) {
      window.dispatchEvent(new Event("umbral:sesion-vencida"));
    }
    throw new ErrorApi(mensaje, respuesta.status, cuerpo.campos, respuesta.headers.get("X-Umbral-Motivo"));
  }
  return cuerpo;
}

// ---- utilidades de presentacion ----
const FECHA = new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "long", hour: "numeric", minute: "2-digit" });
const DIA = new Intl.DateTimeFormat("es-MX", { weekday: "long", day: "numeric", month: "long" });

export const fecha = (iso) => (iso ? FECHA.format(new Date(iso)) : "");
export const dia = (iso) => (iso ? DIA.format(new Date(iso)) : "");

export function haceCuanto(iso) {
  if (!iso) return "nunca";
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (min < 1) return "hace un momento";
  if (min < 60) return `hace ${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `hace ${h} h`;
  const d = Math.round(h / 24);
  return d === 1 ? "ayer" : `hace ${d} días`;
}

export const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;

export const NIVELES = {
  urgente: { nombre: "Atiéndelo ya", corto: "Urgente" },
  atento: { nombre: "Ojo aquí", corto: "Ojo" },
  tranquilo: { nombre: "Tranquilo", corto: "Bien" },
};

export const SISTEMAS = { windows: "Windows", linux: "Linux", mac: "macOS" };
