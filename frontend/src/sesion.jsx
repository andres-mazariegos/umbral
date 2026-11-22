// Quien esta usando Umbral ahora mismo. Se pregunta al servidor (cookie),
// no se guarda nada sensible en el navegador.
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api.js";

const Contexto = createContext(null);

export function ProveedorSesion({ children }) {
  const [usuario, setUsuario] = useState(undefined); // undefined = todavia no sabemos
  const [servidor, setServidor] = useState({ revision_directa: false, correo_real: true, modo_dev: false });

  useEffect(() => {
    api("/auth/yo").then((r) => setUsuario(r.usuario || null)).catch(() => setUsuario(null));
    api("/estado").then(setServidor).catch(() => {});
    const vencida = () => setUsuario(null);
    window.addEventListener("umbral:sesion-vencida", vencida);
    return () => window.removeEventListener("umbral:sesion-vencida", vencida);
  }, []);

  const salir = useCallback(async () => {
    await api("/auth/salir", { metodo: "POST" }).catch(() => {});
    setUsuario(null);
  }, []);

  return <Contexto.Provider value={{ usuario, setUsuario, salir, servidor }}>{children}</Contexto.Provider>;
}

export const useSesion = () => useContext(Contexto);
