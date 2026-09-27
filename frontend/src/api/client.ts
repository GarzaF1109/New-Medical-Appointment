import { ApiError } from "./ApiError";
import type { ApiErrorBody } from "./types";

const API_BASE = "/api/v1";

/**
 * Realiza una peticion a la API y normaliza cualquier fallo a `ApiError`.
 *
 * Es el unico punto del frontend que conoce `fetch`. Los hooks y componentes
 * trabajan contra funciones tipadas, no contra respuestas HTTP crudas.
 */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(
      (body as ApiErrorBody | null) ?? {
        status: response.status,
        code: "UNKNOWN_ERROR",
        message: "No se pudo contactar al servidor.",
      },
    );
  }

  return body as T;
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, payload: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(payload) }),
  patch: <T>(path: string, payload: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(payload) }),
  put: <T>(path: string) => request<T>(path, { method: "PUT" }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),
};
