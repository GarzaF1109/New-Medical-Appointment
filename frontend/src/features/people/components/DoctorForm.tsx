import { useEffect, useState } from "react";

import { ApiError } from "@/api/ApiError";
import type { Doctor } from "@/api/types";
import { Alert } from "@/components/Alert";
import { Field, RequiredLegend } from "@/components/Field";
import { useCreateDoctor, useUpdateDoctor } from "@/features/people/hooks/usePeople";
import {
  NAME_MAX,
  SPECIALITY_MAX,
  isClean,
  validateLicense,
  validateName,
  validateSpeciality,
} from "@/lib/validation";

interface DoctorFormProps {
  /** Doctor a editar. Si es null, el formulario da de alta uno nuevo. */
  editing: Doctor | null;
  onDone: (message: string) => void;
  onCancelEdit: () => void;
}

const EMPTY_FORM = { fullName: "", speciality: "", medicalLicenseNumber: "" };
type FormField = keyof typeof EMPTY_FORM;

/** Formulario de alta y edicion de doctores. */
export function DoctorForm({ editing, onDone, onCancelEdit }: DoctorFormProps) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const create = useCreateDoctor();
  const updateDoctor = useUpdateDoctor();

  const pending = create.isPending || updateDoctor.isPending;
  const failure = create.error ?? updateDoctor.error;
  const error = failure instanceof ApiError ? failure : null;

  const errors = {
    fullName: validateName(form.fullName),
    speciality: validateSpeciality(form.speciality),
    medicalLicenseNumber: validateLicense(form.medicalLicenseNumber),
  };
  const valid = isClean(errors);

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
    setTouched({});
  }, [editing]);

  function setField(field: FormField, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function markTouched(field: FormField) {
    setTouched((current) => ({ ...current, [field]: true }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setTouched({ fullName: true, speciality: true, medicalLicenseNumber: true });
    if (!valid) return;

    const license = form.medicalLicenseNumber.trim();

    try {
      if (editing) {
        await updateDoctor.mutateAsync({
          id: editing.id,
          input: {
            fullName: form.fullName.trim(),
            speciality: form.speciality.trim(),
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
    setTouched({});
    onCancelEdit();
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate>
      <h2>{editing ? `Editar doctor #${editing.id}` : "Registrar doctor"}</h2>
      <RequiredLegend />

      {error && (
        <Alert variant={error.isConflict ? "warning" : "error"} title={error.code}>
          {error.message}
        </Alert>
      )}

      <div className="grid">
        <Field label="Nombre completo" required error={errors.fullName} touched={touched.fullName}>
          <input
            aria-required="true"
            maxLength={NAME_MAX}
            placeholder="Elena Navarro"
            value={form.fullName}
            onChange={(e) => setField("fullName", e.target.value)}
            onBlur={() => markTouched("fullName")}
          />
        </Field>

        <Field
          label="Especialidad"
          required
          error={errors.speciality}
          touched={touched.speciality}
        >
          <input
            aria-required="true"
            maxLength={SPECIALITY_MAX}
            placeholder="Cardiologia"
            value={form.speciality}
            onChange={(e) => setField("speciality", e.target.value)}
            onBlur={() => markTouched("speciality")}
          />
        </Field>

        <Field
          label="Cedula profesional"
          error={errors.medicalLicenseNumber}
          touched={touched.medicalLicenseNumber}
          hint={editing ? "Dejela vacia para borrarla." : "Opcional. Formato L-YYYYMMDD-####A."}
        >
          <input
            maxLength={20}
            placeholder="L-20260526-8845A"
            value={form.medicalLicenseNumber}
            onChange={(e) => setField("medicalLicenseNumber", e.target.value)}
            onBlur={() => markTouched("medicalLicenseNumber")}
          />
        </Field>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn--primary" disabled={pending || !valid}>
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
