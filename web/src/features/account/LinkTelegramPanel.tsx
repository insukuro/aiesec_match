import { useMutation } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { Button } from "../../shared/ui/Button";

export function LinkTelegramPanel() {
  const link = useMutation({ mutationFn: () => api.createLinkCode() });
  return (
    <div className="stack">
      <Button onClick={() => link.mutate()} disabled={link.isPending}>Получить код</Button>
      {link.data && (
        <div className="ui-card">
          <div>Код: <strong>{link.data.code}</strong></div>
          <div className="muted">Действует {Math.round(link.data.expires_in / 60)} мин. Введите его в боте AIESEC Match.</div>
        </div>
      )}
    </div>
  );
}