# ADR-007: Estrategia de analisis de seguridad y pruebas E2E

## Estado
Aceptada — 2026-11-02

## Contexto

El curso exige demostrar seis practicas sobre el mismo proyecto: decisiones
arquitectonicas, stack tecnologico, analisis estatico (OWASP ZAP), analisis
dinamico (Burp), pruebas E2E (Playwright) y automatizacion. Las dos primeras
ya estaban cubiertas por los ADR-001 a 006 y por el README. Faltaban las
otras cuatro, y cada una traia una decision real que tomar, no solo
"instalar la herramienta":

1. **ZAP tiene varios modos** (baseline, full active scan, API scan dirigido
   por contrato) con compromisos distintos entre cobertura y riesgo de dejar
   datos de prueba en un estado roto.
2. **Burp es una herramienta interactiva**, no un paso de CI. Automatizarlo
   no tiene sentido; lo que si se puede preparar es *que* probar, para que la
   sesion con el profesor no se improvise endpoint por endpoint.
3. **Playwright necesita decidir contra que corre**: el servidor de
   desarrollo de Vite, o la imagen de produccion servida por Nginx a traves
   de `docker compose`. Son superficies distintas (proxy de Vite vs. Nginx
   real).
4. **Automatizar todo en CI tiene un costo**: un escaneo de seguridad que
   bloquea cada PR por hallazgos que requieren criterio humano entrena al
   equipo a ignorarlo o a saltarselo con `--no-verify`.

## Decision

### ZAP: baseline + API scan dirigido por OpenAPI, nunca full active scan

`zap-api-scan.py` contra `http://backend:8000/openapi.json` prueba cada
endpoint que FastAPI documenta —incluidos los que la UI nunca llama
directo, como `PATCH /appointments/{id}`—, y `zap-baseline.py` contra la
interfaz real en `:8080` cubre lo que ve un usuario (cabeceras, cookies,
mixed content). Se descarta el *full active scan* porque intenta explotar
activamente contra una base de datos compartida sin autenticacion: dejaria
el catalogo de pacientes/doctores en un estado inconsistente justo antes de
una demo, a cambio de hallazgos que el baseline+API ya cubren en su mayoria.
Ver [`docs/security/owasp-zap.md`](../../security/owasp-zap.md).

### Burp: checklist por escrito, ejecucion manual

No se automatiza. Se preparo
[`docs/security/burp-manual-testing.md`](../../security/burp-manual-testing.md)
mapeando el Top 10 de OWASP a los endpoints reales del proyecto —con enfasis
en lo que **si** aplica a este sistema (la condicion de carrera del
agendado, la revalidacion del reagendado) y una nota explicita de lo que
**no** aplica por diseño (A07, sin autenticacion) para no fingir un hallazgo
donde solo hay una limitacion de alcance conocida.

### Playwright: contra la imagen de Docker, no contra Vite

La suite vive en `frontend/e2e/` y por defecto apunta a
`http://localhost:5173` (Vite) para iterar rapido en local, pero en CI corre
con `E2E_BASE_URL=http://localhost:8080` contra `docker compose up --build`.
Es deliberado: Vite sirve los archivos directo y proxea `/api` en su propio
proceso de Node; Nginx (lo que corre en produccion, `frontend/nginx.conf`)
sirve estaticos y rutea distinto. Probar solo contra Vite daria una falsa
sensacion de cobertura sobre un camino que la produccion no usa.

### CI: ZAP reporta, nunca bloquea; Playwright si bloquea

El job `security-zap` sube los reportes como artefacto con
`continue-on-error: true` explicito. El job `e2e` **si** hace fallar el
pipeline si una prueba de Playwright rompe: una prueba E2E que falla
describe una regresion funcional concreta (ya no se puede agendar, el 409
dejo de dispararse), mientras que una alerta de ZAP casi siempre requiere
que alguien decida si es ruido del entorno de prueba o un hallazgo real
(ver la seccion "Por que reporte, no bloqueo" en `owasp-zap.md`).

## Consecuencias

**Positivas**

- Los seis puntos del enunciado quedan cubiertos con artefactos
  reproducibles: cualquiera corre `./ops/zap/run-zap.sh` o
  `npm run test:e2e` y obtiene el mismo resultado que CI.
- El checklist de Burp convierte la sesion manual en algo que se puede
  terminar en el tiempo de una expo, con casos concretos en vez de
  improvisacion.
- Las pruebas E2E corren contra la misma imagen que se entrega, no contra un
  servidor de desarrollo que nadie despliega.

**Negativas**

- Dos jobs nuevos en CI (`e2e`, `security-zap`) alargan el tiempo total del
  pipeline porque cada uno reconstruye las imagenes de Docker desde cero.
  Se acepta porque el proyecto es pequeño (tres modulos) y el tiempo
  absoluto sigue siendo de minutos, no de decenas de minutos.
- `ops/zap/rules.tsv` empieza vacio a proposito: la primera corrida en CI
  va a mostrar alertas sin triar. Es el costo de no decidir falsos positivos
  sin haberlos visto al menos una vez.
- El checklist de Burp requiere que una persona lo ejecute; no hay
  verificacion automatica de que efectivamente se haya corrido antes de la
  expo. Se acepta porque automatizarlo seria, de nuevo, hacer un ZAP
  activo con otro nombre.

## Alternativas consideradas

- **Full active scan de ZAP en vez de baseline+API.** Mas cobertura en
  papel, pero con el riesgo de romper el catalogo de datos de prueba
  descrito arriba. Descartado para el alcance de un proyecto escolar sin
  entorno de staging desechable.
- **Automatizar Burp con su API/extensiones (Burp Suite Enterprise o
  scripts de Intruder guardados).** Fuera de alcance: la licencia community
  no expone esa automatizacion, y el enunciado pide explicitamente un
  analisis manual separado del automatizado.
- **Correr Playwright contra Vite tambien en CI**, por ser mas rapido de
  levantar que `docker compose`. Descartado porque no prueba el artefacto
  que realmente se entrega (la imagen de Nginx).
- **Bloquear el pipeline en cualquier hallazgo de ZAP con severidad
  "High".** Se considero y se dejo documentado como el primer punto a
  revisar si el proyecto agrega autenticacion real (ver
  `owasp-zap.md`), porque ahi un hallazgo alto si tiene un impacto claro y
  accionable.

## Referencias

- `ops/zap/run-zap.sh`, `ops/zap/rules.tsv`
- `frontend/e2e/`
- `docs/security/owasp-zap.md`, `docs/security/burp-manual-testing.md`
- `.github/workflows/ci.yml` (jobs `e2e`, `security-zap`)
