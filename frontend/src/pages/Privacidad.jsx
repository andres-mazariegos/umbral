import { Link } from "react-router-dom";
import { Marca } from "../components/Basicos.jsx";
import Volver from "../components/Volver.jsx";

export default function Privacidad() {
  return (
    <div className="legal">
      <Marca />
      <Volver />
      <h1>Aviso de privacidad</h1>
      <p className="legal-fecha">Vigente desde noviembre de 2026</p>

      <h2>Quién es responsable</h2>
      <p>Umbral es un proyecto académico de Carlos Andrés Mazariegos Laguna, estudiante de la Universidad Politécnica de Chiapas, para la materia Seguridad Informática.</p>

      <h2>Qué datos guardamos</h2>
      <ul>
        <li><b>De tu cuenta:</b> nombre, correo y una huella irreversible de tu contraseña (Argon2id). La contraseña en sí nunca se guarda.</li>
        <li><b>De tus equipos:</b> el nombre que tú les pongas, su sistema operativo y, por cada revisión, la lista de puertos abiertos con el programa que abrió cada uno y el estado del cortafuegos.</li>
        <li><b>De seguridad:</b> una bitácora de accesos a tu cuenta (fecha y dirección IP) para que puedas detectar entradas que no reconozcas.</li>
      </ul>

      <h2>Qué no recolectamos</h2>
      <p>El agente no lee archivos, contraseñas, historial de navegación, pulsaciones del teclado, capturas de pantalla ni el contenido de tu tráfico de red. Tu nombre de usuario del sistema se elimina de las rutas antes de enviarlas.</p>

      <h2>Para qué los usamos</h2>
      <p>Únicamente para mostrarte el estado de tus equipos y explicarte cada hallazgo. No se venden, no se comparten con terceros y no se usan para publicidad.</p>

      <h2>Tu consentimiento</h2>
      <p>Ninguna revisión ocurre sin que la autorices dos veces: al generar el código de conexión en el sitio y al responder «sí» en el agente, en tu propia computadora. Puedes revocar el permiso quitando el equipo desde <i>Mis equipos</i>.</p>

      <h2>Tus derechos</h2>
      <p>Puedes consultar, corregir y borrar tus datos en cualquier momento desde <i>Cuenta</i>. Al eliminar la cuenta se borran de inmediato tus equipos, revisiones y bitácora.</p>

      <h2>Uso responsable</h2>
      <p>Conecta solo equipos que sean tuyos o sobre los que tengas autorización. Revisar equipos ajenos sin permiso puede constituir un delito.</p>

      <p><Link to="/">Volver al inicio</Link></p>
    </div>
  );
}
