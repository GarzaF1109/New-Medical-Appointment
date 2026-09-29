import { useEffect, useState } from "react";

import { ApiError } from "@/api/ApiError";
import type { Patient } from "@/api/types";
import { Alert } from "@/components/Alert";
import { Field, RequiredLegend } from "@/components/Field";
import { useCreatePatient, useUpdatePatient } from "@/features/people/hooks/usePeople";
import { todayIso } from "@/lib/format";
import {
  NAME_MAX,
  isClean,
  validateBirthDate,
  validateName,
  validatePhone,
} from "@/lib/validation";

interface PatientFormProps {
  /** Paciente a editar. Si es null, el formulario da de alta uno nuevo. */
  editing: Patient | null;
  onDone: (message: string) => void;
  onCancelEdit: () => void;
}

const EMPTY_FORM = { fullName: "", birthDate: "", phone: "" };
type FormField = keyof typeof EMPTY_FORM;

/**
 * Formulario de alta y edicion de pacientes.
 *
 * En modo edicion vaciar el telefono envia `null` explicitamente, que es como
 * el backend distingue "borrar el dato" de "no lo toques".
 */
export function PatientForm({ editing, onDone, onCancelEdit }: PatientFormProps) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const create = useCreatePatient();
  const updatePatient = useUpdatePatient();

  const pending = create.isPending || updatePatient.isPending;
  const failure = create.error ?? updatePatient.error;
  const error = failure instanceof ApiError ? failure : null;

  const errors = {
    fullName: validateName(form.fullName),
    birthDate: validateBirthDate(form.birthDate),
    phone: validatePhone(form.phone),
  };
  const valid = isClean(errors);

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
    // Al enviar se marcan todos como tocados para que los errores pendientes
    // se hagan visibles de golpe, en lugar de fallar en silencio.
    setTouched({ fullName: true, birthDate: true, phone: true });
    if (!valid) return;

    const phone = form.phone.trim();

    try {
      if (editing) {
        await updatePatient.mutateAsync({
          id: editing.id,
          input: {
            fullName: form.fullName.trim(),
            birthDate: form.birthDate,
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
      return;
    }

    setForm(EMPTY_FORM);
    setTouched({});
    onCancelEdit();
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate>
      <h2>{editing ? `Editar paciente #${editing.id}` : "Registrar paciente"}</h2>
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
            placeholder="Ana Maria Lopez"
            value={form.fullName}
            onChange={(e) => setField("fullName", e.target.value)}
            onBlur={() => markTouched("fullName")}
          />
        </Field>

        <Field
          label="Fecha de nacimiento"
          required
          error={errors.birthDate}
          touched={touched.birthDate}
        >
          <input
            type="date"
            aria-required="true"
            min="1900-01-01"
            max={todayIso()}
            value={form.birthDate}
            onChange={(e) => setField("birthDate", e.target.value)}
            onBlur={() => markTouched("birthDate")}
          />
        </Field>

        <Field
          label="Telefono de contacto"
          error={errors.phone}
          touched={touched.phone}
          hint={editing ? "Dejelo vacio para borrar el telefono." : "Opcional. Solo digitos."}
        >
          <input
            type="tel"
            inputMode="tel"
            maxLength={20}
            placeholder="8112345678"
            value={form.phone}
            onChange={(e) => setField("phone", e.target.value)}
            onBlur={() => markTouched("phone")}
          />
        </Field>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn--primary" disabled={pending || !valid}>
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
