import { expect, test } from "@playwright/test";

import { autoAcceptDialogs, createDoctor, goToTab, uniqueSuffix } from "./helpers";

test.beforeEach(async ({ page }) => {
  autoAcceptDialogs(page);
  await page.goto("/");
});

test("registra un doctor y lo muestra en el catalogo", async ({ page }) => {
  const name = `Dra. Playwright ${uniqueSuffix()}`;

  await createDoctor(page, { fullName: name, speciality: "Cardiologia" });

  await expect(page.getByRole("cell", { name })).toBeVisible();
});

test("rechaza una cedula con formato invalido", async ({ page }) => {
  await goToTab(page, "Doctores");

  await page.getByLabel("Nombre completo").fill("Dr. Formato Invalido");
  await page.getByLabel("Especialidad").fill("Dermatologia");
  const license = page.getByLabel("Cedula profesional");
  await license.fill("12345");
  await license.blur();

  await expect(page.getByText(/formato debe ser/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Registrar doctor" })).toBeDisabled();
});

test("elimina un doctor sin citas vigentes", async ({ page }) => {
  const name = `Dr. Borrable ${uniqueSuffix()}`;
  await createDoctor(page, { fullName: name, speciality: "Pediatria" });

  const row = page.getByRole("row", { name: new RegExp(name) });
  await row.getByRole("button", { name: "Eliminar" }).click();

  await expect(page.getByText(/eliminado/)).toBeVisible();
  await expect(page.getByRole("cell", { name })).toHaveCount(0);
});
