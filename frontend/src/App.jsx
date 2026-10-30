// Rutas principales de Umbral.
// Por ahora tengo la landing y el login. Mas adelante agrego
// el registro, el consentimiento y el panel de revisiones.
import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
    </Routes>
  );
}

export default App;
