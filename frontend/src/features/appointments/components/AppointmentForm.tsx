import { useState } from "react";

import { ApiError } from "@/api/ApiError";
import type { Doctor, Patient } from "@/api/types";
import { Alert } from "@/components/Alert";
import { useScheduleAppointment } from "@/features/appointments/hooks/useAppointments";
import { todayIso } from "@/lib/format";

const MIN_REASON_LENGTH = 10;

interface AppointmentFormProps {
  patients: Patient[];
  doctors: Doctor[];
  onScheduled: (message: string) => void;
}

const EMPTY_FORM = {
  patientId: "",
  doctorId: "",
  date: "",
  startTime: "",
  durationMinutes: "60",
  reason: "",
};

/**
 * Formulario de agendado.
 *
 * La validacion de formato se hace aqui para dar respuesta inmediata, pero la
 * autoridad sigue siendo el backend: los errores que devuelve se muestran tal
 * cual, incluido el conflicto de horario que el navegador no puede predecir.
 */
export function AppointmentForm({ patients, doctors, onScheduled }: AppointmentFormProps) {
  const [form, setForm] = useState(EMPTY_FORM);
  const schedule = useScheduleAppointment();
  const error = schedule.error instanceof ApiError ? schedule.error : null;

  function update(field: keyof typeof EMPTY_FORM, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    let result;
    try {
      result = await schedule.mutateAsync({
        patientId: Number(form.patientId),
        doctorId: Number(form.doctorId),
        date: form.date,
        startTime: `${form.startTime}:00`,
        durationMinutes: Number(form.durationMinutes),
        reason: form.reason.trim(),
      });
    } catch {
      // El error ya quedo en `schedule.error` y se muestra en el aviso de
      // arriba; el formulario conserva lo capturado para poder corregirlo.
      return;
    }

    setForm(EMPTY_FORM);
    onScheduled(
      result.notificationSent
        ? `Cita registrada. Se notifico a ${result.patientName} por WhatsApp.`
        : `Cita registrada, pero no se pudo notificar a ${result.patientName}.`,
    );
  }

  const reasonTooShort =
    form.reason.trim().length > 0 && form.reason.trim().length < MIN_REASON_LENGTH;

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Agendar cita</h2>

      {error && (
        <Alert variant={error.isConflict ? "warning" : "error"} title={error.code}>
          {error.message}
        </Alert>
      )}

      <div className="grid">
        <label>
          Paciente
          <select
            required
            value={form.patientId}
            onChange={(e) => update("patientId", e.target.value)}
          >
            <option value="">Seleccione un paciente</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.fullName}
                {patient.phone ? "" : " (sin telefono)"}
              </option>
            ))}
          </select>
        </label>

        <label>
          Doctor
          <select
            required
            value={form.doctorId}
            onChange={(e) => update("doctorId", e.target.value)}
          >
            <option value="">Seleccione un doctor</option>
            {doctors.map((doctor) => (
              <option key={doctor.id} value={doctor.id}>
                {doctor.displayName} — {doctor.speciality}
              </option>
            ))}
          </select>
        </label>

        <label>
          Fecha
          <input
            type="date"
            required
            min={todayIso()}
            value={form.date}
            onChange={(e) => update("date", e.target.value)}
          />
        </label>

        <label>
          Hora de inicio
          <input
            type="time"
            required
            value={form.startTime}
            onChange={(e) => update("startTime", e.target.value)}
          />
        </label>

        <label>
          Duracion
          <select
            value={form.durationMinutes}
            onChange={(e) => update("durationMinutes", e.target.value)}
          >
            <option value="30">30 minutos</option>
            <option value="60">1 hora</option>
            <option value="90">1 hora 30 minutos</option>
          </select>
        </label>
      </div>

      <label>
        Motivo de la consulta
        <textarea
          required
          rows={3}
          minLength={MIN_REASON_LENGTH}
          placeholder="Describa el motivo con al menos 10 caracteres"
          value={form.reason}
          onChange={(e) => update("reason", e.target.value)}
        />
        {reasonTooShort && (
          <small className="field-error">
            Faltan {MIN_REASON_LENGTH - form.reason.trim().length} caracteres.
          </small>
        )}
      </label>

      <button type="submit" className="btn btn--primary" disabled={schedule.isPending}>
        {schedule.isPending ? "Agendando…" : "Agendar cita"}
      </button>
    </form>
  );
}
