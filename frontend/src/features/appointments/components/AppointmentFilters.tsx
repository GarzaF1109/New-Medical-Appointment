import type { AppointmentFilters as Filters } from "@/api/appointments";
import type { Doctor } from "@/api/types";

interface AppointmentFiltersProps {
  doctors: Doctor[];
  value: Filters;
  onChange: (filters: Filters) => void;
}

const STATUS_OPTIONS = [
  { value: 1, label: "Pendiente" },
  { value: 2, label: "Confirmada" },
  { value: 3, label: "Completada" },
  { value: 4, label: "Cancelada" },
];

/** Controles de filtrado del listado de citas. */
export function AppointmentFilters({ doctors, value, onChange }: AppointmentFiltersProps) {
  function update(patch: Partial<Filters>) {
    onChange({ ...value, ...patch });
  }

  return (
    <div className="filters">
      <label>
        Doctor
        <select
          value={value.doctorId ?? ""}
          onChange={(e) =>
            update({ doctorId: e.target.value ? Number(e.target.value) : undefined })
          }
        >
          <option value="">Todos</option>
          {doctors.map((doctor) => (
            <option key={doctor.id} value={doctor.id}>
              {doctor.displayName}
            </option>
          ))}
        </select>
      </label>

      <label>
        Estado
        <select
          value={value.status ?? ""}
          onChange={(e) =>
            update({ status: e.target.value ? Number(e.target.value) : undefined })
          }
        >
          <option value="">Todos</option>
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Desde
        <input
          type="date"
          value={value.dateFrom ?? ""}
          onChange={(e) => update({ dateFrom: e.target.value || undefined })}
        />
      </label>

      <label>
        Hasta
        <input
          type="date"
          value={value.dateTo ?? ""}
          onChange={(e) => update({ dateTo: e.target.value || undefined })}
        />
      </label>

      <button type="button" className="btn btn--ghost" onClick={() => onChange({})}>
        Limpiar filtros
      </button>
    </div>
  );
}
