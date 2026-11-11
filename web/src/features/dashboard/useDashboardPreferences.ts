import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { qk } from "../../shared/api/queries";
import { DEFAULT_DASHBOARD, type DashboardPreferences } from "../../shared/api/types";

export function useDashboardPreferences() {
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: qk.dashboard,
    queryFn: async () => {
      try {
        return await api.getDashboardPreferences();
      } catch (e) {
        const status = (e as { status?: number }).status;
        if (status === 404) return DEFAULT_DASHBOARD;
        throw e;
      }
    },
  });

  const saveM = useMutation({
    mutationFn: (p: DashboardPreferences) => api.putDashboardPreferences(p),
    onSuccess: (p) => qc.setQueryData(qk.dashboard, p),
  });

  const resetM = useMutation({
    mutationFn: () => api.putDashboardPreferences(DEFAULT_DASHBOARD),
    onSuccess: (p) => qc.setQueryData(qk.dashboard, p),
  });

  return {
    data: q.data,
    isLoading: q.isLoading,
    error: q.error,
    isSaving: saveM.isPending || resetM.isPending,
    save: (p: DashboardPreferences) => saveM.mutate(p),
    reset: () => resetM.mutate(),
  };
}