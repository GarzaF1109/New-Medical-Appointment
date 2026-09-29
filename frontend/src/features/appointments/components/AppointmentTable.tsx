import { Fragment, useState } from "react";

import { ApiError } from "@/api/ApiError";
import { AppointmentStatus, type Appointment } from "@/api/types";
import { RescheduleRow } from "@/features/appointments/components/RescheduleRow";
import {
  useAppointmentTransition,
  useDeleteAppointment,
} from "@/features/appointments/hooks/useAppointments";
import { formatDate, formatTime, statusClassName } from "@/lib/format";

/** Columnas de la tabla; la fila de reagendado las abarca todas. */
const COLUMN_COUNT = 8;

interface AppointmentTableProps {
  appointments: Appointment[];
  onActionResult: (message: string, ok: boolean) => void;
}

/** Tabla de citas con las acciones disponibles segun el estado de cada una. */
export function AppointmentTable({ appointments, onActionResult }: AppointmentTableProps) {
  const [reschedulingId, setReschedulingId] = useState<number | null>(null);
  const transition = useAppointmentTransition();
  const remove = useDeleteAppointment();

  async function run(id: number, action: "confirm" | "complete" | "cancel", label: string) {
    try {
      await transition.mutateAsync({ id, action });
      onActionResult(`Cita #${id}: ${label}.`, true);
    } catch (error) {
      onActionResult(error instanceof Error ? error.message : "Error inesperado.", false);
    }
  }

  async function handleDelete(id: number) {
    const confirmed = window.confirm(
      `Eliminar la cita #${id}? Cancelarla conserva el historial; eliminarla no.`,
    );
    if (!confirmed) return;

    try {
      await remove.mutateAsync(id);
      if (reschedulingId === id) setReschedulingId(null);
      onActionResult(`Cita #${id} eliminada.`, true);
    } catch (error) {
      onActionResult(error instanceof ApiError ? error.message : "Error inesperado.", false);
    }
  }

  if (appointments.length === 0) {
    return <p className="empty">No hay citas que coincidan con los filtros.</p>;
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Paciente</th>
            <th>Doctor</th>
            <th>Fecha</th>
            <th>Horario</th>
            <th>Motivo</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((appointment) => (
            <Fragment key={appointment.id}>
              <tr>
                <td>{appointment.id}</td>
                <td>{appointment.patientName}</td>
                <td>{appointment.doctorName}</td>
                <td>{formatDate(appointment.date)}</td>
                <td>
                  {formatTime(appointment.startTime)}–{formatTime(appointment.endTime)}
                </td>
                <td className="cell--reason" title={appointment.reason}>
                  {appointment.reason}
                </td>
                <td>
                  <span className={statusClassName(appointment.status)}>
                    {appointment.statusLabel}
                  </span>
                </td>
                <td className="cell--actions">
                  {appointment.status === AppointmentStatus.Pending && (
                    <button
                      type="button"
                      className="btn btn--small"
                      onClick={() => run(appointment.id, "confirm", "confirmada")}
                    >
                      Confirmar
                    </button>
                  )}
                  {appointment.status !== AppointmentStatus.Completed &&
                    appointment.status !== AppointmentStatus.Cancelled && (
                      <>
                        <button
                          type="button"
                          className="btn btn--small"
                          onClick={() => run(appointment.id, "complete", "marcada como atendida")}
                        >
                          Atendida
                        </button>
                        <button
                          type="button"
                          className="btn btn--small"
                          onClick={() =>
                            setReschedulingId(
                              reschedulingId === appointment.id ? null : appointment.id,
                            )
                          }
                        >
                          Reagendar
                        </button>
                        <button
                          type="button"
                          className="btn btn--small btn--danger"
                          onClick={() => run(appointment.id, "cancel", "cancelada")}
                        >
                          Cancelar
                        </button>
                      </>
                    )}
                  <button
                    type="button"
                    className="btn btn--small btn--danger"
                    onClick={() => handleDelete(appointment.id)}
                    disabled={remove.isPending}
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
              {reschedulingId === appointment.id && (
                <RescheduleRow
                  appointment={appointment}
                  columnCount={COLUMN_COUNT}
                  onDone={onActionResult}
                  onCancel={() => setReschedulingId(null)}
                />
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
