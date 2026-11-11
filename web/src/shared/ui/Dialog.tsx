import { useEffect, type PropsWithChildren, type ReactNode } from "react";

export interface DialogProps {
  open: boolean;
  title: string;
  onClose: () => void;
  footer?: ReactNode;
}

export function Dialog({ open, title, onClose, footer, children }: PropsWithChildren<DialogProps>) {
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="ui-dialog" role="dialog" aria-modal="true" aria-label={title}>
      <div className="ui-dialog__backdrop" onClick={onClose} />
      <div className="ui-dialog__panel">
        <header className="ui-dialog__header">
          <h2>{title}</h2>
          <button type="button" aria-label="Закрыть" onClick={onClose}>×</button>
        </header>
        <div className="ui-dialog__body">{children}</div>
        {footer && <footer className="ui-dialog__footer">{footer}</footer>}
      </div>
    </div>
  );
}