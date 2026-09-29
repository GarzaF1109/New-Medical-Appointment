# ADR-006: La validacion vive en el dominio y se refleja en los bordes

## Estado
Aceptada — 2026-09-29

## Contexto

Al ampliar el sistema con el CRUD de Pacientes y Doctores aparecieron campos de
entrada nuevos —nombre, fecha de nacimiento, telefono, especialidad, cedula— y
con ellos la pregunta de **donde** comprobarlos. El codigo existente respondia de
tres formas distintas a la vez, y las tres tenian huecos:

1. **En el esquema de Pydantic**, como `min_length` y `max_length`. Cubria la
   forma del dato pero no su significado: `fullName: "12345678"` pasaba, igual
   que `"!!!@@@###"` y `"<script>alert</script>"`.

2. **En el value object**, pero mal. `PhoneNumber.parse()` normalizaba antes de
   validar: hacia `re.sub(r"\D", "", raw)` para quitar los separadores humanos y
   solo despues comprobaba longitud. El efecto es que **borraba en silencio**
   cualquier caracter no numerico. `"8112345678abc"` se guardaba tan tranquilo
   como `+5218112345678` (commit `855f34f`). El usuario no se enteraba de que su
   captura habia sido alterada.

3. **En ningun lado.** La especialidad aceptaba `"99999"`, el motivo de consulta
   aceptaba `"!!!!!!!!!!!!"` y la fecha de una cita aceptaba el ano 2099.

Ademas, el frontend no validaba nada mas alla de los atributos `required` y
`minLength` de HTML, de modo que cada captura invalida costaba una peticion y
devolvia un mensaje pensado para un desarrollador, no para un recepcionista.

El problema de fondo no era la falta de comprobaciones sino la **ausencia de una
regla sobre donde ponerlas**. Sin esa regla, cada campo nuevo repetiria la
loteria de las tres opciones anteriores.

## Decision

**Las reglas de validacion son invariantes del dominio y viven en `domain/`.**
Las demas capas las reutilizan; no las reimplementan.

Concretamente:

- `domain/text_rules.py` concentra las reglas de texto compartidas:
  `validate_person_name`, `validate_free_text` y `validate_phone_charset`.
  Las entidades `Patient`, `Doctor` y `Appointment` las invocan desde sus
  constructores, de modo que **no existe una instancia invalida**: si el objeto
  se construyo, sus datos cumplen las reglas.

- **La capa de presentacion delega, no repite.** Los esquemas de Pydantic usan
  `field_validator` que llama a las mismas funciones del dominio y convierte
  `InvalidInputException` en `ValueError`. Esto da lo mejor de ambos mundos: el
  `422` nombra el campo culpable en `details[]` —porque Pydantic sabe de que
  campo viene— y el mensaje es el que escribio el dominio, en espanol y dirigido
  al usuario (commit `2cfccac`).

- **El frontend es un espejo, no una autoridad.** `lib/validation.ts` replica las
  reglas para dar respuesta inmediata y no gastar una peticion en algo que el
  navegador puede saber solo. Pero nunca decide: lo que el backend rechaza se
  muestra tal cual, y el frontend no intenta adelantarse a lo que no puede
  conocer —el traslape de horario, sobre todo.

- **Validar antes de normalizar, nunca al reves.** `PhoneNumber.parse()` ahora
  comprueba el juego de caracteres *antes* de quitar los separadores. Los
  guiones y espacios se siguen aceptando porque la gente escribe
  `(81) 1234-5678`; las letras se rechazan con un error explicito.

La linea divisoria entre las dos ultimas viñetas es la que resuelve la pregunta
"donde vive cada validacion": **el navegador corta lo que puede predecir por si
solo** (una fecha de nacimiento futura, un nombre con digitos); **el backend es
la autoridad de todo lo demas**, y en exclusiva de lo que depende del estado
compartido.

## Consecuencias

**Positivas**

- Una regla tiene una sola definicion. Cambiar el juego de caracteres de un
  nombre es editar `text_rules.py`; la API y la persistencia lo heredan.
- Las reglas se prueban sin levantar nada: `test_text_rules.py` son pruebas
  unitarias puras, sin HTTP ni base de datos.
- Los mensajes de error son legibles. Antes el usuario recibia
  `"String should match pattern '^[+0-9 ().\\-]+$'"`; ahora recibe
  `"El telefono no puede contener letras."`.
- Una validacion es imposible de olvidar al agregar un punto de entrada nuevo:
  una importacion masiva o una siembra que construya un `Patient` obtiene las
  mismas comprobaciones gratis, sin pasar por HTTP.
- El frontend deja de gastar peticiones en errores previsibles, y el boton de
  enviar se deshabilita mientras haya un campo invalido.

**Negativas**

- **Las reglas estan duplicadas entre Python y TypeScript.** Es la concesion mas
  incomoda de esta decision: `validate_person_name` y `validateName` pueden
  divergir si alguien toca una sola. Se acepta a conciencia porque la alternativa
  —generar el validador de TypeScript desde el esquema de OpenAPI— añade un paso
  de compilacion que no se justifica con seis campos. **Si el numero de campos
  crece, esta decision debe revisarse.**
- El dominio gana un modulo que no modela un concepto del negocio, sino un
  utilitario de texto. Es deuda conceptual menor, tolerada por evitar la
  duplicacion entre tres entidades.
- Validar en el constructor de una entidad inmutable significa que un dato
  invalido lanza en el momento de construir, no al guardar. Es lo deseable, pero
  obliga a envolver la construccion en `try` en los casos de uso de edicion.

## Alternativas consideradas

- **Solo Pydantic, con `pattern` y longitudes.** Es lo mas corto de escribir y
  fue el punto de partida. Se descarto por dos razones: deja el dominio
  desprotegido frente a cualquier entrada que no venga por HTTP, y sus mensajes
  de error exponen la expresion regular al usuario final.

- **Solo el dominio, sin tocar los esquemas.** Funciona y mantiene una sola
  definicion, pero el `422` resultante no puede decir *que* campo fallo: el
  dominio lanza una excepcion con un mensaje, no con la ruta del campo. El
  frontend no podria pintar el error junto al input correspondiente.

- **Un motor de validacion declarativo compartido** (un JSON de reglas que
  consuman Python y TypeScript). Elimina la duplicacion, pero introduce un
  formato propio que hay que interpretar en dos lenguajes y que nadie conoce.
  Desproporcionado para el tamaño actual.

- **Confiar solo en el frontend.** Descartada de plano: cualquiera puede llamar
  a la API con `curl`, como de hecho se hizo para encontrar el defecto del
  telefono.

## Referencias

- `backend/src/app/domain/text_rules.py`
- `backend/src/app/presentation/api/v1/schemas/people.py`
- `frontend/src/lib/validation.ts`
- Commits `c0eb313`, `855f34f`, `341b1c3`, `2cfccac`, `5cf5adf`
