"""Middleware de cabeceras de seguridad HTTP.

OWASP ZAP las marco como ausentes en la primera corrida (ver
`docs/security/owasp-zap.md`): sin autenticacion ni sesiones el riesgo es
bajo, pero son gratis de agregar y cierran clases enteras de ataque del lado
del navegador (clickjacking, sniffing de MIME, inyeccion de recursos).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

_SECURITY_HEADERS = {
    # Evita que el navegador adivine el tipo de contenido (mitiga MIME sniffing).
    "X-Content-Type-Options": "nosniff",
    # Prohibe que la API se incruste en un <iframe> de otro origen.
    "X-Frame-Options": "DENY",
    # Los endpoints son JSON puro: no necesitan camara, geolocalizacion, etc.
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    # 'same-origin' en vez de 'same-site': la API solo se consume a traves
    # del proxy de Nginx/Vite, nunca desde otro origen, y ZAP marca
    # 'same-site' como la opcion menos estricta de las tres validas.
    "Cross-Origin-Resource-Policy": "same-origin",
}

# Los endpoints JSON no sirven HTML de usuario, asi que una politica estricta
# no rompe nada. Swagger/Redoc si cargan su propio JS/CSS (del CDN o
# empaquetado), asi que quedan fuera de esta regla para no romper `/docs`.
_STRICT_CSP = "default-src 'none'; frame-ancestors 'none'"
_DOCS_PATH_PREFIXES = ("/docs", "/redoc", "/openapi.json")


def add_security_headers(app: FastAPI) -> None:
    """Agrega las cabeceras de seguridad a toda respuesta de la API."""

    @app.middleware("http")
    async def _security_headers_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        if not request.url.path.startswith(_DOCS_PATH_PREFIXES):
            response.headers.setdefault("Content-Security-Policy", _STRICT_CSP)
        return response
