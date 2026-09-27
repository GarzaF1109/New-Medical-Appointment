"""Puerto de reloj del sistema."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class Clock(ABC):
    """Fuente de la hora actual.

    Se abstrae el reloj para que las reglas temporales -"no agendar en el
    pasado", "recordatorios a 24 horas"- sean deterministas en las pruebas.
    """

    @abstractmethod
    def now(self) -> datetime:
        """Devuelve el instante actual."""
