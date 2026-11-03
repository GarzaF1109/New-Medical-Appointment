# Pruebas E2E — Playwright

Cubre el punto (5) del enunciado. Vive en `frontend/e2e/` porque usa el mismo
`package.json`/`node_modules` que el resto del frontend; no es un proyecto
aparte.

## Que cubre

| Archivo | Casos |
|---|---|
| `tests/patients.spec.ts` | Alta, validacion de nombre con digitos, edicion de telefono, baja sin citas vigentes |
| `tests/doctors.spec.ts` | Alta, validacion de formato de cedula, baja sin citas vigentes |
| `tests/appointments.spec.ts` | Camino feliz completo (agendar → confirmar → reagendar → cancelar → eliminar) y el 409 de traslape de horario |

El camino feliz de citas es el caso mas importante: ejercita la regla de
negocio central del sistema (`TimeSlot.overlaps()`) a traves de toda la pila,
desde el formulario de React hasta la base de datos y de vuelta.

## Como correrlas

Contra el servidor de desarrollo (rapido, para iterar):

```bash
# Terminal 1
cd backend && uvicorn app.main:app --reload
# Terminal 2
cd frontend && npm run dev
# Terminal 3
cd frontend && npm run test:e2e
```

Contra la imagen que realmente se entrega (lo que corre en CI):

```bash
docker compose up --build -d
cd frontend && E2E_BASE_URL=http://localhost:8080 npm run test:e2e
docker compose down
```

`npm run test:e2e:ui` abre el modo interactivo de Playwright (util para ver
cada paso mientras se escribe un caso nuevo).

## Decisiones de diseño de la suite

- **Nombres unicos sin digitos.** `validateName` rechaza cualquier numero en
  un nombre de persona (ver `lib/validation.ts`), asi que el helper
  `uniqueSuffix()` genera un sufijo de solo letras en vez de usar un
  timestamp crudo. Un sufijo numerico habria invalidado el formulario antes
  de que el test llegara a enviarlo.
- **Selectores por rol/label accesibles, no por clase CSS.** Cada campo usa
  `<label>` envolviendo su `<input>` (`components/Field.tsx`), asi que
  `getByLabel` funciona sin agregar `data-testid` artificiales. La excepcion
  es el filtro de la agenda (`AppointmentFilters`), que repite la etiqueta
  "Doctor" del formulario de alta: los specs que tocan el formulario acotan
  la busqueda con `page.locator("form", { hasText: "Agendar cita" })` para no
  chocar con el filtro.
- **Base de datos compartida entre corridas.** La suite no resetea la base
  de datos entre ejecuciones (no hay un endpoint de "seed" ni de limpieza).
  Por eso cada test genera sus propios nombres unicos en vez de asumir un
  catalogo vacio — corren bien aunque la base ya tenga datos de corridas
  anteriores o de uso manual.
- **Un solo worker (`workers: 1`).** Varios tests comparten catalogo de
  pacientes/doctores recien creados dentro del mismo archivo; correrlos en
  paralelo arriesgaria condiciones de carrera contra la misma base de datos
  compartida sin aislamiento transaccional entre tests.
