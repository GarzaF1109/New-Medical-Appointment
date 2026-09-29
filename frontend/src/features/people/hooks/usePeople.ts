import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { doctorsApi, patientsApi } from "@/api/people";
import type {
  CreateDoctorInput,
  CreatePatientInput,
  UpdateDoctorInput,
  UpdatePatientInput,
} from "@/api/types";
import { queryKeys } from "@/features/appointments/hooks/useAppointments";

/**
 * Invalida el catalogo indicado y, ademas, el listado de citas.
 *
 * Renombrar a un paciente cambia el texto que la tabla de citas muestra, de
 * modo que refrescar solo el catalogo dejaria la agenda con el nombre viejo.
 */
function useInvalidateCatalog(key: readonly string[]) {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries({ queryKey: key });
    void queryClient.invalidateQueries({ queryKey: ["appointments"] });
  };
}

/** Agenda completa de un paciente (subrecurso `/patients/{id}/appointments`). */
export function usePatientAgenda(patientId: number | null) {
  return useQuery({
    queryKey: ["patient-agenda", patientId],
    queryFn: () => patientsApi.appointments(patientId!),
    enabled: patientId !== null,
  });
}

/** Agenda completa de un doctor (subrecurso `/doctors/{id}/appointments`). */
export function useDoctorAgenda(doctorId: number | null) {
  return useQuery({
    queryKey: ["doctor-agenda", doctorId],
    queryFn: () => doctorsApi.appointments(doctorId!),
    enabled: doctorId !== null,
  });
}

export function useCreatePatient() {
  const invalidate = useInvalidateCatalog(queryKeys.patients);
  return useMutation({
    mutationFn: (input: CreatePatientInput) => patientsApi.create(input),
    onSuccess: invalidate,
  });
}

export function useUpdatePatient() {
  const invalidate = useInvalidateCatalog(queryKeys.patients);
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: UpdatePatientInput }) =>
      patientsApi.update(id, input),
    onSuccess: invalidate,
  });
}

export function useDeletePatient() {
  const invalidate = useInvalidateCatalog(queryKeys.patients);
  return useMutation({
    mutationFn: (id: number) => patientsApi.remove(id),
    onSuccess: invalidate,
  });
}

export function useCreateDoctor() {
  const invalidate = useInvalidateCatalog(queryKeys.doctors);
  return useMutation({
    mutationFn: (input: CreateDoctorInput) => doctorsApi.create(input),
    onSuccess: invalidate,
  });
}

export function useUpdateDoctor() {
  const invalidate = useInvalidateCatalog(queryKeys.doctors);
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: UpdateDoctorInput }) =>
      doctorsApi.update(id, input),
    onSuccess: invalidate,
  });
}

export function useDeleteDoctor() {
  const invalidate = useInvalidateCatalog(queryKeys.doctors);
  return useMutation({
    mutationFn: (id: number) => doctorsApi.remove(id),
    onSuccess: invalidate,
  });
}
