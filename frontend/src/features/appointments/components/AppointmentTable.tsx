import { AppointmentStatus, type Appointment } from "@/api/types";
import { useAppointmentTransition } from "@/features/appointments/hooks/useAppointments";
import { formatDate, formatTime, statusClassName } from "@/lib/format";

interface AppointmentTableProps {
  appointments: Appointment[];
  onActionResult: (message: string, ok: boolean) => void;
}

/** Tabla de citas con las acciones disponibles segun el estado de cada una. */
export function AppointmentTable({ appointments, onActionResult }: AppointmentTableProps) {
  const transition = useAppointmentTransition();

  async function run(id: number, action: "confirm" | "complete" | "cancel", label: string) {
    try {
      await transition.mutateAsync({ id, action });
      onActionResult(`Cita #${id}: ${label}.`, true);
    } catch (error) {
      onActionResult(error instanceof Error ? error.message : "Error inesperado.", false);
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
            <tr key={appointment.id}>
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
                        className="btn btn--small btn--danger"
                        onClick={() => run(appointment.id, "cancel", "cancelada")}
                      >
                        Cancelar
                      </button>
                    </>
                  )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
