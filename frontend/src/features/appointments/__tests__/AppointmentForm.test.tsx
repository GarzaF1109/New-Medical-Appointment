import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Doctor, Patient } from "@/api/types";
import { AppointmentForm } from "@/features/appointments/components/AppointmentForm";

const PATIENTS: Patient[] = [
  {
    id: 1,
    fullName: "Ana Maria Lopez",
    birthDate: "1988-03-14",
    age: 38,
    phone: "+5218112345678",
  },
  { id: 3, fullName: "Lucia Sin Telefono", birthDate: "2001-07-23", age: 25, phone: null },
];

const DOCTORS: Doctor[] = [
  {
    id: 1,
    fullName: "Elena Navarro",
    displayName: "Dr(a). Elena Navarro",
    speciality: "Cardiologia",
    medicalLicenseNumber: null,
  },
];

function renderForm(onScheduled = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  render(
    <QueryClientProvider client={queryClient}>
      <AppointmentForm patients={PATIENTS} doctors={DOCTORS} onScheduled={onScheduled} />
    </QueryClientProvider>,
  );

  return { onScheduled };
}

async function fillValidForm() {
  const user = userEvent.setup();
  await user.selectOptions(screen.getByLabelText(/paciente/i), "1");
  await user.selectOptions(screen.getByLabelText(/doctor/i), "1");
  await user.type(screen.getByLabelText(/fecha/i), "2026-12-15");
  await user.type(screen.getByLabelText(/hora de inicio/i), "10:00");
  await user.type(screen.getByLabelText(/motivo/i), "Dolor de cabeza persistente");
  return user;
}

function mockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status < 400,
    status,
    json: () => Promise.resolve(body),
  });
}

describe("AppointmentForm", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch(201, {}));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("marca a los pacientes sin telefono en el selector", () => {
    renderForm();

    expect(screen.getByRole("option", { name: /Lucia Sin Telefono \(sin telefono\)/ }))
      .toBeInTheDocument();
  });

  it("avisa cuando el motivo aun es demasiado corto", async () => {
    renderForm();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/motivo/i), "gripa");

    expect(screen.getByText(/Faltan 5 caracteres/)).toBeInTheDocument();
  });

  it("envia la hora con segundos, como espera la API", async () => {
    const fetchMock = mockFetch(201, {
      id: 1,
      patientName: "Ana Maria Lopez",
      notificationSent: true,
    });
    vi.stubGlobal("fetch", fetchMock);
    renderForm();

    const user = await fillValidForm();
    await user.click(screen.getByRole("button", { name: /agendar cita/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const payload = JSON.parse(init.body as string);
    expect(payload.startTime).toBe("10:00:00");
  });

  it("informa cuando la notificacion no pudo entregarse", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch(201, { id: 1, patientName: "Lucia Sin Telefono", notificationSent: false }),
    );
    const { onScheduled } = renderForm();

    const user = await fillValidForm();
    await user.click(screen.getByRole("button", { name: /agendar cita/i }));

    await waitFor(() =>
      expect(onScheduled).toHaveBeenCalledWith(
        expect.stringContaining("no se pudo notificar"),
      ),
    );
  });

  it("muestra el conflicto de horario que solo el backend puede detectar", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch(409, {
        status: 409,
        code: "CONFLICT",
        message: "El doctor ya tiene una cita en ese horario.",
      }),
    );
    renderForm();

    const user = await fillValidForm();
    await user.click(screen.getByRole("button", { name: /agendar cita/i }));

    expect(
      await screen.findByText("El doctor ya tiene una cita en ese horario."),
    ).toBeInTheDocument();
  });
});
