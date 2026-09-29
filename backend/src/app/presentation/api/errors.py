"""Excepciones HTTP y traduccion desde las excepciones de negocio.

La guia AIVARA distingue dos familias: las de negocio (agnosticas al
transporte) y las ad-hoc de los endpoints. Este modulo es la frontera entre
ambas y el unico lugar del sistema que conoce ambos vocabularios.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    BusinessException,
    ConflictException,
    InvalidInputException,
    NotFoundException,
)

logger = logging.getLogger(__name__)

# Se usa el literal porque Starlette renombro la constante entre versiones.
HTTP_422_UNPROCESSABLE_CONTENT = 422


class APIException(Exception):
    """Clase base para las excepciones de la capa REST."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class BadRequestHTTP(APIException):
    """Mapea a HTTP 400 Bad Request."""

    def __init__(self, message: str = "Solicitud invalida.") -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, "BAD_REQUEST", message)


class UnauthorizedHTTP(APIException):
    """Mapea a HTTP 401 Unauthorized."""

    def __init__(self, message: str = "Autenticacion requerida.") -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", message)


class ForbiddenHTTP(APIException):
    """Mapea a HTTP 403 Forbidden."""

    def __init__(self, message: str = "No tiene permisos suficientes.") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "FORBIDDEN", message)


class NotFoundHTTP(APIException):
    """Mapea a HTTP 404 Not Found."""

    def __init__(self, message: str = "Recurso no encontrado.") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "NOT_FOUND", message)


class ConflictHTTP(APIException):
    """Mapea a HTTP 409 Conflict."""

    def __init__(
        self, message: str = "La solicitud entra en conflicto con el estado actual."
    ) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "CONFLICT", message)


class UnprocessableEntityHTTP(APIException):
    """Mapea a HTTP 422 Unprocessable Entity."""

    def __init__(self, message: str = "Los datos enviados no son procesables.") -> None:
        super().__init__(HTTP_422_UNPROCESSABLE_CONTENT, "VALIDATION_ERROR", message)


def _error_body(
    *, status_code: int, code: str, message: str, details: list[dict] | None = None
) -> dict:
    """Construye el cuerpo de error en el formato que fija la guia."""
    body: dict = {"status": status_code, "code": code, "message": message}
    if details:
        body["details"] = details
    return body


# Traduccion de cada excepcion de negocio a su equivalente HTTP.
_BUSINESS_TO_HTTP: dict[type[BusinessException], int] = {
    InvalidInputException: HTTP_422_UNPROCESSABLE_CONTENT,
    NotFoundException: status.HTTP_404_NOT_FOUND,
    ConflictException: status.HTTP_409_CONFLICT,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Instala los manejadores de error de la aplicacion.

    Garantiza que toda respuesta de error -de negocio, de validacion o
    inesperada- comparta la misma forma JSON.
    """

    @app.exception_handler(APIException)
    async def _handle_api_exception(_: Request, exc: APIException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(status_code=exc.status_code, code=exc.code, message=exc.message),
        )

    @app.exception_handler(BusinessException)
    async def _handle_business_exception(_: Request, exc: BusinessException) -> JSONResponse:
        status_code = _BUSINESS_TO_HTTP.get(type(exc), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(
            status_code=status_code,
            content=_error_body(status_code=status_code, code=exc.code, message=exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"][1:]) or "body",
                # Pydantic antepone "Value error, " a los mensajes de los
                # validadores propios; al usuario no le dice nada.
                "message": error["msg"].removeprefix("Value error, "),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            content=jsonable_encoder(
                _error_body(
                    status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                    code="VALIDATION_ERROR",
                    message="Datos de entrada invalidos.",
                    details=details,
                )
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        # El detalle tecnico va a la bitacora; al cliente solo un mensaje neutro.
        logger.exception("Error no controlado: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="INTERNAL_ERROR",
                message="Ocurrio un error interno. Intentelo de nuevo mas tarde.",
            ),
        )
