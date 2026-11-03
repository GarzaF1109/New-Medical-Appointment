import { expect, test } from "@playwright/test";

import { autoAcceptDialogs, createDoctor, createPatient, goToTab, uniqueSuffix } from "./helpers";

function tomorrowIso(): string {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date.toISOString().slice(0, 10);
}

async function scheduleAppointment(
  page: import("@playwright/test").Page,
  options: {
    patientName: string;
    doctorLabel: string;
    date: string;
    startTime: string;
    reason: string;
  },
) {
  await goToTab(page, "Citas");
  // El filtro de la agenda tambien tiene un <select> etiquetado "Doctor";
  // hay que acotar al formulario de alta para no chocar con el de filtros.
  const form = page.locator("form", { hasText: "Agendar cita" });
  await form.getByLabel("Paciente").selectOption({ label: options.patientName });
  await form.getByLabel("Doctor").selectOption({ label: options.doctorLabel });
  await form.getByLabel("Fecha").fill(options.date);
  await form.getByLabel("Hora de inicio").fill(options.startTime);
  await form.getByLabel("Motivo de la consulta").fill(options.reason);
  await form.getByRole("button", { name: "Agendar cita" }).click();
}

test.beforeEach(async ({ page }) => {
  autoAcceptDialogs(page);
  await page.goto("/");
});

test("camino feliz: agenda, confirma, reagenda, cancela y elimina una cita", async ({ page }) => {
  const suffix = uniqueSuffix();
  const patientName = `Paciente Automatizado ${suffix}`;
  const doctorName = `Doctor Automatizado ${suffix}`;
  const doctorLabel = `Dr(a). ${doctorName} — Medicina General`;
  const date = tomorrowIso();

  await createPatient(page, { fullName: patientName, birthDate: "1992-02-02", phone: "8112345678" });
  await createDoctor(page, { fullName: doctorName, speciality: "Medicina General" });

  await scheduleAppointment(page, {
    patientName,
    doctorLabel,
    date,
    startTime: "10:00",
    reason: "Consulta de control programada por Playwright",
  });

  await expect(page.getByText(/Cita registrada/)).toBeVisible();
  const row = page.getByRole("row", { name: new RegExp(`${patientName}.*${doctorName}`) });
  await expect(row).toBeVisible();
  await expect(row.getByText("Pendiente")).toBeVisible();

  await row.getByRole("button", { name: "Confirmar" }).click();
  await expect(page.getByText(/confirmada/)).toBeVisible();
  await expect(row.getByText("Confirmada")).toBeVisible();

  await row.getByRole("button", { name: "Reagendar" }).click();
  const rescheduleRow = page.locator("tr.row--editing");
  // La fila de reagendado repite las etiquetas "Fecha"/"Hora de inicio" del
  // formulario de arriba, asi que hay que acotar la busqueda a esta fila.
  await rescheduleRow.getByLabel("Hora de inicio").fill("15:00");
  await rescheduleRow.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByText(/reagendad/i)).toBeVisible();

  await row.getByRole("button", { name: "Cancelar" }).click();
  await expect(page.getByText(/cancelada/)).toBeVisible();
  await expect(row.getByText("Cancelada")).toBeVisible();

  await row.getByRole("button", { name: "Eliminar" }).click();
  await expect(page.getByText(/Cita.*eliminada/)).toBeVisible();
});

test("rechaza un traslape de horario con 409", async ({ page }) => {
  const suffix = uniqueSuffix();
  const patientA = `Paciente Conflicto A ${suffix}`;
  const patientB = `Paciente Conflicto B ${suffix}`;
  const doctorName = `Doctor Conflicto ${suffix}`;
  const doctorLabel = `Dr(a). ${doctorName} — Traumatologia`;
  const date = tomorrowIso();

  await createPatient(page, { fullName: patientA, birthDate: "1992-02-02", phone: "8112345678" });
  await createPatient(page, { fullName: patientB, birthDate: "1993-03-03", phone: "8112345679" });
  await createDoctor(page, { fullName: doctorName, speciality: "Traumatologia" });

  await scheduleAppointment(page, {
    patientName: patientA,
    doctorLabel,
    date,
    startTime: "11:00",
    reason: "Primera cita que ocupa el horario de las 11",
  });
  await expect(page.getByText(/Cita registrada/)).toBeVisible();

  await scheduleAppointment(page, {
    patientName: patientB,
    doctorLabel,
    date,
    startTime: "11:00",
    reason: "Segunda cita que choca con el mismo horario",
  });

  const form = page.locator("form", { hasText: "Agendar cita" });
  await expect(form.getByRole("alert").filter({ hasText: /CONFLICT|ya tiene una cita/i })).toBeVisible();
});
