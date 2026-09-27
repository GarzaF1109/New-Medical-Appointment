import type { ReactNode } from "react";

interface AlertProps {
  variant: "success" | "error" | "warning" | "info";
  title?: string;
  children: ReactNode;
  onDismiss?: () => void;
}

/** Mensaje destacado para retroalimentar el resultado de una accion. */
export function Alert({ variant, title, children, onDismiss }: AlertProps) {
  return (
    <div className={`alert alert--${variant}`} role="alert">
      <div>
        {title && <strong>{title}</strong>}
        <div>{children}</div>
      </div>
      {onDismiss && (
        <button type="button" className="alert__close" onClick={onDismiss} aria-label="Cerrar">
          ×
        </button>
      )}
    </div>
  );
}
