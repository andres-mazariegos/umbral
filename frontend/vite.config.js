import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El frontend habla con la API por la misma direccion (/api): Vite le pasa
// esas peticiones al backend. Asi la cookie de sesion nunca cruza de dominio.
// host: true permite abrir Umbral desde el celular en la misma red Wi-Fi.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } },
  },
  // Sin archivos .map al compilar: esos archivos dejan ver el codigo original
  // completo del sitio, y es lo primero que descargan agentes como ARTEX.
  build: { sourcemap: false },
})
