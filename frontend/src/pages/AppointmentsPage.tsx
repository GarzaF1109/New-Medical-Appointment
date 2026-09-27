import { useState } from "react";

import type { AppointmentFilters as Filters } from "@/api/appointments";
import { Alert } from "@/components/Alert";
import { AppointmentFilters } from "@/features/appointments/components/AppointmentFilters";
import { AppointmentForm } from "@/features/appointments/components/AppointmentForm";
import { AppointmentTable } from "@/features/appointments/components/AppointmentTable";
import {
  useAppointments,
  useDoctors,
  usePatients,
} from "@/features/appointments/hooks/useAppointments";

interface Feedback {
  message: string;
  ok: boolean;
}

/** Pantalla principal del modulo de citas. */
export function AppointmentsPage() {
  const [filters, setFilters] = useState<Filters>({});
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const appointments = useAppointments(filters);
  const patients = usePatients();
  const doctors = useDoctors();

  if (appointments.isError || patients.isError || doctors.isError) {
    return (
      <Alert variant="error" title="No se pudo cargar la informacion">
        Verifique que el backend este disponible en /api/v1 e intente de nuevo.
      </Alert>
    );
  }

  return (
    <main className="page">
      <header className="page__header">
        <h1>Citas medicas</h1>
        <p>
          {appointments.data
            ? `${appointments.data.total} cita(s) registradas`
            : "Cargando…"}
        </p>
      </header>

      {feedback && (
        <Alert
          variant={feedback.ok ? "success" : "error"}
          onDismiss={() => setFeedback(null)}
        >
          {feedback.message}
        </Alert>
      )}

      {patients.data && doctors.data && (
        <AppointmentForm
          patients={patients.data}
          doctors={doctors.data}
          onScheduled={(message) => setFeedback({ message, ok: true })}
        />
      )}

      <section className="card">
        <h2>Agenda</h2>
        <AppointmentFilters
          doctors={doctors.data ?? []}
          value={filters}
          onChange={setFilters}
        />
        {appointments.isLoading ? (
          <p className="empty">Cargando citas…</p>
        ) : (
          <AppointmentTable
            appointments={appointments.data?.items ?? []}
            onActionResult={(message, ok) => setFeedback({ message, ok })}
          />
        )}
      </section>
    </main>
  );
}
