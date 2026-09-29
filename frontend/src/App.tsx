import { useState } from "react";

import { AppointmentsPage } from "@/pages/AppointmentsPage";
import { DoctorsPage } from "@/pages/DoctorsPage";
import { PatientsPage } from "@/pages/PatientsPage";

const TABS = [
  { id: "appointments", label: "Citas" },
  { id: "patients", label: "Pacientes" },
  { id: "doctors", label: "Doctores" },
] as const;

type TabId = (typeof TABS)[number]["id"];

/**
 * Contenedor de la aplicacion.
 *
 * La navegacion es un estado local en lugar de un enrutador: con tres
 * pantallas, agregar `react-router` costaria mas de lo que resuelve. Si
 * aparecen URLs compartibles o rutas anidadas, ese es el momento de cambiarlo.
 */
export function App() {
  const [tab, setTab] = useState<TabId>("appointments");

  return (
    <>
      <nav className="nav" aria-label="Secciones">
        <div className="nav__inner">
          <span className="nav__brand">ClinicaApp</span>
          <div className="nav__tabs" role="tablist">
            {TABS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={tab === id}
                className={`nav__tab${tab === id ? " nav__tab--active" : ""}`}
                onClick={() => setTab(id)}
              >
                {label}
              </button>
            ))}
          </div>
          <a className="nav__link" href="/docs" target="_blank" rel="noreferrer">
            API
          </a>
        </div>
      </nav>

      {tab === "appointments" && <AppointmentsPage />}
      {tab === "patients" && <PatientsPage />}
      {tab === "doctors" && <DoctorsPage />}
    </>
  );
}
