"""Implementacion del puerto de reloj basada en el reloj del sistema."""

from __future__ import annotations

from datetime import datetime

from app.domain.ports.clock import Clock


class SystemClock(Clock):
    """Devuelve la hora real del servidor."""

    def now(self) -> datetime:
        return datetime.now()
