# ADR-002: FastAPI para el backend y React para el frontend

## Estado
Aceptada — 2026-09-22

## Contexto

La migracion exige separar backend y frontend en un monorepo. La guia AIVARA pide
documentacion OpenAPI sincronizada con la implementacion, respuestas de error con
una forma canonica y ejemplos de codigo que la guia misma presenta **en Python**
(docstrings, instrumentacion OpenTelemetry, pruebas unitarias).

## Decision

- **Backend**: Python 3.12 + FastAPI + SQLAlchemy 2.0 + Pydantic v2.
- **Frontend**: React 19 + TypeScript + Vite + TanStack Query.
- **Monorepo** con `backend/` y `frontend/` como raices independientes.

## Consecuencias

**Positivas**

- FastAPI **genera OpenAPI automaticamente** desde los esquemas Pydantic: el
  requisito de documentacion de API se cumple sin mantener un archivo aparte que
  se desincronice.
- Pydantic produce errores de validacion con lista de campos, casi identicos al
  formato `{status, code, message, details[]}` que fija la guia; solo hizo falta
  un manejador que los reenvuelva.
- TypeScript en el frontend da un contrato tipado que refleja el de la API.
- El equipo ya conoce FastAPI por trabajos previos del curso.

**Negativas**

- Dos lenguajes y dos cadenas de herramientas que mantener.
- Los tipos del frontend se escriben a mano y pueden desfasarse del OpenAPI. Si el
  contrato crece, conviene generarlos con `openapi-typescript`.

## Alternativas consideradas

- **NestJS + Next.js**: un solo lenguaje y DI de fabrica, pero obligaria a traducir
  todos los ejemplos de la guia y tiene mayor curva de aprendizaje.
- **Spring Boot + Angular**: el mas riguroso, descartado por ceremonia y tiempo de
  arranque.
