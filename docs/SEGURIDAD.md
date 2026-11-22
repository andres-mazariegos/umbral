# Medidas de seguridad de Umbral

Cada medida dice contra qué protege y en qué archivo está, para poder
enseñarla en el código.

## Contraseñas

| Medida | Protege contra | Dónde |
|---|---|---|
| Se guarda una huella Argon2id, nunca la contraseña | Robo de la base de datos | `backend/app/security.py` (`crear_hash`) |
| Mínimo 10 caracteres, mayúscula, minúscula y número | Contraseñas débiles | `backend/app/schemas.py` (`validar_clave`) |
| Se rechazan las contraseñas más filtradas y las que contienen tu nombre o correo | Ataques de diccionario | `backend/app/schemas.py` |
| Al cambiarla se cierran las demás sesiones y llega un aviso por correo | Sesiones robadas | `backend/app/routers/cuenta.py` |

## Acceso a la cuenta

| Medida | Protege contra | Dónde |
|---|---|---|
| Bloqueo de 15 minutos tras 5 contraseñas incorrectas | Fuerza bruta | `security.py` (`registrar_fallo`) |
| Límite de peticiones por IP en registro, entrada, códigos y agente | Automatización y abuso | `security.py` (`limitar`) |
| El mismo mensaje y el mismo tiempo de respuesta exista o no el correo | Enumeración de usuarios | `routers/auth.py` |
| Confirmación de correo obligatoria antes de entrar | Cuentas falsas | `routers/auth.py` (`confirmar`) |
| Códigos de 6 dígitos que vencen en 15 min, sirven una vez y se anulan al quinto error | Adivinar el código | `routers/auth.py` |
| En la base solo hay huellas (HMAC-SHA256) de códigos, enlaces y llaves | Robo de la base de datos | `security.py` (`huella`) |
| Bitácora de accesos visible para el usuario | Entradas no reconocidas | `routers/cuenta.py` (`actividad`) |

## Sesión

| Medida | Protege contra | Dónde |
|---|---|---|
| El token viaja en una cookie `HttpOnly` | Robo de sesión por XSS | `security.py` (`poner_cookie`) |
| Cookie `SameSite=Strict` y cabecera `X-Umbral` obligatoria | CSRF | `security.py`, `main.py` (`escudo`) |
| Cookie `Secure` y cabecera HSTS fuera de desarrollo | Intercepción sin HTTPS | `security.py`, `main.py` |
| El token caduca a las 12 horas y lleva versión de sesión | Tokens viejos | `security.py` (`crear_sesion`) |

## Datos de entrada

| Medida | Protege contra | Dónde |
|---|---|---|
| Nombres solo con letras; nombres de equipo solo letras, números, espacio y guiones | Inyección de código y de HTML | `schemas.py` (`SOLO_LETRAS`, `NOMBRE_EQUIPO`) |
| Longitud máxima en cada campo y tope de 256 KB por petición | Saturación del servidor | `schemas.py`, `main.py` |
| Campos desconocidos se rechazan (`extra="forbid"`) | Asignación masiva (por ejemplo, mandar `"rol": "admin"`) | `schemas.py` (`Base`) |
| Consultas con SQLAlchemy (parámetros enlazados) | Inyección SQL | todos los `routers/` |
| React escapa todo lo que muestra; no se usa `dangerouslySetInnerHTML` | XSS | `frontend/src` |
| Lo que manda el agente se valida igual que un formulario | Agente falso o manipulado | `schemas.py` (`ReporteIn`) |

## Cabeceras del navegador

`Content-Security-Policy` (solo recursos propios, sin marcos), `X-Frame-Options: DENY`,
`X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
`Permissions-Policy` y `Cache-Control: no-store` en la API. Todas en `backend/app/main.py`.

Las tipografías se sirven desde el propio sitio: no se carga nada de terceros.

## Autorización

| Medida | Protege contra | Dónde |
|---|---|---|
| Toda consulta de revisiones, hallazgos y equipos filtra por dueño | Ver datos de otra cuenta cambiando el número de la URL (IDOR) | `routers/revisiones.py` (`_mia`), `routers/equipos.py` |
| La documentación automática de la API se apaga en producción | Dar el mapa de la API a un atacante | `main.py` |
| El rol de administrador no se guarda en la tabla: lo decide `UMBRAL_ADMINS` en el servidor | Que alguien se vuelva administrador editando su cuenta (escalada de privilegios) | `config.py`, `models.py` (`es_admin`) |
| A quien no es administrador, `/api/admin/*` le responde 404 (no 403) | Descubrir que existe una sección oculta | `security.py` (`usuario_admin`) |
| El administrador ve los correos tapados (`ca****@gmail.com`) | Exponer datos personales de más (mínimo privilegio) | `routers/admin.py` |

## El agente y el consentimiento

| Medida | Para qué | Dónde |
|---|---|---|
| Doble permiso: tres casillas en el sitio y un «s» en la terminal | Que nada se revise sin autorización | `frontend/src/pages/panel/Equipos.jsx`, `agent/umbral_agente.py` (`_permiso`) |
| Código de conexión de un solo uso, 10 minutos | Que nadie conecte un equipo a tu cuenta | `routers/equipos.py` |
| Cada equipo tiene su propia llave y se puede anular al instante | Revocar un equipo perdido | `routers/equipos.py` (`quitar`) |
| `--ver` enseña exactamente lo que se enviaría | Transparencia | `agent/umbral_agente.py` |
| Se quita el nombre de usuario de las rutas antes de enviarlas | Mínimo dato necesario | `agent/umbral_agente.py` (`_sin_usuario`) |
| Solo lee el equipo donde corre; no escanea la red | Evitar uso contra terceros | `agent/umbral_agente.py` |
| Avisa si el servidor no usa HTTPS | Envío sin cifrar | `agent/umbral_agente.py` (`_conectar`) |

## Despliegue

| Medida | Protege contra | Dónde |
|---|---|---|
| Las llaves (secreta, base de datos, Resend) viven en las Variables de Railway, nunca en GitHub | Fuga de secretos en el repositorio | `.env.produccion.example`, `.gitignore` |
| HTTPS obligatorio con certificado automático y cabecera HSTS | Espiar o modificar el tráfico (hombre en medio) | Railway, `main.py` |
| El contenedor corre con un usuario sin privilegios (no root) | Que una falla en la app tome control del contenedor | `Dockerfile` |
| PostgreSQL solo acepta conexiones con usuario y contraseña generados por Railway | Acceso directo a la base | Railway |
| El agente de Windows no necesita instalar nada y su código es texto legible | Pedir al usuario que corra un .exe que no puede revisar | `agent/umbral-agente.ps1` |

## Privacidad

Borrar la cuenta elimina en cascada equipos, revisiones, hallazgos y bitácora
(`routers/cuenta.py`, `eliminar`). El aviso de privacidad está en `/privacidad`.

## Pruebas

`backend/tests/test_flujo.py` comprueba, entre otras cosas: que el registro
rechaza `<script>`, comillas y campos extra; que sin la cabecera `X-Umbral` no
se acepta nada; el bloqueo tras cinco fallos; que un código no sirve dos veces;
que una cuenta no puede leer las revisiones de otra; y que al quitar un equipo
su llave deja de funcionar.

## Revisión con Semgrep y CodeQL

| Herramienta | Resultado | Qué se hizo |
|---|---|---|
| CodeQL (GitHub, modo Extended) | 0 alertas | Se dejó activo: revisa el código en cada `git push` y cada semana |
| Semgrep CE (`--config auto`, 501 reglas) | 1 hallazgo en `agent/umbral_agente.py`: `dynamic-urllib-use-detected` (CWE-939) | `urlopen` también abre direcciones `file://`. El agente ahora usa un abridor que solo conoce `http` y `https` y rechaza cualquier otra dirección. Tras corregirlo: 0 hallazgos |

Regla propia: `reglas/umbral-urllib.yml`. Busca todas las variantes de ese
error, incluidas `build_opener(...).open(...)`, que la regla de la comunidad
no revisa. Se probó contra `pruebas-semgrep/variantes_inseguras.py` (4 variantes
a propósito, 4 encontradas).

```bash
semgrep scan --config reglas/umbral-urllib.yml
```

## Revisión contra lo que intentan los agentes como ARTEX

Basada en el artículo *ARTEX: La nueva era de las pruebas de penetración con IA*
(Mtro. José Alonso Macías Montoya, noviembre de 2026). Cada fila tiene su prueba
en `backend/tests/test_artex.py`.

| Lo que intenta el agente | Cómo responde Umbral | Prueba |
|---|---|---|
| Descargar source maps (`.js.map`) | Vite compila con `sourcemap: false`; no hay archivos `.map` en `dist` | `test_vite_no_genera_source_maps`, `test_sitio_compilado_sin_archivos_map` |
| Leer `/env.js`, `/assets/config.json`, `.env` o `.git` | El sitio solo sirve archivos de `frontend/dist`; lo demás regresa la página principal | `test_no_se_pueden_leer_archivos_del_servidor` |
| Leer Swagger / OpenAPI expuesto | La documentación de la API se apaga fuera de desarrollo | `test_documentacion_de_la_api_apagada_en_produccion` |
| Usar un JWT sin firma (`"alg": "none"`) o con otra llave | Solo se acepta HS256 firmado con la llave del servidor | `test_token_sin_firma_alg_none_no_sirve`, `test_token_firmado_con_otra_llave_no_sirve` |
| Enumerar usuarios con el login o la recuperación | Mismo mensaje exista o no el correo | `test_login_no_revela_si_el_correo_existe`, `test_recuperar_contrasena_no_revela_si_el_correo_existe` |
| Ver datos de otro usuario cambiando el número (IDOR) | Toda consulta filtra por dueño: responde 404 | `test_no_se_ven_revisiones_de_otro_usuario_cambiando_el_numero` |
| Ráfagas de peticiones | Límite por IP; responde 429 | `test_rafaga_contra_el_codigo_de_conexion_se_corta` |

Regla de uso: cualquier prueba ofensiva automatizada se corre solo contra
Umbral en `localhost` o en un contenedor propio, nunca contra equipos ajenos.
