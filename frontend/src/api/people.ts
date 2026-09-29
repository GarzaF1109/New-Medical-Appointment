import { http } from "./client";
import type {
  AppointmentPage,
  CreateDoctorInput,
  CreatePatientInput,
  Doctor,
  Patient,
  UpdateDoctorInput,
  UpdatePatientInput,
} from "./types";

/**
 * Cliente de los catalogos de pacientes y doctores.
 *
 * Cubre el CRUD completo y el subrecurso de citas de cada persona, que es un
 * endpoint distinto del listado filtrado y por eso se expone aparte.
 */
export const patientsApi = {
  list: () => http.get<Patient[]>("/patients"),

  get: (id: number) => http.get<Patient>(`/patients/${id}`),

  create: (input: CreatePatientInput) => http.post<Patient>("/patients", input),

  update: (id: number, input: UpdatePatientInput) =>
    http.patch<Patient>(`/patients/${id}`, input),

  remove: (id: number) => http.delete(`/patients/${id}`),

  appointments: (id: number) => http.get<AppointmentPage>(`/patients/${id}/appointments`),
};

export const doctorsApi = {
  list: () => http.get<Doctor[]>("/doctors"),

  get: (id: number) => http.get<Doctor>(`/doctors/${id}`),

  create: (input: CreateDoctorInput) => http.post<Doctor>("/doctors", input),

  update: (id: number, input: UpdateDoctorInput) => http.patch<Doctor>(`/doctors/${id}`, input),

  remove: (id: number) => http.delete(`/doctors/${id}`),

  appointments: (id: number) => http.get<AppointmentPage>(`/doctors/${id}/appointments`),
};
