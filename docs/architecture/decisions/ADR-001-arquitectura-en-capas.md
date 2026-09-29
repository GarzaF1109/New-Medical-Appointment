# ADR-001: Adoptar arquitectura en capas con inversion de dependencias

## Estado
Aceptada — 2026-09-22

## Contexto

El sistema anterior (Laravel + Livewire) concentraba en los controladores la
validacion, las reglas de negocio, el acceso a datos y las llamadas a Twilio. Tres
consecuencias concretas:

1. La regla de conflicto de horario estaba **duplicada** en `AppointmentCreate` y
   `AppointmentEdit` como una consulta SQL repetida, con riesgo de divergir.
2. `WhatsAppService::sendMessage()` era un **metodo estatico**: imposible de
   sustituir por un doble, lo que obligaba a que cualquier prueba de agendado
   golpeara la red.
3. Los modelos Eloquent mezclaban datos y persistencia (ActiveRecord), de modo que
   no existia un lugar donde probar una regla de negocio sin base de datos.

La Guia de Mejores Practicas de AIVARA exige explicitamente arquitectura en cuatro
capas, inyeccion de dependencias, contratos claros entre componentes y una piramide
de pruebas con 70-80% de unitarias.

## Decision

Organizar el backend en cuatro capas —presentacion, aplicacion, dominio e
infraestructura— con la regla de que las capas superiores dependen de las
inferiores y nunca al reves.

El dominio declara **puertos** (`AppointmentRepository`, `NotificationSender`,
`Clock`) como clases base abstractas. La infraestructura los implementa. El
cableado ocurre en un unico composition root (`presentation/dependencies.py`).

## Consecuencias

**Positivas**

- El paquete `domain/` no importa SQLAlchemy, httpx ni FastAPI: sus reglas se
  prueban en milisegundos y sin E/S.
- La regla de solapamiento vive una sola vez, en `TimeSlot.overlaps()`.
- Cambiar Twilio por otro proveedor toca un archivo de infraestructura y ninguno
  de dominio o aplicacion.
- Se alcanzo 94% de cobertura global con la mayoria de pruebas siendo unitarias.

**Negativas**

- Mas archivos y mas indireccion que un CRUD directo. Para una entidad trivial es
  sobreingenieria; se justifica porque la logica de agenda **si** tiene reglas.
- Se requieren mapeadores explicitos entre filas y entidades (`mappers.py`), codigo
  que un ORM ActiveRecord ahorra.
- El equipo debe resistir la tentacion de importar SQLAlchemy desde el dominio; se
  recomienda verificarlo en la revision de codigo.

## Alternativas consideradas

- **Mantener Laravel y solo refactorizar**: se descarto porque el ORM Eloquent
  empuja hacia fat models, contrario a la separacion que pide la guia.
- **Django REST Framework**: mismo problema; el ORM de Django asume que el modelo
  es tambien la entidad de negocio.
- **CRUD de una sola capa en FastAPI**: mas rapido de escribir, pero reproduce
  exactamente el acoplamiento que motivo la migracion.
