import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { qk } from "../../shared/api/queries";
import type { FeedbackIn, RecommendationRun } from "../../shared/api/types";
import { useToast } from "../../shared/ui/Toast";

export function useSendFeedback() {
  const qc = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: (body: FeedbackIn) => api.postFeedback(body),
    onMutate: async (body) => {
      await qc.cancelQueries({ queryKey: qk.run });
      const prev = qc.getQueryData<RecommendationRun>(qk.run);
      if (prev) {
        const next: RecommendationRun = {
          ...prev,
          groups: prev.groups.map((g) => ({
            ...g,
            items: g.items.map((it) => {
              if (it.opportunity.opportunity_id !== body.opportunity_id) return it;
              if (body.signal === "liked") return { ...it, liked: true };
              if (body.signal === "hidden") return { ...it, hidden: true };
              if (body.signal === "disliked") return { ...it, hidden: true };
              return it;
            }),
          })),
        };
        qc.setQueryData(qk.run, next);
      }
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(qk.run, ctx.prev);
      toast.show("Не удалось сохранить действие", "error");
    },
    onSuccess: (_d, vars) => {
      if (vars.signal === "liked") toast.show("Добавлено в избранное", "success");
      if (vars.signal === "hidden") toast.show("Скрыто — можно вернуть в профиле", "info");
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: qk.run });
      void qc.invalidateQueries({ queryKey: qk.historyRoot });
      void qc.invalidateQueries({ queryKey: qk.analyticsRoot });
      void qc.invalidateQueries({ queryKey: ["feedback"] });
    },
  });
}

export function useRemoveFeedback() {
  const qc = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ id, signal }: { id: number; signal: "liked" | "hidden" | "disliked" }) =>
      api.deleteFeedback(id, signal),
    onSuccess: (_d, vars) => {
      if (vars.signal === "liked") toast.show("Убрано из избранного", "info");
      if (vars.signal === "hidden") toast.show("Возвращено в рекомендации", "info");
      void qc.invalidateQueries({ queryKey: qk.run });
      void qc.invalidateQueries({ queryKey: ["feedback"] });
    },
    onError: () => toast.show("Не удалось обновить", "error"),
  });
}