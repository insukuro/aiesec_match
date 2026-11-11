import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { qk } from "../../shared/api/queries";
import type { SubscriptionPrefs } from "../../shared/api/types";
import { Toggle } from "../../shared/ui/Toggle";
import { Button } from "../../shared/ui/Button";
import { useToast } from "../../shared/ui/Toast";

export function SubscriptionForm({ initial }: { initial: SubscriptionPrefs }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [prefs, setPrefs] = useState<SubscriptionPrefs>(initial);
  const save = useMutation({
    mutationFn: (p: SubscriptionPrefs) => api.putSubscription(p),
    onSuccess: (p) => {
      qc.setQueryData(qk.subscription, p);
      toast.show("Сохранено", "success");
    },
  });

  return (
    <div className="stack">
      <Toggle
        label="Уведомления о новых совпадениях"
        value={prefs.notify_new_matches}
        onChange={(v) => setPrefs({ ...prefs, notify_new_matches: v })}
      />
      <label className="field">
        <span className="field__label">Минимальный скор: {prefs.min_score.toFixed(2)}</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={prefs.min_score}
          onChange={(e) => setPrefs({ ...prefs, min_score: Number(e.target.value) })}
        />
      </label>
      <Button onClick={() => save.mutate(prefs)} disabled={save.isPending}>Сохранить</Button>
    </div>
  );
}