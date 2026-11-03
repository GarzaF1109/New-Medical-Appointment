import type { Page } from "@playwright/test";

/**
 * Sufijo unico para no chocar entre corridas que comparten base de datos.
 *
 * Son solo letras: `validateName` rechaza cualquier digito en un nombre de
 * persona, asi que un sufijo numerico lo hubiera invalidado en los specs de
 * pacientes y doctores.
 */
export function uniqueSuffix(): string {
  const alphabet = "abcdefghijklmnopqrstuvwxyz";
  let n = Date.now() * 1000 + Math.floor(Math.random() * 1000);
  let letters = "";
  while (n > 0) {
    letters = alphabet[n % alphabet.length] + letters;
    n = Math.floor(n / alphabet.length);
  }
  return letters;
}

/** Acepta automaticamente el `window.confirm` de las acciones de borrado. */
export function autoAcceptDialogs(page: Page): void {
  page.on("dialog", (dialog) => dialog.accept());
}

export async function goToTab(page: Page, name: "Citas" | "Pacientes" | "Doctores") {
  await page.getByRole("tab", { name }).click();
}

interface PatientInput {
  fullName: string;
  birthDate: string;
  phone?: string;
}

/** Da de alta un paciente desde el formulario de la pestana Pacientes. */
export async function createPatient(page: Page, input: PatientInput) {
  await goToTab(page, "Pacientes");
  await page.getByLabel("Nombre completo").fill(input.fullName);
  await page.getByLabel("Fecha de nacimiento").fill(input.birthDate);
  if (input.phone) {
    await page.getByLabel("Telefono de contacto").fill(input.phone);
  }
  await page.getByRole("button", { name: "Registrar paciente" }).click();
}

interface DoctorInput {
  fullName: string;
  speciality: string;
}

/** Da de alta un doctor desde el formulario de la pestana Doctores. */
export async function createDoctor(page: Page, input: DoctorInput) {
  await goToTab(page, "Doctores");
  await page.getByLabel("Nombre completo").fill(input.fullName);
  await page.getByLabel("Especialidad").fill(input.speciality);
  await page.getByRole("button", { name: "Registrar doctor" }).click();
}
