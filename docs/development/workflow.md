# Flujo de trabajo

## Ramas (GitFlow modificado)

| Rama | Proposito |
|---|---|
| `main` | Codigo listo para produccion |
| `dev` | Integracion de caracteristicas |
| `feature/[ticket]-descripcion` | Nueva funcionalidad |
| `bugfix/[ticket]-descripcion` | Correccion |
| `hotfix/[ticket]-descripcion` | Correccion critica en produccion |
| `release/vX.Y.Z` | Preparacion de lanzamiento |

## Mensajes de commit

```
[MED-42] Resumen breve en presente, 50 caracteres o menos

Explicacion mas detallada ajustada a 72 caracteres. Explica el PROBLEMA
que se resuelve y POR QUE, no el COMO.

- Los puntos son aceptables
- Usar guion o asterisco seguido de espacio

Resuelve: MED-42
```

## Pull requests

1. Descripcion con el cambio y su proposito.
2. Enlace al ticket.
3. Al menos una aprobacion.
4. CI en verde (linter, tipos, pruebas con 80% de cobertura, build, Docker).
5. Atender comentarios y actualizar.
6. **Squash merge** para mantener limpio el historial.

## Lista de verificacion de revision

- [ ] Cumple SOLID y respeta la direccion de las dependencias entre capas
- [ ] **`domain/` no importa SQLAlchemy, httpx ni FastAPI**
- [ ] El codigo es DRY
- [ ] Nombres claros y descriptivos
- [ ] Manejo de errores apropiado: excepciones de negocio, no cadenas sueltas
- [ ] Casos limite cubiertos
- [ ] Pruebas unitarias presentes y en verde
- [ ] Rendimiento considerado (sin N+1)
- [ ] Seguridad considerada (sin secretos en el codigo)
- [ ] Documentacion actualizada; ADR nuevo si la decision es estructural
- [ ] Sin codigo muerto ni comentarios innecesarios

## Desarrollo guiado por pruebas

Para funcionalidad nueva:

1. Escribir la prueba que falla.
2. Escribir el minimo codigo que la hace pasar.
3. Refactorizar con las pruebas en verde.

La regla practica: **si es una regla de negocio, la prueba va en `tests/unit/` y no
toca la base de datos.** Si necesita base de datos para probarse, probablemente la
regla esta en la capa equivocada.
