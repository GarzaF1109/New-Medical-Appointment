import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { appointmentsApi, catalogApi, type AppointmentFilters } from "@/api/appointments";
import type { RescheduleAppointmentInput, ScheduleAppointmentInput } from "@/api/types";

/** Claves de cache de React Query, centralizadas para invalidar sin adivinar. */
export const queryKeys = {
  appointments: (filters: AppointmentFilters) => ["appointments", filters] as const,
  patients: ["patients"] as const,
  doctors: ["doctors"] as const,
};

/** Lista de citas segun los filtros indicados. */
export function useAppointments(filters: AppointmentFilters = {}) {
  return useQuery({
    queryKey: queryKeys.appointments(filters),
    queryFn: () => appointmentsApi.list(filters),
  });
}

/** Catalogo de pacientes para los selectores del formulario. */
export function usePatients() {
  return useQuery({ queryKey: queryKeys.patients, queryFn: catalogApi.patients });
}

/** Catalogo de doctores para los selectores del formulario. */
export function useDoctors() {
  return useQuery({ queryKey: queryKeys.doctors, queryFn: catalogApi.doctors });
}

/**
 * Invalida el listado de citas tras cualquier mutacion.
 *
 * Centralizarlo evita el error de agregar una accion nueva y olvidar refrescar
 * la tabla, que dejaria al usuario viendo datos obsoletos.
 */
function useInvalidateAppointments() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["appointments"] });
}

/** Agenda una cita nueva. */
export function useScheduleAppointment() {
  const invalidate = useInvalidateAppointments();
  return useMutation({
    mutationFn: (input: ScheduleAppointmentInput) => appointmentsApi.schedule(input),
    onSuccess: invalidate,
  });
}

/** Reagenda o reasigna una cita existente. */
export function useRescheduleAppointment() {
  const invalidate = useInvalidateAppointments();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: RescheduleAppointmentInput }) =>
      appointmentsApi.reschedule(id, input),
    onSuccess: invalidate,
  });
}

/** Aplica una transicion de estado sobre una cita. */
export function useAppointmentTransition() {
  const invalidate = useInvalidateAppointments();
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: "confirm" | "complete" | "cancel" }) =>
      appointmentsApi[action](id),
    onSuccess: invalidate,
  });
}
