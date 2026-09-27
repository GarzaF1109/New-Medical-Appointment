"""Excepciones de la capa de dominio.

Siguiendo la guia AIVARA, las excepciones de negocio son independientes del
protocolo de transporte: no conocen codigos HTTP. La traduccion a HTTP ocurre
en la capa de presentacion (`presentation.api.errors`).
"""


class BusinessException(Exception):
    """Clase base para todas las excepciones de logica de negocio."""

    code = "BUSINESS_ERROR"

    def __init__(self, message: str = "Error de negocio.") -> None:
        super().__init__(message)
        self.message = message


class InvalidInputException(BusinessException):
    """Se lanza cuando la entrada es semanticamente incorrecta."""

    code = "INVALID_INPUT"

    def __init__(self, message: str = "Los datos proporcionados no son validos.") -> None:
        super().__init__(message)


class NotFoundException(BusinessException):
    """Se lanza cuando una entidad concreta no puede encontrarse."""

    code = "NOT_FOUND"

    def __init__(self, entity_type: str, entity_id: object) -> None:
        super().__init__(f"{entity_type} con ID {entity_id} no encontrado.")
        self.entity_type = entity_type
        self.entity_id = entity_id


class ConflictException(BusinessException):
    """Se lanza cuando una operacion viola una restriccion o un estado."""

    code = "CONFLICT"

    def __init__(
        self, message: str = "La operacion entra en conflicto con el estado actual."
    ) -> None:
        super().__init__(message)
