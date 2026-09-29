"""Value object: franja horaria de una cita."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime, time, timedelta

from app.domain.exceptions import InvalidInputException

DEFAULT_DURATION_MINUTES = 60
# Horizonte de agenda: mas alla de dos anos una cita es un error de captura,
# no una planeacion. Acota el dano de un dedazo en el ano.
MAX_MONTHS_AHEAD = 24
MIN_DURATION_MINUTES = 15
MAX_DURATION_MINUTES = 480


@dataclass(frozen=True, slots=True)
class TimeSlot:
    """Intervalo [inicio, fin) en un dia concreto.

    Concentra la aritmetica de horarios y la regla de solapamiento que en el
    sistema anterior estaba duplicada entre `AppointmentCreate` y
    `AppointmentEdit` como una consulta SQL repetida. Al vivir aqui, la regla se
    prueba una sola vez y no puede divergir entre casos de uso (DRY).

    Attributes:
        date: Dia en que ocurre la cita.
        start_time: Hora de inicio, inclusiva.
        duration_minutes: Duracion en minutos, estrictamente positiva.
    """

    date: Date
    start_time: time
    duration_minutes: int = DEFAULT_DURATION_MINUTES

    def __post_init__(self) -> None:
        """Valida las invariantes de duracion al construir el objeto."""
        if self.duration_minutes < MIN_DURATION_MINUTES:
            raise InvalidInputException(
                f"La duracion minima de una cita es de {MIN_DURATION_MINUTES} minutos."
            )
        if self.duration_minutes > MAX_DURATION_MINUTES:
            raise InvalidInputException(
                f"La duracion maxima de una cita es de {MAX_DURATION_MINUTES} minutos."
            )
        if self._end_datetime().date() != self.date:
            raise InvalidInputException("La cita no puede extenderse al dia siguiente.")

    @property
    def end_time(self) -> time:
        """Hora de fin, exclusiva. Derivada, nunca almacenada por separado."""
        return self._end_datetime().time()

    def _start_datetime(self) -> datetime:
        return datetime.combine(self.date, self.start_time)

    def _end_datetime(self) -> datetime:
        return self._start_datetime() + timedelta(minutes=self.duration_minutes)

    def overlaps(self, other: TimeSlot) -> bool:
        """Indica si esta franja se traslapa con otra.

        Los intervalos son semiabiertos, asi que dos citas contiguas -una que
        termina a las 10:00 y otra que empieza a las 10:00- NO se traslapan.

        Args:
            other: La franja contra la cual comparar.

        Returns:
            True si comparten al menos un instante.
        """
        if self.date != other.date:
            return False
        return (
            self._start_datetime() < other._end_datetime()
            and other._start_datetime() < self._end_datetime()
        )

    def is_too_far_ahead(self, now: datetime) -> bool:
        """Indica si la franja cae mas alla del horizonte de agenda."""
        target = self.date.year * 12 + self.date.month
        reference = now.year * 12 + now.month
        return target - reference > MAX_MONTHS_AHEAD

    def is_in_the_past(self, now: datetime) -> bool:
        """Indica si la franja ya comenzo respecto al instante dado.

        Args:
            now: Instante de referencia. Se inyecta en lugar de leer el reloj
                del sistema para que las pruebas sean deterministas.
        """
        return self._start_datetime() < now
