import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMemo, useState, type PropsWithChildren } from "react";
import { ToastProvider } from "../shared/ui/Toast";

export function AppProviders({ children }: PropsWithChildren) {
  const [client] = useState(() =>
    new QueryClient({
      defaultOptions: {
        queries: {
          retry: (count, err) => {
            const status = (err as { status?: number })?.status ?? 0;
            if (status >= 400 && status < 500) return false;
            return count < 2;
          },
          staleTime: 30_000,
          refetchOnWindowFocus: false,
        },
      },
    })
  );
  const value = useMemo(() => client, [client]);
  return (
    <QueryClientProvider client={value}>
      <ToastProvider>{children}</ToastProvider>
    </QueryClientProvider>
  );
}