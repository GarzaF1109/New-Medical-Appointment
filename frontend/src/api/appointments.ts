import { http } from "./client";
import type {
  Appointment,
  AppointmentPage,
  Doctor,
  Patient,
  RescheduleAppointmentInput,
  ScheduleAppointmentInput,
} from "./types";

/** Filtros aceptados por el listado de citas. */
export interface AppointmentFilters {
  doctorId?: number;
  patientId?: number;
  status?: number;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
  offset?: number;
}

function toQueryString(filters: AppointmentFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const appointmentsApi = {
  list: (filters: AppointmentFilters = {}) =>
    http.get<AppointmentPage>(`/appointments${toQueryString(filters)}`),

  get: (id: number) => http.get<Appointment>(`/appointments/${id}`),

  schedule: (input: ScheduleAppointmentInput) =>
    http.post<Appointment>("/appointments", input),

  reschedule: (id: number, input: RescheduleAppointmentInput) =>
    http.patch<Appointment>(`/appointments/${id}`, input),

  confirm: (id: number) => http.put<Appointment>(`/appointments/${id}/confirmation`),

  complete: (id: number) => http.put<Appointment>(`/appointments/${id}/completion`),

  cancel: (id: number) => http.put<Appointment>(`/appointments/${id}/cancellation`),

  remove: (id: number) => http.delete(`/appointments/${id}`),
};

export const catalogApi = {
  patients: () => http.get<Patient[]>("/patients"),
  doctors: () => http.get<Doctor[]>("/doctors"),
};
