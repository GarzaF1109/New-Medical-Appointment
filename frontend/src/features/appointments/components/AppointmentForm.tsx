import { useState } from "react";

import { ApiError } from "@/api/ApiError";
import type { Doctor, Patient } from "@/api/types";
import { Alert } from "@/components/Alert";
import { Field, RequiredLegend } from "@/components/Field";
import { useScheduleAppointment } from "@/features/appointments/hooks/useAppointments";
import { todayIso } from "@/lib/format";
import {
  REASON_MAX,
  isClean,
  maxAppointmentDateIso,
  validateAppointmentDate,
  validateReason,
  validateRequired,
} from "@/lib/validation";

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
type FormField = keyof typeof EMPTY_FORM;

/**
 * Formulario de agendado.
 *
 * La validacion de formato se hace aqui para dar respuesta inmediata, pero la
 * autoridad sigue siendo el backend: los errores que devuelve se muestran tal
 * cual, incluido el conflicto de horario que el navegador no puede predecir.
 */
export function AppointmentForm({ patients, doctors, onScheduled }: AppointmentFormProps) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const schedule = useScheduleAppointment();
  const error = schedule.error instanceof ApiError ? schedule.error : null;

  const errors = {
    patientId: validateRequired(form.patientId, "El paciente"),
    doctorId: validateRequired(form.doctorId, "El doctor"),
    date: validateAppointmentDate(form.date),
    startTime: validateRequired(form.startTime, "La hora de inicio"),
    reason: validateReason(form.reason),
  };
  const valid = isClean(errors);

  function setField(field: FormField, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function markTouched(field: FormField) {
    setTouched((current) => ({ ...current, [field]: true }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setTouched({
      patientId: true,
      doctorId: true,
      date: true,
      startTime: true,
      reason: true,
    });
    if (!valid) return;

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
    setTouched({});
    onScheduled(
      result.notificationSent
        ? `Cita registrada. Se notifico a ${result.patientName} por WhatsApp.`
        : `Cita registrada, pero no se pudo notificar a ${result.patientName}.`,
    );
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate>
      <h2>Agendar cita</h2>
      <RequiredLegend />

      {error && (
        <Alert variant={error.isConflict ? "warning" : "error"} title={error.code}>
          {error.message}
        </Alert>
      )}

      <div className="grid">
        <Field label="Paciente" required error={errors.patientId} touched={touched.patientId}>
          <select
            aria-required="true"
            value={form.patientId}
            onChange={(e) => setField("patientId", e.target.value)}
            onBlur={() => markTouched("patientId")}
          >
            <option value="">Seleccione un paciente</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.fullName}
                {patient.phone ? "" : " (sin telefono)"}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Doctor" required error={errors.doctorId} touched={touched.doctorId}>
          <select
            aria-required="true"
            value={form.doctorId}
            onChange={(e) => setField("doctorId", e.target.value)}
            onBlur={() => markTouched("doctorId")}
          >
            <option value="">Seleccione un doctor</option>
            {doctors.map((doctor) => (
              <option key={doctor.id} value={doctor.id}>
                {doctor.displayName} — {doctor.speciality}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Fecha" required error={errors.date} touched={touched.date}>
          <input
            type="date"
            aria-required="true"
            min={todayIso()}
            max={maxAppointmentDateIso()}
            value={form.date}
            onChange={(e) => setField("date", e.target.value)}
            onBlur={() => markTouched("date")}
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
            value={form.startTime}
            onChange={(e) => setField("startTime", e.target.value)}
            onBlur={() => markTouched("startTime")}
          />
        </Field>

        <Field label="Duracion" required>
          <select
            value={form.durationMinutes}
            onChange={(e) => setField("durationMinutes", e.target.value)}
          >
            <option value="30">30 minutos</option>
            <option value="60">1 hora</option>
            <option value="90">1 hora 30 minutos</option>
          </select>
        </Field>
      </div>

      <Field
        label="Motivo de la consulta"
        required
        error={errors.reason}
        touched={touched.reason}
        hint={`${form.reason.trim().length} / ${REASON_MAX} caracteres`}
      >
        <textarea
          aria-required="true"
          rows={3}
          maxLength={REASON_MAX}
          placeholder="Describa el motivo con al menos 10 caracteres"
          value={form.reason}
          onChange={(e) => setField("reason", e.target.value)}
          onBlur={() => markTouched("reason")}
        />
      </Field>

      <button type="submit" className="btn btn--primary" disabled={schedule.isPending || !valid}>
        {schedule.isPending ? "Agendando…" : "Agendar cita"}
      </button>
    </form>
  );
}
