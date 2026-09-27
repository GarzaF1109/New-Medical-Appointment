# Frontend — Citas Medicas

React 19 + TypeScript + Vite + TanStack Query.

## Comandos

```bash
npm install
npm run dev        # http://localhost:5173
npm test           # pruebas
npm run build      # compilacion de produccion
npx tsc -b --noEmit
```

Vite hace proxy de `/api` hacia `http://localhost:8000`. Para apuntar a otro puerto:

```bash
VITE_API_TARGET=http://localhost:8899 npm run dev
```

## Organizacion

| Carpeta | Contenido |
|---|---|
| `src/api/` | Cliente HTTP tipado, tipos del contrato y `ApiError` |
| `src/features/appointments/` | Componentes y hooks del modulo de citas |
| `src/components/` | Componentes compartidos |
| `src/lib/` | Utilidades de formato |
| `src/pages/` | Composicion de pantallas |

`src/api/client.ts` es el **unico** lugar que usa `fetch`. Todo fallo se normaliza
a `ApiError`, que conserva `status`, `code` y `details`, de modo que la interfaz
distingue un conflicto de agenda (409) de un error de validacion (422) sin
interpretar cadenas de texto.
