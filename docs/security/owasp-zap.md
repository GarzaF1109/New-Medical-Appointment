# OWASP ZAP — analisis automatizado

Este documento cubre el punto (3) del enunciado. ZAP corre de dos formas
complementarias contra la pila ya construida (`docker compose up --build`):

1. **API scan** (`zap-api-scan.py`), dirigido por el `openapi.json` que FastAPI
   genera automaticamente. Recorre cada endpoint documentado —incluidos los
   que la interfaz nunca llama directamente, como `PATCH /appointments/{id}`—
   y prueba variantes de inyeccion, fuzzing de parametros y cabeceras.
2. **Baseline scan** (`zap-baseline.py`), un crawling pasivo + unas pocas
   pruebas activas de bajo riesgo contra la interfaz en `http://localhost:8080`.
   Encuentra lo que un usuario normal expondria: cookies sin `Secure`,
   cabeceras de seguridad ausentes, mixed content, etc.

No se eligio el *full active scan* porque es agresivo (intenta explotar, no
solo detectar) y en una app sin autenticacion con datos de prueba compartidos
puede dejar el catalogo de pacientes/doctores en un estado inconsistente justo
antes de una demo. El baseline + API scan cubren el mismo catalogo de
categorias OWASP sin ese riesgo.

## Como correrlo

```bash
docker compose up --build -d
./ops/zap/run-zap.sh
```

El script espera a que `/health` responda, corre ambos escaneos con la imagen
oficial `zaproxy/zap-stable`, y deja los reportes en
`docs/security/zap-reports/`:

- `api-report.html` / `api-report.json`
- `baseline-report.html` / `baseline-report.json`

Esos reportes **no se versionan** (cambian en cada corrida y pueden pesar
varios MB); el directorio tiene un `.gitkeep` para que exista en el repo, y
`run-zap.sh` es reproducible en cualquier maquina con Docker.

## Reglas y falsos positivos

`ops/zap/rules.tsv` es la lista de alertas que el equipo decidio degradar
(`IGNORE` o `WARN`) a conciencia, cada una con su razon. Esta vacio a
proposito: en la primera corrida, cualquier hallazgo debe revisarse, no
descartarse de entrada. Si aparece un falso positivo real (por ejemplo, una
alerta de "Cookie sin atributo Secure" en un ambiente HTTP de desarrollo que
nunca correra asi en produccion), se agrega ahi con un comentario explicando
por que no aplica — nunca se silencia sin dejar rastro escrito.

Formato de una fila (ver comentario en el propio archivo):

```
10063	WARN	# Cabecera X-Content-Type ausente solo en /docs de Swagger, fuera de alcance
```

## Por que "reporte, no bloqueo"

El job de CI (`security-zap` en `.github/workflows/ci.yml`) publica ambos
reportes como artefacto pero **no hace fallar el pipeline**. La razon es
practica: ZAP contra una API sin autenticacion y con datos sembrados por
pruebas anteriores genera alertas de severidad media que requieren juicio
humano (¿es un hallazgo real o ruido del entorno de prueba?). Bloquear el
build con eso habria entrenado al equipo a ignorar el job entero. Reportar sin
bloquear mantiene la señal visible sin volverla un obstaculo para cada PR.

Si en el futuro se agrega autenticacion real, vale la pena revisar esta
decision: un hallazgo "High" contra un endpoint que si maneja sesiones ya no
es ruido, y ahi si se justifica bloquear el pipeline.

## Resultado: antes y despues (2026-11-02)

Para referencia — y como evidencia real que se puede mostrar en la expo en
vez de solo la metodologia. Mismo dia, misma maquina, tres corridas:

| Scan | Corrida | FAIL-NEW | WARN-NEW | PASS |
|---|---|---|---|---|
| API (`zap-api-scan.py`) | Antes | 0 | 3 | 118 |
| API (`zap-api-scan.py`) | Despues | 0 | **0** | 120 |
| Baseline (`zap-baseline.py`) | Antes | 0 | 8 | 60 |
| Baseline (`zap-baseline.py`) | Despues | 0 | **3** | 65 |

Nada en severidad alta, ni antes ni despues. Dos hallazgos reales en la
primera corrida, ambos corregidos:

1. **Cabeceras de seguridad ausentes** (`X-Content-Type-Options`,
   `Content-Security-Policy`, `Cross-Origin-Resource-Policy`,
   anti-clickjacking, `Permissions-Policy`). Se corrigio con un middleware
   nuevo en FastAPI (`app/presentation/api/security_headers.py`) y
   directivas `add_header` en `frontend/nginx.conf` — incluyendo COOP y
   COEP, que ZAP tampoco encontraba. La CSP del backend excluye a proposito
   `/docs` y `/redoc`: Swagger carga su propio JS/CSS y una politica
   estricta ahi lo hubiera roto.

2. **Un `500` real con un ID numerico fuera de rango**: ZAP probo
   `GET /api/v1/patients/{id}` con un entero gigantesco
   (`4792862250242561607`, mayor al rango de `INTEGER` de Postgres) y el
   backend respondio `500` en vez de `404`. El cuerpo de la respuesta
   **no** filtraba el detalle tecnico (la regla "Application Error
   Disclosure" ya pasaba en verde), asi que no era una fuga de informacion,
   pero si un error no controlado: el router recibia el ID como `int` de
   Python (sin limite) y SQLAlchemy lo pasaba tal cual a Postgres, que lo
   rechazaba con un error de rango que el manejador generico
   (`presentation/api/errors.py`) atrapaba como `500`. Se corrigio con un
   tipo compartido `ResourceId` (`app/presentation/api/path_params.py`) que
   acota todo ID de ruta a `[1, 2_147_483_647]`: ahora responde `422` antes
   de llegar a la base de datos. Se verifico con `curl` y con Playwright
   (9/9 sigue en verde tras el cambio).

Las 3 advertencias que quedan en el baseline despues de corregir se
revisaron y se degradaron a conciencia en `ops/zap/rules.tsv`: cache de
assets con hash (a proposito, es cache-busting), `style-src 'unsafe-inline'`
(los componentes de React escriben `style={{...}}`) y un aviso meramente
informativo de que la interfaz es una SPA moderna. Ninguna es un hallazgo
de seguridad real.

## Relacion con el resto del plan de seguridad

- El analisis **dinamico manual** (Burp) vive en
  [`burp-manual-testing.md`](burp-manual-testing.md) y es complementario: ZAP
  cubre amplitud (todos los endpoints, de forma repetible); Burp cubre
  profundidad (un analista decidiendo que tamperar caso por caso, como
  condiciones de carrera en el agendado).
- La decision de por que el pipeline no bloquea en hallazgos de ZAP, y por que
  se eligio baseline+API en vez de full active scan, queda registrada en
  [ADR-007](../architecture/decisions/ADR-007-estrategia-de-pruebas-de-seguridad-y-e2e.md).
