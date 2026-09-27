# ADR-003: Derivar `end_time` y gobernar el esquema con Alembic

## Estado
Aceptada — 2026-09-22

## Contexto

La tabla `appointments` del sistema anterior almacenaba `start_time`, `end_time` **y**
`duration` como tres columnas independientes. Nada garantizaba su coherencia: un
`UPDATE` que tocara solo `start_time` dejaba las otras dos mintiendo.

Ademas, el esquema se creaba con migraciones de Laravel, que no existen aqui.

## Decision

1. Persistir unicamente `start_time` y `duration_minutes`. `end_time` es una
   **propiedad derivada** de `TimeSlot`, calculada al vuelo y expuesta en la API.
2. Gobernar el esquema con **Alembic** en entornos desplegados. `create_schema()`
   —que usa `Base.metadata.create_all()`— queda reservada para desarrollo local y
   pruebas.

## Consecuencias

**Positivas**

- Es imposible que la hora de fin contradiga a la de inicio: solo hay una fuente
  de verdad.
- La API sigue devolviendo `endTime`, asi que el cliente no nota la diferencia.
- Alembic da migraciones versionadas y reversibles.

**Negativas**

- Filtrar por hora de fin directamente en SQL requiere calcularla en la consulta.
  Hoy no hace falta: los conflictos se resuelven en memoria sobre la agenda del dia.
- `create_all()` y Alembic pueden divergir si alguien agrega una columna al modelo
  sin generar la migracion. Debe verificarse en la revision de codigo.

## Alternativas consideradas

- **Conservar las tres columnas y sincronizarlas con un trigger**: mueve la regla
  de negocio a la base de datos, donde es invisible para las pruebas unitarias.
- **Columna generada de PostgreSQL**: resuelve la coherencia pero ata el diseno a
  un motor concreto y complica las pruebas en SQLite.
