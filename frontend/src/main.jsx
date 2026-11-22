// Punto de entrada del frontend de Umbral.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
// Arimo es una letra libre con las mismas medidas que Arial. Se usa cuando
// la computadora no tiene Arial instalada (por ejemplo en Linux).
import "@fontsource/arimo/latin-400.css";
import "@fontsource/arimo/latin-700.css";
import "./index.css";
import "./imprimir.css";
import App from "./App.jsx";
import { ProveedorSesion } from "./sesion.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <ProveedorSesion>
        <App />
      </ProveedorSesion>
    </BrowserRouter>
  </StrictMode>
);
