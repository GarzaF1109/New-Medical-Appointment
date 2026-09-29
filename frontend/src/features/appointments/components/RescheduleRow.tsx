import { useState } from "react";

import { ApiError } from "@/api/ApiError";
import type { Appointment } from "@/api/types";
import { Field } from "@/components/Field";
import { useRescheduleAppointment } from "@/features/appointments/hooks/useAppointments";
import { todayIso } from "@/lib/format";
import {
  isClean,
  maxAppointmentDateIso,
  validateAppointmentDate,
  validateRequired,
} from "@/lib/validation";

interface RescheduleRowProps {
  appointment: Appointment;
  columnCount: number;
  onDone: (message: string, ok: boolean) => void;
  onCancel: () => void;
}

/**
 * Fila expandible para reagendar una cita.
 *
 * Vive dentro de la tabla, en la fila siguiente a la cita afectada, para que el
 * usuario no pierda de vista cual esta moviendo. El conflicto de horario que
 * devuelve el backend se muestra aqui mismo.
 */
export function RescheduleRow({
  appointment,
  columnCount,
  onDone,
  onCancel,
}: RescheduleRowProps) {
  const [date, setDate] = useState(appointment.date);
  const [startTime, setStartTime] = useState(appointment.startTime.slice(0, 5));
  const [durationMinutes, setDurationMinutes] = useState(String(appointment.durationMinutes));

  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const reschedule = useRescheduleAppointment();
  const error = reschedule.error instanceof ApiError ? reschedule.error : null;

  const errors = {
    date: validateAppointmentDate(date),
    startTime: validateRequired(startTime, "La hora de inicio"),
  };
  const valid = isClean(errors);

  async function handleSave() {
    setTouched({ date: true, startTime: true });
    if (!valid) return;

    try {
      await reschedule.mutateAsync({
        id: appointment.id,
        input: {
          date,
          startTime: `${startTime}:00`,
          durationMinutes: Number(durationMinutes),
        },
      });
    } catch {
      // El detalle queda en `error` y se pinta debajo de los campos.
      return;
    }
    onDone(`Cita #${appointment.id} reagendada.`, true);
    onCancel();
  }

  return (
    <tr className="row--editing">
      <td colSpan={columnCount}>
        <div className="inline-form">
          <Field label="Fecha" required error={errors.date} touched={touched.date}>
            <input
              type="date"
              aria-required="true"
              min={todayIso()}
              max={maxAppointmentDateIso()}
              value={date}
              onChange={(e) => setDate(e.target.value)}
              onBlur={() => setTouched((c) => ({ ...c, date: true }))}
            />
          </Field>

          <Field
            label="Hora de inicio"
            required
            error={errors.startTime}
            touched={touched.startTime}
          >
            <input
              type="time"
              aria-required="true"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              onBlur={() => setTouched((c) => ({ ...c, startTime: true }))}
            />
          </Field>

          <Field label="Duracion" required>
            <select
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(e.target.value)}
            >
              <option value="30">30 minutos</option>
              <option value="60">1 hora</option>
              <option value="90">1 hora 30 minutos</option>
            </select>
          </Field>

          <div className="inline-form__actions">
            <button
              type="button"
              className="btn btn--small btn--primary"
              onClick={handleSave}
              disabled={reschedule.isPending || !valid}
            >
              {reschedule.isPending ? "Guardando…" : "Guardar"}
            </button>
            <button type="button" className="btn btn--small" onClick={onCancel}>
              Cancelar
            </button>
          </div>
        </div>

        {error && <p className="field-error">{error.message}</p>}
      </td>
    </tr>
  );
}
