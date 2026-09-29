/**
 * Tipos del contrato HTTP.
 *
 * Reflejan uno a uno los esquemas que publica el backend en /openapi.json.
 * Mantenerlos en su propio modulo evita que los componentes inventen formas
 * de datos que el servidor nunca envia.
 */

export const AppointmentStatus = {
  Pending: 1,
  Confirmed: 2,
  Completed: 3,
  Cancelled: 4,
} as const;

export type AppointmentStatusValue =
  (typeof AppointmentStatus)[keyof typeof AppointmentStatus];

export interface Appointment {
  id: number;
  patientId: number;
  patientName: string;
  doctorId: number;
  doctorName: string;
  date: string;
  startTime: string;
  endTime: string;
  durationMinutes: number;
  reason: string;
  status: AppointmentStatusValue;
  statusLabel: string;
  notificationSent: boolean | null;
  _links: Record<string, { href: string }>;
}

export interface AppointmentPage {
  items: Appointment[];
  total: number;
  limit: number;
  offset: number;
}

export interface Patient {
  id: number;
  fullName: string;
  /** Fecha de nacimiento en formato ISO 8601 (YYYY-MM-DD). */
  birthDate: string;
  /** Edad cumplida, derivada por el backend. */
  age: number;
  phone: string | null;
}

export interface Doctor {
  id: number;
  fullName: string;
  displayName: string;
  speciality: string;
  medicalLicenseNumber: string | null;
}

export interface ScheduleAppointmentInput {
  patientId: number;
  doctorId: number;
  date: string;
  startTime: string;
  durationMinutes?: number;
  reason: string;
}

export interface CreatePatientInput {
  fullName: string;
  /** Fecha de nacimiento en formato ISO 8601 (YYYY-MM-DD). */
  birthDate: string;
  phone?: string | null;
}

/**
 * Edicion parcial de un paciente.
 *
 * Omitir un campo lo conserva; enviarlo como `null` lo borra. La distincion es
 * significativa para el backend, asi que no se debe "rellenar" con undefined.
 */
export interface UpdatePatientInput {
  fullName?: string;
  birthDate?: string;
  phone?: string | null;
}

export interface CreateDoctorInput {
  fullName: string;
  speciality: string;
  medicalLicenseNumber?: string | null;
}

/** Edicion parcial de un doctor; mismas reglas que `UpdatePatientInput`. */
export interface UpdateDoctorInput {
  fullName?: string;
  speciality?: string;
  medicalLicenseNumber?: string | null;
}

export interface RescheduleAppointmentInput {
  date?: string;
  startTime?: string;
  durationMinutes?: number;
  patientId?: number;
  doctorId?: number;
  reason?: string;
}

/** Detalle de un campo invalido devuelto por el backend. */
export interface ApiErrorDetail {
  field: string;
  message: string;
}

/** Cuerpo de error canonico de la API. */
export interface ApiErrorBody {
  status: number;
  code: string;
  message: string;
  details?: ApiErrorDetail[];
}
