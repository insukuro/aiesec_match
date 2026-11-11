import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { qk } from "../../shared/api/queries";

export function useCreateRecommendations() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.createRecommendations(crypto.randomUUID(), { mode: "sync", limit_per_programme: 10 }),
    onSuccess: (run) => qc.setQueryData(qk.run, run),
  });
}