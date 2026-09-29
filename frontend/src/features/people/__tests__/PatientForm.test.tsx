import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Patient } from "@/api/types";
import { PatientForm } from "@/features/people/components/PatientForm";

const EXISTING: Patient = {
  id: 1,
  fullName: "Ana Maria Lopez",
  birthDate: "1988-03-14",
  age: 38,
  phone: "+5218112345678",
};

function mockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status < 400,
    status,
    json: () => Promise.resolve(body),
  });
}

function renderForm(editing: Patient | null) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const onDone = vi.fn();

  render(
    <QueryClientProvider client={queryClient}>
      <PatientForm editing={editing} onDone={onDone} onCancelEdit={vi.fn()} />
    </QueryClientProvider>,
  );

  return { onDone };
}

function payloadOf(fetchMock: ReturnType<typeof mockFetch>) {
  const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
  return JSON.parse(init.body as string);
}

describe("PatientForm", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch(201, { id: 9 }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("precarga los datos del paciente que se esta editando", () => {
    renderForm(EXISTING);

    expect(screen.getByLabelText(/nombre completo/i)).toHaveValue("Ana Maria Lopez");
    expect(screen.getByLabelText(/fecha de nacimiento/i)).toHaveValue("1988-03-14");
  });

  it("envia la fecha de nacimiento al dar de alta", async () => {
    const fetchMock = mockFetch(201, { id: 9 });
    vi.stubGlobal("fetch", fetchMock);
    renderForm(null);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/nombre completo/i), "Sofia Herrera");
    await user.type(screen.getByLabelText(/fecha de nacimiento/i), "1992-06-18");
    await user.click(screen.getByRole("button", { name: /registrar paciente/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(payloadOf(fetchMock).birthDate).toBe("1992-06-18");
  });

  it("manda phone como null cuando se deja vacio, para borrarlo", async () => {
    const fetchMock = mockFetch(200, EXISTING);
    vi.stubGlobal("fetch", fetchMock);
    renderForm(EXISTING);
    const user = userEvent.setup();

    await user.clear(screen.getByLabelText(/telefono/i));
    await user.click(screen.getByRole("button", { name: /guardar cambios/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(payloadOf(fetchMock).phone).toBeNull();
  });

  it("edita con PATCH sobre el identificador del paciente", async () => {
    const fetchMock = mockFetch(200, EXISTING);
    vi.stubGlobal("fetch", fetchMock);
    renderForm(EXISTING);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /guardar cambios/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/patients/1");
    expect(init.method).toBe("PATCH");
  });

  it("rechaza letras en el telefono sin gastar una peticion", async () => {
    const fetchMock = mockFetch(201, { id: 9 });
    vi.stubGlobal("fetch", fetchMock);
    renderForm(null);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/telefono/i), "8112345678abc");
    await user.tab();

    expect(await screen.findByText("El telefono no puede contener letras.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rechaza un telefono con mas digitos de los permitidos", async () => {
    renderForm(null);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/telefono/i), "81123456789012345");
    await user.tab();

    expect(await screen.findByText(/no puede exceder 15 digitos/)).toBeInTheDocument();
  });

  it("rechaza numeros en el nombre", async () => {
    renderForm(null);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/nombre completo/i), "Ana123");
    await user.tab();

    expect(await screen.findByText("El nombre no puede contener numeros.")).toBeInTheDocument();
  });

  it("muestra el error que solo el backend puede detectar", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch(409, {
        status: 409,
        code: "CONFLICT",
        message: "El paciente tiene citas vigentes; cancelelas antes de eliminarlo.",
      }),
    );
    renderForm(EXISTING);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /guardar cambios/i }));

    expect(
      await screen.findByText(/El paciente tiene citas vigentes/),
    ).toBeInTheDocument();
  });

  it("impide enviar una fecha de nacimiento futura sin llegar al servidor", async () => {
    const fetchMock = mockFetch(201, { id: 9 });
    vi.stubGlobal("fetch", fetchMock);
    renderForm(null);

    // El atributo `max` del input corta el caso antes de gastar una peticion.
    expect(screen.getByLabelText(/fecha de nacimiento/i)).toHaveAttribute("max");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
