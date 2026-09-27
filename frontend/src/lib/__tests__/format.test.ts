import { describe, expect, it } from "vitest";

import { formatDate, formatTime, statusClassName } from "@/lib/format";

describe("formatDate", () => {
  it("convierte una fecha ISO al formato local", () => {
    expect(formatDate("2026-10-15")).toBe("15/10/2026");
  });

  it("no se desfasa por zona horaria", () => {
    // Construir un Date con una fecha ISO la interpreta en UTC y, al
    // formatearla en America/Monterrey, retrocede un dia. Por eso se parte la
    // cadena en lugar de usar Date.
    expect(formatDate("2026-01-01")).toBe("01/01/2026");
  });
});

describe("formatTime", () => {
  it("recorta los segundos", () => {
    expect(formatTime("10:00:00")).toBe("10:00");
  });
});

describe("statusClassName", () => {
  it("asigna una clase por estado", () => {
    expect(statusClassName(1)).toContain("pending");
    expect(statusClassName(4)).toContain("cancelled");
  });

  it("degrada a la clase base ante un estado desconocido", () => {
    expect(statusClassName(99)).toBe("badge");
  });
});
