import { useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { qk } from "../../shared/api/queries";

export function useCreateRecommendations() {
  const qc = useQueryClient();
  const idempotencyKey = useRef<string | null>(null);
  return useMutation({
    mutationFn: () => {
      idempotencyKey.current ??= crypto.randomUUID();
      return api.createRecommendations(idempotencyKey.current, { mode: "sync", limit_per_programme: 10 });
    },
    onSuccess: (run) => {
      idempotencyKey.current = null;
      qc.setQueryData(qk.run, run);
    },
  });
}