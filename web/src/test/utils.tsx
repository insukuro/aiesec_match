import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { ToastProvider } from "../shared/ui/Toast";

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
}

interface Options extends Omit<RenderOptions, "wrapper"> {
  route?: string;
  queryClient?: QueryClient;
}

export function renderWithProviders(ui: ReactElement, opts: Options = {}) {
  const qc = opts.queryClient ?? makeQueryClient();
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <ToastProvider>
          <MemoryRouter initialEntries={[opts.route ?? "/"]}>{children}</MemoryRouter>
        </ToastProvider>
      </QueryClientProvider>
    );
  }
  return { queryClient: qc, ...render(ui, { wrapper: Wrapper, ...opts }) };
}