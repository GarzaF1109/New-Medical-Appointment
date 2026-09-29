import { useState } from "react";

import { ApiError } from "@/api/ApiError";
import type { Patient } from "@/api/types";
import { Alert } from "@/components/Alert";
import { usePatients } from "@/features/appointments/hooks/useAppointments";
import { PatientForm } from "@/features/people/components/PatientForm";
import { PersonAgenda } from "@/features/people/components/PersonAgenda";
import { useDeletePatient, usePatientAgenda } from "@/features/people/hooks/usePeople";
import { formatDate } from "@/lib/format";

interface Feedback {
  message: string;
  ok: boolean;
}

/** Pantalla de administracion del catalogo de pacientes. */
export function PatientsPage() {
  const [editing, setEditing] = useState<Patient | null>(null);
  const [agendaFor, setAgendaFor] = useState<Patient | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const patients = usePatients();
  const agenda = usePatientAgenda(agendaFor?.id ?? null);
  const remove = useDeletePatient();

  async function handleDelete(patient: Patient) {
    const confirmed = window.confirm(
      `Eliminar a ${patient.fullName}? Esta accion no se puede deshacer.`,
    );
    if (!confirmed) return;

    try {
      await remove.mutateAsync(patient.id);
      if (agendaFor?.id === patient.id) setAgendaFor(null);
      if (editing?.id === patient.id) setEditing(null);
      setFeedback({ message: `Paciente #${patient.id} eliminado.`, ok: true });
    } catch (error) {
      // El 409 de "tiene citas vigentes" llega aqui: se muestra tal cual
      // porque explica exactamente que hacer antes de reintentar.
      setFeedback({
        message: error instanceof ApiError ? error.message : "Error inesperado.",
        ok: false,
      });
    }
  }

  if (patients.isError) {
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
        <h1>Pacientes</h1>
        <p>
          {patients.data ? `${patients.data.length} paciente(s) registrados` : "Cargando…"}
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

      <PatientForm
        editing={editing}
        onDone={(message) => setFeedback({ message, ok: true })}
        onCancelEdit={() => setEditing(null)}
      />

      <section className="card">
        <h2>Catalogo</h2>
        {patients.isLoading ? (
          <p className="empty">Cargando pacientes…</p>
        ) : patients.data?.length === 0 ? (
          <p className="empty">Aun no hay pacientes registrados.</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Nombre</th>
                  <th>Fecha de nacimiento</th>
                  <th>Edad</th>
                  <th>Telefono</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {patients.data?.map((patient) => (
                  <tr key={patient.id}>
                    <td>{patient.id}</td>
                    <td>{patient.fullName}</td>
                    <td>{formatDate(patient.birthDate)}</td>
                    <td>{patient.age}</td>
                    <td>{patient.phone ?? <span className="muted">Sin telefono</span>}</td>
                    <td className="cell--actions">
                      <button
                        type="button"
                        className="btn btn--small"
                        onClick={() => setEditing(patient)}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="btn btn--small"
                        onClick={() => setAgendaFor(patient)}
                      >
                        Ver citas
                      </button>
                      <button
                        type="button"
                        className="btn btn--small btn--danger"
                        onClick={() => handleDelete(patient)}
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
          title={`Citas de ${agendaFor.fullName}`}
          page={agenda.data}
          isLoading={agenda.isLoading}
          onClose={() => setAgendaFor(null)}
        />
      )}
    </main>
  );
}
