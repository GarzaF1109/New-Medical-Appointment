import type { ApiErrorBody, ApiErrorDetail } from "./types";

/**
 * Error tipado que representa una respuesta 4xx o 5xx de la API.
 *
 * Al conservar `code` y `details`, la interfaz puede reaccionar de forma
 * distinta a un conflicto de horario (409) que a un fallo de validacion (422)
 * sin tener que interpretar cadenas de texto.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ApiErrorDetail[];

  constructor(body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = body.status;
    this.code = body.code;
    this.details = body.details ?? [];
  }

  /** Indica si el error corresponde a un choque de agenda. */
  get isConflict(): boolean {
    return this.status === 409;
  }

  /** Indica si el error corresponde a datos de entrada invalidos. */
  get isValidation(): boolean {
    return this.status === 422;
  }

  /** Devuelve el mensaje asociado a un campo concreto, si lo hay. */
  messageForField(field: string): string | undefined {
    return this.details.find((detail) => detail.field === field)?.message;
  }
}
