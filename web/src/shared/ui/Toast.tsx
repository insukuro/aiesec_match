import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren } from "react";

type Tone = "info" | "success" | "error";
interface ToastItem { id: string; tone: Tone; text: string }

interface ToastContextValue {
  show: (text: string, tone?: Tone) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: PropsWithChildren) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const show = useCallback((text: string, tone: Tone = "info") => {
    const id = crypto.randomUUID();
    setItems((prev) => [...prev, { id, tone, text }]);
  }, []);

  const remove = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const ctx = useMemo(() => ({ show }), [show]);

  return (
    <ToastContext.Provider value={ctx}>
      {children}
      <div className="ui-toasts">
        {items.map((t) => <ToastRow key={t.id} item={t} onDone={() => remove(t.id)} />)}
      </div>
    </ToastContext.Provider>
  );
}

function ToastRow({ item, onDone }: { item: ToastItem; onDone: () => void }) {
  useEffect(() => {
    const id = window.setTimeout(onDone, 4000);
    return () => window.clearTimeout(id);
  }, [onDone]);
  return (
    <div className={`ui-toast ui-toast--${item.tone}`} role="status">
      {item.text}
      <button type="button" aria-label="Закрыть" onClick={onDone}>×</button>
    </div>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}