import type { ReactNode } from "react";

import type { FieldError } from "@/lib/validation";

interface FieldProps {
  label: string;
  /** Marca visible y `aria-required` para lectores de pantalla. */
  required?: boolean;
  /** Mensaje de error, o null si el campo es valido. */
  error?: FieldError;
  /** Se muestra el error solo cuando el usuario ya toco el campo. */
  touched?: boolean;
  hint?: string;
  children: ReactNode;
}

/**
 * Envoltorio de un campo de formulario.
 *
 * Centraliza tres cosas que antes cada input resolvia a su manera: la marca de
 * obligatorio, el mensaje de error y la pista. El error solo aparece cuando el
 * campo ya fue tocado, para no reganar al usuario antes de que escriba.
 */
export function Field({ label, required, error, touched, hint, children }: FieldProps) {
  const showError = Boolean(touched && error);

  return (
    <label className={`field${showError ? " field--invalid" : ""}`}>
      <span className="field__label">
        {label}
        {required && (
          <span className="field__required" aria-hidden="true">
            *
          </span>
        )}
      </span>

      {children}

      {showError ? (
        <small className="field-error" role="alert">
          {error}
        </small>
      ) : (
        hint && <small className="hint">{hint}</small>
      )}
    </label>
  );
}

/** Leyenda que explica el asterisco. Va una sola vez por formulario. */
export function RequiredLegend() {
  return (
    <p className="required-legend">
      Los campos marcados con <span className="field__required">*</span> son obligatorios.
    </p>
  );
}
