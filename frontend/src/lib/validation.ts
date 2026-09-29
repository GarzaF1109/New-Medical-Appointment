/**
 * Validaciones de formulario.
 *
 * Son un espejo de las reglas del dominio en `backend/src/app/domain/`. Existen
 * para dar respuesta inmediata y no gastar una peticion en un error que el
 * navegador puede detectar solo; la autoridad sigue siendo el backend, y sus
 * mensajes se muestran tal cual cuando rechaza algo que aqui no se puede saber
 * (un horario ocupado, por ejemplo).
 */

/** Letras con acentos y ñ, espacios y los signos de un nombre real. Sin digitos. */
const NAME_ALLOWED = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' .-]+$/;
const HAS_LETTER = /[A-Za-zÁÉÍÓÚáéíóúÑñÜü]/;
/** En un telefono se aceptan separadores humanos, pero jamas letras. */
const PHONE_ALLOWED = /^[+0-9 ().-]+$/;
const LICENSE = /^L-\d{8}-\d{4}[A-Z]$/;

export const NAME_MIN = 3;
export const NAME_MAX = 255;
export const SPECIALITY_MIN = 3;
export const SPECIALITY_MAX = 120;
export const REASON_MIN = 10;
export const REASON_MAX = 500;
export const PHONE_MIN_DIGITS = 10;
export const PHONE_MAX_DIGITS = 15;
export const MAX_HUMAN_AGE = 120;
export const MAX_MONTHS_AHEAD = 24;

/** Mensaje de error del campo, o null si es valido. */
export type FieldError = string | null;

function collapse(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

export function validateName(raw: string, field = "El nombre"): FieldError {
  const value = collapse(raw);
  if (!value) return `${field} es obligatorio.`;
  if (value.length < NAME_MIN) return `${field} debe tener al menos ${NAME_MIN} caracteres.`;
  if (value.length > NAME_MAX) return `${field} no puede exceder ${NAME_MAX} caracteres.`;
  if (/\d/.test(value)) return `${field} no puede contener numeros.`;
  if (!NAME_ALLOWED.test(value)) return `${field} solo admite letras, espacios, guiones y apostrofes.`;
  if (!HAS_LETTER.test(value)) return `${field} debe contener al menos una letra.`;
  return null;
}

/** El telefono es opcional: vacio es valido y significa "sin telefono". */
export function validatePhone(raw: string): FieldError {
  const value = raw.trim();
  if (!value) return null;
  if (/[A-Za-zÁÉÍÓÚáéíóúÑñÜü]/.test(value)) return "El telefono no puede contener letras.";
  if (!PHONE_ALLOWED.test(value)) return "El telefono solo admite digitos y los separadores + ( ) - . y espacio.";

  const digits = value.replace(/\D/g, "");
  if (digits.length < PHONE_MIN_DIGITS) return `El telefono debe tener al menos ${PHONE_MIN_DIGITS} digitos.`;
  if (digits.length > PHONE_MAX_DIGITS) return `El telefono no puede exceder ${PHONE_MAX_DIGITS} digitos.`;
  return null;
}

export function validateBirthDate(raw: string, today = new Date()): FieldError {
  if (!raw) return "La fecha de nacimiento es obligatoria.";
  const value = new Date(`${raw}T00:00:00`);
  if (Number.isNaN(value.getTime())) return "La fecha de nacimiento no es valida.";
  if (value > today) return "La fecha de nacimiento no puede estar en el futuro.";
  if (value.getFullYear() < 1900) return "La fecha de nacimiento no puede ser anterior a 1900.";

  let age = today.getFullYear() - value.getFullYear();
  const beforeBirthday =
    today.getMonth() < value.getMonth() ||
    (today.getMonth() === value.getMonth() && today.getDate() < value.getDate());
  if (beforeBirthday) age -= 1;
  if (age > MAX_HUMAN_AGE) return `La fecha implica una edad mayor a ${MAX_HUMAN_AGE} anos.`;
  return null;
}

export function validateSpeciality(raw: string): FieldError {
  const value = collapse(raw);
  if (!value) return "La especialidad es obligatoria.";
  if (value.length < SPECIALITY_MIN) return `La especialidad debe tener al menos ${SPECIALITY_MIN} caracteres.`;
  if (value.length > SPECIALITY_MAX) return `La especialidad no puede exceder ${SPECIALITY_MAX} caracteres.`;
  if (!HAS_LETTER.test(value)) return "La especialidad debe contener palabras, no solo numeros o simbolos.";
  return null;
}

/** La cedula es opcional; si viene, debe cumplir el formato oficial. */
export function validateLicense(raw: string): FieldError {
  const value = raw.trim();
  if (!value) return null;
  if (!LICENSE.test(value)) return "El formato debe ser L-YYYYMMDD-####A (Ej: L-20260526-8845A).";
  return null;
}

export function validateReason(raw: string): FieldError {
  const value = collapse(raw);
  if (!value) return "El motivo de la consulta es obligatorio.";
  if (value.length < REASON_MIN) {
    return `Faltan ${REASON_MIN - value.length} caracteres para llegar al minimo de ${REASON_MIN}.`;
  }
  if (value.length > REASON_MAX) return `El motivo no puede exceder ${REASON_MAX} caracteres.`;
  if (!HAS_LETTER.test(value)) return "El motivo debe describir la consulta, no solo numeros o simbolos.";
  return null;
}

/** Fecha de una cita: obligatoria, no pasada y dentro del horizonte de agenda. */
export function validateAppointmentDate(raw: string, today = new Date()): FieldError {
  if (!raw) return "La fecha es obligatoria.";
  const value = new Date(`${raw}T00:00:00`);
  if (Number.isNaN(value.getTime())) return "La fecha no es valida.";

  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  if (value < startOfToday) return "No se puede agendar una cita en el pasado.";

  const months = (value.getFullYear() - today.getFullYear()) * 12 + (value.getMonth() - today.getMonth());
  if (months > MAX_MONTHS_AHEAD) return "No se puede agendar con mas de dos anos de anticipacion.";
  return null;
}

export function validateRequired(raw: string, field: string): FieldError {
  return raw.trim() ? null : `${field} es obligatorio.`;
}

/** True si ningun campo del formulario tiene error. */
export function isClean(errors: Record<string, FieldError>): boolean {
  return Object.values(errors).every((error) => error === null);
}

/** Fecha maxima agendable en formato ISO, para el atributo `max` de un input. */
export function maxAppointmentDateIso(today = new Date()): string {
  const limit = new Date(today.getFullYear(), today.getMonth() + MAX_MONTHS_AHEAD, today.getDate());
  return limit.toISOString().slice(0, 10);
}
