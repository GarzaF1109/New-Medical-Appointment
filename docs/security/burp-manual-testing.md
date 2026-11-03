# Pruebas manuales con Burp Suite

Este documento es la guia para la sesion de **analisis dinamico manual** que
pide el punto (4) del enunciado. A diferencia de ZAP (automatizado, ver
[`owasp-zap.md`](owasp-zap.md)), aqui el analista interactua con la aplicacion
a traves de Burp y decide que tamperar en cada caso.

## Preparacion

1. Levantar la pila completa: `docker compose up --build`.
2. Configurar el navegador para usar el proxy de Burp (`127.0.0.1:8080` por
   defecto) e instalar el certificado CA de Burp si se va a interceptar TLS.
3. Navegar la interfaz en <http://localhost:8080> una vez con el proxy activo
   para que Burp descubra el sitio (Target → Site map).
4. Opcional pero recomendado: importar `backend`'s OpenAPI
   (`http://localhost:8000/openapi.json`) con la extension **OpenAPI Parser**
   o Postman→Burp, para tener cada endpoint listado en Target incluso los que
   la interfaz no usa directamente (p. ej. `PATCH /appointments/{id}`).

Dejar corriendo `docker compose logs -f backend` en otra terminal: varias de
las pruebas de abajo se verifican mirando que **no** aparezca el detalle
tecnico en la respuesta, pero si en la bitacora.

## Mapa de superficie

| Recurso | Endpoints | Dato sensible involucrado |
|---|---|---|
| Pacientes | `GET/POST /patients`, `GET/PATCH/DELETE /patients/{id}`, `GET /patients/{id}/appointments` | Nombre, fecha de nacimiento, telefono |
| Doctores | `GET/POST /doctors`, `GET/PATCH/DELETE /doctors/{id}`, `GET /doctors/{id}/appointments` | Cedula profesional |
| Citas | `GET/POST /appointments`, `GET/PATCH /appointments/{id}`, `PUT .../confirmation|completion|cancellation`, `DELETE /appointments/{id}` | Motivo de consulta (dato clinico) |

**Nota de alcance:** el sistema **no tiene autenticacion ni autorizacion**
(ADR-002 lo deja pendiente junto con JWT/RBAC). Esto no es un hallazgo que
haya que "encontrar" — es una limitacion conocida y documentada del alcance
actual. En la expo, repórtalo como tal (A01/A07 fuera de alcance por diseño)
en vez de presentarlo como un descubrimiento sorpresivo.

## Casos por categoria OWASP Top 10 (2021)

### A01 — Broken Access Control (IDOR)

Como no hay autenticacion, no hay un "usuario A no debe ver datos del usuario
B" que probar. Lo que **si** aplica es que cualquier ID secuencial es
adivinable y de solo cambiar el numero se llega al recurso de otra persona:

- En Repeater, `GET /api/v1/patients/1`, luego `/2`, `/3`... Confirma que los
  IDs son secuenciales y por lo tanto enumerables (no es un hallazgo nuevo,
  es consecuencia directa de no tener auth — documentalo asi).
- `DELETE /api/v1/patients/{id}` sin haber pasado por la UI: confirma que
  cualquiera con la URL puede borrar cualquier paciente.

### A02 — Cryptographic Failures

- Confirma que en produccion simulada (`docker compose`) el trafico va por
  HTTP plano, sin TLS. Revisa si `Set-Cookie` existe en alguna respuesta (no
  deberia, no hay sesiones) y si algun dato sensible viaja en query string en
  vez de body (revisa `GET /appointments?patientId=...` — el filtro es
  publico, no es un secreto, asi que no aplica aqui).

### A03 — Injection

- **SQLi en filtros**: en Repeater, prueba
  `GET /api/v1/appointments?doctorId=1' OR '1'='1` y variantes en `status`,
  `dateFrom`, `dateTo`. SQLAlchemy parametriza las consultas, asi que se
  espera `422` (tipo invalido) y no un error 500 ni resultados inesperados.
  Si ves un 500 con traza SQL, es un hallazgo real.
- **XSS almacenado**: da de alta un paciente con
  `fullName` conteniendo `<img src=x onerror=alert(1)>` — la validacion de
  `validate_person_name` deberia rechazarlo (solo letras/espacios/guiones). Si
  pasa el campo `reason` de una cita (texto libre, menos restringido), prueba
  ahi: crea la cita con ese payload en `reason` y confirma si la tabla de
  citas en React lo renderiza como texto (JSX escapa por defecto) o si en
  algun lugar se usa `dangerouslySetInnerHTML` (buscalo en el repo: no deberia
  haber ninguno).
- **Mass assignment via PATCH**: `PATCH /patients/{id}` con un cuerpo que
  incluya campos que el schema no expone (`{"id": 999, "role": "admin"}`).
  Pydantic con `extra="ignore"`/schema estricto deberia descartarlos; confirma
  que la respuesta no refleja el campo inventado.

### A04 — Insecure Design (logica de negocio)

Estos son los mas interesantes de este proyecto porque la regla de negocio
central es el no-traslape de horario:

- **Condicion de carrera**: con Burp Intruder o Turbo Intruder, dispara dos
  `POST /appointments` **simultaneos** con el mismo `doctorId`, `date` y
  `startTime` pero distinto `patientId`. La regla `TimeSlot.overlaps()`
  corre en Python contra una base compartida; confirma si ambas peticiones
  pueden colarse como `201` (condicion de carrera real) o si la segunda
  siempre recibe `409` (el comportamiento esperado, cerrado por una
  constraint o por serializacion de transacciones).
- **Transicion de estado ilegal**: intenta
  `PUT /appointments/{id}/confirmation` sobre una cita ya `Cancelada` o
  `Completada`. Debe responder `409`, nunca `200`.
- **Reagendado que no revalida**: reagenda una cita (`PATCH`) hacia un
  horario que ya ocupa otra cita del mismo doctor. Debe fallar con `409`
  igual que al crear (la correccion del ADR del sistema anterior); si no
  revalida, es una regresion real que vale la pena reportar en la expo.
- **Borrado de catalogo con citas vigentes**: confirma el `409` al intentar
  `DELETE /patients/{id}` o `/doctors/{id}` con una cita Pendiente o
  Confirmada asociada, y que **si** se permite tras cancelarla.

### A05 — Security Misconfiguration

- **CORS**: inspecciona la respuesta a un `OPTIONS` preflight. La politica
  (`CORS_ORIGINS`) deberia limitarse al origen del frontend
  (`http://localhost:8080`), no `*`. Si en algun ambiente aparece `*` con
  `allow_credentials: true`, es un hallazgo real y ademas invalido segun la
  especificacion CORS misma.
- **Cabeceras de seguridad ausentes**: revisa con Burp si la respuesta trae
  `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options` o
  `Strict-Transport-Security`. Hoy no las hay (ni Nginx en el frontend ni
  FastAPI las agregan) — es una brecha real y sencilla de reportar, aunque de
  severidad baja porque no hay sesiones que secuestrar.
- **Swagger/OpenAPI publico**: `/docs` y `/openapi.json` quedan accesibles sin
  restriccion. Aceptable para un entorno de evaluacion escolar; en
  produccion real se recomendaria restringirlos.

### A06 — Vulnerable and Outdated Components

Esto no se prueba con Burp sino con el propio build: corre
`npm audit` en `frontend/` y `pip list --outdated` (o `pip-audit` si esta
disponible) en `backend/`, y anexa el resultado al reporte. Es evidencia
reproducible y rapida de obtener.

### A07 — Identification and Authentication Failures

Fuera de alcance: no hay autenticacion que probar (ver nota de alcance
arriba). Documentalo como tal en vez de buscar un hallazgo que no existe.

### A08 — Software and Data Integrity Failures

No aplica de forma directa: no hay actualizaciones automaticas ni
deserializacion de datos no confiables mas alla de JSON validado por
Pydantic. Si se usa, mencionar que las imagenes Docker no estan firmadas
(aceptable para el alcance del curso).

### A09 — Security Logging and Monitoring Failures

- Provoca un error 500 real (por ejemplo, apaga la base de datos con
  `docker compose stop db` y haz una peticion) y confirma en
  `docker compose logs backend` que el detalle tecnico **si** queda
  registrado (`logger.exception` en `presentation/api/errors.py`) mientras que
  el cliente solo recibe el mensaje neutro `INTERNAL_ERROR`. Es el
  comportamiento correcto — confirmalo, no lo rompas.
- Revisa si hay rate limiting o alerta ante una rafaga de `DELETE`. Hoy no
  existe: es una brecha de disponibilidad aceptable para el alcance, pero
  vale mencionarla.

### A10 — Server-Side Request Forgery (SSRF)

El unico saliente de red es `TwilioWhatsAppSender` hacia la API de Twilio con
una URL fija (no viene de un input de usuario), asi que no hay superficie de
SSRF que explotar. Documentalo como "revisado, no aplica" en vez de omitirlo.

## Que anexar al reporte final

1. Capturas de Burp (Proxy → HTTP history) de al menos un caso por categoria
   aplicable, con la peticion y la respuesta completas.
2. La salida de `npm audit` (`frontend/`) — ya corrida localmente, ver
   seccion A06.
3. Veredicto por categoria: **Vulnerable**, **Mitigado** o **Fuera de
   alcance**, con una linea de justificacion cada uno.
4. Cualquier hallazgo real (el que sea) con su severidad y una recomendacion
   concreta de arreglo — aunque no te de tiempo de corregirlo antes de la
   expo, repórtalo con la ruta del archivo donde se corregiria.
