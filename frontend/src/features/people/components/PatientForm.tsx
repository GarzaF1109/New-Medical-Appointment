import { useEffect, useState } from "react";

import { ApiError } from "@/api/ApiError";
import type { Patient } from "@/api/types";
import { Alert } from "@/components/Alert";
import { useCreatePatient, useUpdatePatient } from "@/features/people/hooks/usePeople";
import { todayIso } from "@/lib/format";

interface PatientFormProps {
  /** Paciente a editar. Si es null, el formulario da de alta uno nuevo. */
  editing: Patient | null;
  onDone: (message: string) => void;
  onCancelEdit: () => void;
}

const EMPTY_FORM = { fullName: "", birthDate: "", phone: "" };

/**
 * Formulario de alta y edicion de pacientes.
 *
 * En modo edicion vaciar el telefono envia `null` explicitamente, que es como
 * el backend distingue "borrar el dato" de "no lo toques". Rellenarlo con
 * undefined dejaria el telefono viejo sin que el usuario entienda por que.
 */
export function PatientForm({ editing, onDone, onCancelEdit }: PatientFormProps) {
  const [form, setForm] = useState(EMPTY_FORM);
  const create = useCreatePatient();
  const updatePatient = useUpdatePatient();

  const pending = create.isPending || updatePatient.isPending;
  const failure = create.error ?? updatePatient.error;
  const error = failure instanceof ApiError ? failure : null;

  useEffect(() => {
    setForm(
      editing
        ? {
            fullName: editing.fullName,
            birthDate: editing.birthDate,
            phone: editing.phone ?? "",
          }
        : EMPTY_FORM,
    );
  }, [editing]);

  function setField(field: keyof typeof EMPTY_FORM, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const phone = form.phone.trim();

    try {
      if (editing) {
        await updatePatient.mutateAsync({
          id: editing.id,
          input: {
            fullName: form.fullName.trim(),
            birthDate: form.birthDate,
            // Vacio significa "quitale el telefono", no "dejalo como estaba".
            phone: phone === "" ? null : phone,
          },
        });
        onDone(`Paciente #${editing.id} actualizado.`);
      } else {
        const created = await create.mutateAsync({
          fullName: form.fullName.trim(),
          birthDate: form.birthDate,
          phone: phone === "" ? null : phone,
        });
        onDone(`Paciente #${created.id} registrado.`);
      }
    } catch {
      // El detalle ya se muestra en el aviso; se conserva lo capturado para
      // que el usuario pueda corregirlo sin volver a teclear todo.
      return;
    }

    setForm(EMPTY_FORM);
    onCancelEdit();
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>{editing ? `Editar paciente #${editing.id}` : "Registrar paciente"}</h2>

      {error && (
        <Alert variant={error.isConflict ? "warning" : "error"} title={error.code}>
          {error.message}
        </Alert>
      )}

      <div className="grid">
        <label>
          Nombre completo
          <input
            required
            minLength={3}
            maxLength={255}
            placeholder="Ana Maria Lopez"
            value={form.fullName}
            onChange={(e) => setField("fullName", e.target.value)}
          />
        </label>

        <label>
          Fecha de nacimiento
          <input
            type="date"
            required
            max={todayIso()}
            value={form.birthDate}
            onChange={(e) => setField("birthDate", e.target.value)}
          />
        </label>

        <label>
          Telefono de contacto
          <input
            maxLength={20}
            placeholder="8112345678 (opcional)"
            value={form.phone}
            onChange={(e) => setField("phone", e.target.value)}
          />
          {editing && (
            <small className="hint">Dejelo vacio para borrar el telefono registrado.</small>
          )}
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn--primary" disabled={pending}>
          {pending ? "Guardando…" : editing ? "Guardar cambios" : "Registrar paciente"}
        </button>
        {editing && (
          <button type="button" className="btn" onClick={onCancelEdit} disabled={pending}>
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}
