import { describe, expect, it } from "vitest";

import { ApiError } from "@/api/ApiError";

describe("ApiError", () => {
  it("identifica un conflicto de agenda", () => {
    const error = new ApiError({
      status: 409,
      code: "CONFLICT",
      message: "El doctor ya tiene una cita en ese horario.",
    });

    expect(error.isConflict).toBe(true);
  });

  it("identifica un fallo de validacion", () => {
    const error = new ApiError({ status: 422, code: "VALIDATION_ERROR", message: "Invalido" });

    expect(error.isValidation).toBe(true);
  });

  it("localiza el mensaje de un campo concreto", () => {
    const error = new ApiError({
      status: 422,
      code: "VALIDATION_ERROR",
      message: "Datos invalidos",
      details: [{ field: "reason", message: "Muy corto" }],
    });

    expect(error.messageForField("reason")).toBe("Muy corto");
  });

  it("devuelve undefined para un campo sin error", () => {
    const error = new ApiError({ status: 422, code: "VALIDATION_ERROR", message: "x" });

    expect(error.messageForField("date")).toBeUndefined();
  });
});
