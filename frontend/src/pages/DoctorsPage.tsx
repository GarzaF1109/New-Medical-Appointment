import { useState } from "react";

import { ApiError } from "@/api/ApiError";
import type { Doctor } from "@/api/types";
import { Alert } from "@/components/Alert";
import { useDoctors } from "@/features/appointments/hooks/useAppointments";
import { DoctorForm } from "@/features/people/components/DoctorForm";
import { PersonAgenda } from "@/features/people/components/PersonAgenda";
import { useDeleteDoctor, useDoctorAgenda } from "@/features/people/hooks/usePeople";

interface Feedback {
  message: string;
  ok: boolean;
}

/** Pantalla de administracion del catalogo de doctores. */
export function DoctorsPage() {
  const [editing, setEditing] = useState<Doctor | null>(null);
  const [agendaFor, setAgendaFor] = useState<Doctor | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const doctors = useDoctors();
  const agenda = useDoctorAgenda(agendaFor?.id ?? null);
  const remove = useDeleteDoctor();

  async function handleDelete(doctor: Doctor) {
    const confirmed = window.confirm(
      `Eliminar a ${doctor.displayName}? Esta accion no se puede deshacer.`,
    );
    if (!confirmed) return;

    try {
      await remove.mutateAsync(doctor.id);
      if (agendaFor?.id === doctor.id) setAgendaFor(null);
      if (editing?.id === doctor.id) setEditing(null);
      setFeedback({ message: `Doctor #${doctor.id} eliminado.`, ok: true });
    } catch (error) {
      setFeedback({
        message: error instanceof ApiError ? error.message : "Error inesperado.",
        ok: false,
      });
    }
  }

  if (doctors.isError) {
    return (
      <main className="page">
        <Alert variant="error" title="No se pudo cargar el catalogo">
          Verifique que el backend este disponible en /api/v1 e intente de nuevo.
        </Alert>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="page__header">
        <h1>Doctores</h1>
        <p>{doctors.data ? `${doctors.data.length} doctor(es) registrados` : "Cargando…"}</p>
      </header>

      {feedback && (
        <Alert variant={feedback.ok ? "success" : "error"} onDismiss={() => setFeedback(null)}>
          {feedback.message}
        </Alert>
      )}

      <DoctorForm
        editing={editing}
        onDone={(message) => setFeedback({ message, ok: true })}
        onCancelEdit={() => setEditing(null)}
      />

      <section className="card">
        <h2>Catalogo</h2>
        {doctors.isLoading ? (
          <p className="empty">Cargando doctores…</p>
        ) : doctors.data?.length === 0 ? (
          <p className="empty">Aun no hay doctores registrados.</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Nombre</th>
                  <th>Especialidad</th>
                  <th>Cedula</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {doctors.data?.map((doctor) => (
                  <tr key={doctor.id}>
                    <td>{doctor.id}</td>
                    <td>{doctor.displayName}</td>
                    <td>{doctor.speciality}</td>
                    <td>
                      {doctor.medicalLicenseNumber ?? (
                        <span className="muted">Sin cedula</span>
                      )}
                    </td>
                    <td className="cell--actions">
                      <button
                        type="button"
                        className="btn btn--small"
                        onClick={() => setEditing(doctor)}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="btn btn--small"
                        onClick={() => setAgendaFor(doctor)}
                      >
                        Ver agenda
                      </button>
                      <button
                        type="button"
                        className="btn btn--small btn--danger"
                        onClick={() => handleDelete(doctor)}
                        disabled={remove.isPending}
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {agendaFor && (
        <PersonAgenda
          title={`Agenda de ${agendaFor.displayName}`}
          page={agenda.data}
          isLoading={agenda.isLoading}
          onClose={() => setAgendaFor(null)}
        />
      )}
    </main>
  );
}
