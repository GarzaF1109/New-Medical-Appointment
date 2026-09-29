import { useEffect, useState } from "react";

import { ApiError } from "@/api/ApiError";
import type { Doctor } from "@/api/types";
import { Alert } from "@/components/Alert";
import { useCreateDoctor, useUpdateDoctor } from "@/features/people/hooks/usePeople";

interface DoctorFormProps {
  /** Doctor a editar. Si es null, el formulario da de alta uno nuevo. */
  editing: Doctor | null;
  onDone: (message: string) => void;
  onCancelEdit: () => void;
}

const EMPTY_FORM = { fullName: "", speciality: "", medicalLicenseNumber: "" };

/** Formulario de alta y edicion de doctores. */
export function DoctorForm({ editing, onDone, onCancelEdit }: DoctorFormProps) {
  const [form, setForm] = useState(EMPTY_FORM);
  const create = useCreateDoctor();
  const updateDoctor = useUpdateDoctor();

  const pending = create.isPending || updateDoctor.isPending;
  const failure = create.error ?? updateDoctor.error;
  const error = failure instanceof ApiError ? failure : null;

  useEffect(() => {
    setForm(
      editing
        ? {
            fullName: editing.fullName,
            speciality: editing.speciality,
            medicalLicenseNumber: editing.medicalLicenseNumber ?? "",
          }
        : EMPTY_FORM,
    );
  }, [editing]);

  function setField(field: keyof typeof EMPTY_FORM, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const license = form.medicalLicenseNumber.trim();

    try {
      if (editing) {
        await updateDoctor.mutateAsync({
          id: editing.id,
          input: {
            fullName: form.fullName.trim(),
            speciality: form.speciality.trim(),
            // Vacio significa "quitale la cedula", no "dejala como estaba".
            medicalLicenseNumber: license === "" ? null : license,
          },
        });
        onDone(`Doctor #${editing.id} actualizado.`);
      } else {
        const created = await create.mutateAsync({
          fullName: form.fullName.trim(),
          speciality: form.speciality.trim(),
          medicalLicenseNumber: license === "" ? null : license,
        });
        onDone(`Doctor #${created.id} registrado.`);
      }
    } catch {
      return;
    }

    setForm(EMPTY_FORM);
    onCancelEdit();
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>{editing ? `Editar doctor #${editing.id}` : "Registrar doctor"}</h2>

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
            placeholder="Elena Navarro"
            value={form.fullName}
            onChange={(e) => setField("fullName", e.target.value)}
          />
        </label>

        <label>
          Especialidad
          <input
            required
            maxLength={120}
            placeholder="Cardiologia"
            value={form.speciality}
            onChange={(e) => setField("speciality", e.target.value)}
          />
        </label>

        <label>
          Cedula profesional
          <input
            maxLength={20}
            placeholder="L-20260526-8845A (opcional)"
            value={form.medicalLicenseNumber}
            onChange={(e) => setField("medicalLicenseNumber", e.target.value)}
          />
          <small className="hint">
            {editing
              ? "Dejela vacia para borrar la cedula registrada."
              : "Formato L-YYYYMMDD-####A."}
          </small>
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn--primary" disabled={pending}>
          {pending ? "Guardando…" : editing ? "Guardar cambios" : "Registrar doctor"}
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
