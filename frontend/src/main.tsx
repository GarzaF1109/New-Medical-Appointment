import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { AppointmentsPage } from "@/pages/AppointmentsPage";

import "./styles.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Los errores 4xx son deterministas: reintentarlos solo gasta peticiones.
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppointmentsPage />
    </QueryClientProvider>
  </StrictMode>,
);
