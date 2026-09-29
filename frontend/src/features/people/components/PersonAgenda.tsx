import type { AppointmentPage } from "@/api/types";
import { formatDate, formatTime, statusClassName } from "@/lib/format";

interface PersonAgendaProps {
  title: string;
  page: AppointmentPage | undefined;
  isLoading: boolean;
  onClose: () => void;
}

/**
 * Agenda de una persona, leida del subrecurso `/{coleccion}/{id}/appointments`.
 *
 * Es un endpoint distinto del listado filtrado, por eso tiene su propia vista
 * en lugar de reutilizar la tabla de la pantalla de citas.
 */
export function PersonAgenda({ title, page, isLoading, onClose }: PersonAgendaProps) {
  return (
    <section className="card">
      <div className="card__header">
        <h2>{title}</h2>
        <button type="button" className="btn btn--small" onClick={onClose}>
          Cerrar
        </button>
      </div>

      {isLoading && <p className="empty">Cargando agenda…</p>}

      {!isLoading && (page?.items.length ?? 0) === 0 && (
        <p className="empty">Esta persona no tiene citas registradas.</p>
      )}

      {!isLoading && page && page.items.length > 0 && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Paciente</th>
                <th>Doctor</th>
                <th>Fecha</th>
                <th>Horario</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {page.items.map((appointment) => (
                <tr key={appointment.id}>
                  <td>{appointment.id}</td>
                  <td>{appointment.patientName}</td>
                  <td>{appointment.doctorName}</td>
                  <td>{formatDate(appointment.date)}</td>
                  <td>
                    {formatTime(appointment.startTime)}–{formatTime(appointment.endTime)}
                  </td>
                  <td>
                    <span className={statusClassName(appointment.status)}>
                      {appointment.statusLabel}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
