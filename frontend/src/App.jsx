// Mapa de pantallas de Umbral.
// Publicas: inicio, registro, confirmar, entrar, recuperar.
// Privadas (/panel): piden sesion; sin ella te mandan a entrar.
// /panel/admin: ademas pide ser administrador.
import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useSesion } from "./sesion.jsx";
import Landing from "./pages/Landing.jsx";
import Registro from "./pages/Registro.jsx";
import Confirmar from "./pages/Confirmar.jsx";
import Login from "./pages/Login.jsx";
import { Olvide, Restablecer } from "./pages/Recuperar.jsx";
import Privacidad from "./pages/Privacidad.jsx";
import NoEncontrada from "./pages/NoEncontrada.jsx";
import Marco from "./pages/panel/Marco.jsx";
import Inicio from "./pages/panel/Inicio.jsx";
import Equipos from "./pages/panel/Equipos.jsx";
import Revision from "./pages/panel/Revision.jsx";
import Historial from "./pages/panel/Historial.jsx";
import Aprende from "./pages/panel/Aprende.jsx";
import Cuenta from "./pages/panel/Cuenta.jsx";
import Admin from "./pages/panel/Admin.jsx";

function Cargando() {
  return <div className="cargando" role="status">Abriendo Umbral…</div>;
}

function SoloConSesion() {
  const { usuario } = useSesion();
  const donde = useLocation();
  if (usuario === undefined) return <Cargando />;
  if (!usuario) return <Navigate to="/entrar" replace state={{ volver: donde.pathname }} />;
  return <Marco><Outlet /></Marco>;
}

// La seccion de administracion solo se dibuja para administradores.
// Aunque alguien escriba /panel/admin a mano, la API le responde 404.
function SoloAdmin() {
  const { usuario } = useSesion();
  return usuario?.es_admin ? <Admin /> : <NoEncontrada />;
}

function SoloSinSesion() {
  const { usuario } = useSesion();
  if (usuario === undefined) return <Cargando />;
  if (usuario) return <Navigate to="/panel" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/privacidad" element={<Privacidad />} />
      <Route path="/confirmar" element={<Confirmar />} />
      <Route path="/restablecer" element={<Restablecer />} />
      <Route element={<SoloSinSesion />}>
        <Route path="/registro" element={<Registro />} />
        <Route path="/entrar" element={<Login />} />
        <Route path="/login" element={<Navigate to="/entrar" replace />} />
        <Route path="/olvide" element={<Olvide />} />
      </Route>
      <Route path="/panel" element={<SoloConSesion />}>
        <Route index element={<Inicio />} />
        <Route path="equipos" element={<Equipos />} />
        <Route path="revision/:id" element={<Revision />} />
        <Route path="historial" element={<Historial />} />
        <Route path="aprende" element={<Aprende />} />
        <Route path="cuenta" element={<Cuenta />} />
        <Route path="admin" element={<SoloAdmin />} />
      </Route>
      <Route path="*" element={<NoEncontrada />} />
    </Routes>
  );
}
