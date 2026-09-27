/** Utilidades de presentacion compartidas. */

/** Convierte "2026-10-15" en "15/10/2026" sin desfases de zona horaria. */
export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

/** Recorta "10:00:00" a "10:00". */
export function formatTime(isoTime: string): string {
  return isoTime.slice(0, 5);
}

/** Devuelve la fecha de hoy en formato ISO, util como minimo de un input date. */
export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Clase CSS del distintivo de estado. */
export function statusClassName(status: number): string {
  const byStatus: Record<number, string> = {
    1: "badge badge--pending",
    2: "badge badge--confirmed",
    3: "badge badge--completed",
    4: "badge badge--cancelled",
  };
  return byStatus[status] ?? "badge";
}
