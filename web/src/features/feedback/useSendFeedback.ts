import { useMutation } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import type { FeedbackIn } from "../../shared/api/types";

export function useSendFeedback() {
  return useMutation({
    mutationFn: (body: FeedbackIn) => api.postFeedback(body),
  });
}