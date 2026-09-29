import { describe, expect, it } from "vitest";

import {
  validateAppointmentDate,
  validateBirthDate,
  validateLicense,
  validateName,
  validatePhone,
  validateReason,
  validateSpeciality,
} from "@/lib/validation";

const TODAY = new Date(2026, 8, 29); // 29 de septiembre de 2026

describe("validateName", () => {
  it("acepta un nombre con acentos y ñ", () => {
    expect(validateName("José Muñoz Peña")).toBeNull();
  });

  it("acepta apostrofes y guiones", () => {
    expect(validateName("Ana O'Brien Garcia-Lopez")).toBeNull();
  });

  it("rechaza numeros", () => {
    expect(validateName("Ana123")).toBe("El nombre no puede contener numeros.");
  });

  it("rechaza simbolos", () => {
    expect(validateName("!!!@@@###")).toMatch(/solo admite letras/);
  });

  it("rechaza etiquetas HTML", () => {
    expect(validateName("<script>alert</script>")).not.toBeNull();
  });

  it("rechaza un nombre vacio", () => {
    expect(validateName("   ")).toBe("El nombre es obligatorio.");
  });

  it("rechaza un nombre demasiado corto", () => {
    expect(validateName("Al")).toMatch(/al menos 3/);
  });
});

describe("validatePhone", () => {
  it("acepta vacio porque el telefono es opcional", () => {
    expect(validatePhone("")).toBeNull();
  });

  it("acepta separadores humanos", () => {
    expect(validatePhone("(81) 1234-5678")).toBeNull();
  });

  it("rechaza letras aunque acompanen a digitos validos", () => {
    expect(validatePhone("8112345678abc")).toBe("El telefono no puede contener letras.");
  });

  it("rechaza menos de 10 digitos", () => {
    expect(validatePhone("123")).toMatch(/al menos 10 digitos/);
  });

  it("rechaza mas de 15 digitos", () => {
    expect(validatePhone("81123456789012345")).toMatch(/no puede exceder 15 digitos/);
  });
});

describe("validateBirthDate", () => {
  it("acepta una fecha plausible", () => {
    expect(validateBirthDate("1988-03-14", TODAY)).toBeNull();
  });

  it("rechaza una fecha futura", () => {
    expect(validateBirthDate("2027-01-01", TODAY)).toMatch(/futuro/);
  });

  it("rechaza una edad imposible", () => {
    expect(validateBirthDate("1900-01-01", TODAY)).toMatch(/edad mayor a 120/);
  });

  it("rechaza vacio", () => {
    expect(validateBirthDate("", TODAY)).toBe("La fecha de nacimiento es obligatoria.");
  });
});

describe("validateSpeciality", () => {
  it("acepta una especialidad real", () => {
    expect(validateSpeciality("Medicina Interna")).toBeNull();
  });

  it("rechaza solo numeros", () => {
    expect(validateSpeciality("99999")).toMatch(/palabras/);
  });

  it("rechaza solo simbolos", () => {
    expect(validateSpeciality("@@@")).toMatch(/palabras/);
  });
});

describe("validateLicense", () => {
  it("acepta vacio porque es opcional", () => {
    expect(validateLicense("")).toBeNull();
  });

  it("acepta el formato oficial", () => {
    expect(validateLicense("L-20260526-8845A")).toBeNull();
  });

  it("rechaza un formato inventado", () => {
    expect(validateLicense("ABC-123")).toMatch(/L-YYYYMMDD/);
  });
});

describe("validateReason", () => {
  it("acepta una descripcion suficiente", () => {
    expect(validateReason("Dolor de cabeza persistente")).toBeNull();
  });

  it("cuenta cuantos caracteres faltan", () => {
    expect(validateReason("gripa")).toBe(
      "Faltan 5 caracteres para llegar al minimo de 10.",
    );
  });

  it("rechaza un motivo sin letras", () => {
    expect(validateReason("1234567890")).toMatch(/no solo numeros/);
  });
});

describe("validateAppointmentDate", () => {
  it("acepta hoy mismo", () => {
    expect(validateAppointmentDate("2026-09-29", TODAY)).toBeNull();
  });

  it("rechaza una fecha pasada", () => {
    expect(validateAppointmentDate("2026-09-28", TODAY)).toMatch(/pasado/);
  });

  it("rechaza mas de dos anos de anticipacion", () => {
    expect(validateAppointmentDate("2099-01-01", TODAY)).toMatch(/dos anos/);
  });
});
