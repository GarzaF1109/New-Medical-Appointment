import { expect, test } from "@playwright/test";

import { autoAcceptDialogs, createPatient, goToTab, uniqueSuffix } from "./helpers";

test.beforeEach(async ({ page }) => {
  autoAcceptDialogs(page);
  await page.goto("/");
});

test("registra un paciente y lo muestra en el catalogo", async ({ page }) => {
  const name = `Ana Playwright ${uniqueSuffix()}`;

  await createPatient(page, { fullName: name, birthDate: "1990-05-15", phone: "8112345678" });

  await expect(page.getByRole("cell", { name })).toBeVisible();
});

test("rechaza un nombre con digitos antes de enviar", async ({ page }) => {
  await goToTab(page, "Pacientes");

  await page.getByLabel("Nombre completo").fill("Paciente123");
  await page.getByLabel("Fecha de nacimiento").fill("1990-05-15");
  await page.getByLabel("Nombre completo").blur();

  await expect(page.getByText("no puede contener numeros")).toBeVisible();
  await expect(page.getByRole("button", { name: "Registrar paciente" })).toBeDisabled();
});

test("edita el telefono de un paciente existente", async ({ page }) => {
  const name = `Beto Playwright ${uniqueSuffix()}`;
  await createPatient(page, { fullName: name, birthDate: "1985-01-01", phone: "8112345678" });

  const row = page.getByRole("row", { name: new RegExp(name) });
  await row.getByRole("button", { name: "Editar" }).click();

  const phoneField = page.getByLabel("Telefono de contacto");
  await phoneField.fill("8199998888");
  await page.getByRole("button", { name: "Guardar cambios" }).click();

  await expect(page.getByText(/actualizado/)).toBeVisible();
  await expect(row.getByText("8199998888")).toBeVisible();
});

test("elimina un paciente sin citas vigentes", async ({ page }) => {
  const name = `Carla Playwright ${uniqueSuffix()}`;
  await createPatient(page, { fullName: name, birthDate: "1995-03-20" });

  const row = page.getByRole("row", { name: new RegExp(name) });
  await row.getByRole("button", { name: "Eliminar" }).click();

  await expect(page.getByText(/eliminado/)).toBeVisible();
  await expect(page.getByRole("cell", { name })).toHaveCount(0);
});
