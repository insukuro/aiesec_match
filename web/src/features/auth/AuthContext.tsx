import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren } from "react";
import { api } from "../../shared/api/endpoints";
import { getAccessToken, setAccessToken } from "../../shared/api/client";
import type { Me } from "../../shared/api/types";

type AuthState =
  | { status: "loading" }
  | { status: "guest"; me: Me }
  | { status: "authenticated"; me: Me }
  | { status: "unknown"; me: null };

interface AuthContextValue {
  state: AuthState;
  isGuest: boolean;
  isAuthenticated: boolean;
  refreshMe: () => Promise<void>;
  setMe: (me: Me | null) => void;
  logout: () => void;
  loginAsGuest: () => Promise<void>;
  loginWithPassword: (email: string, password: string) => Promise<void>;
  registerWithPassword: (email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  const setMe = useCallback((me: Me | null) => {
    if (!me) {
      setState({ status: "unknown", me: null });
      return;
    }
    setState({ status: me.is_anonymous ? "guest" : "authenticated", me });
  }, []);

  const refreshMe = useCallback(async () => {
    if (!getAccessToken()) {
      setState({ status: "unknown", me: null });
      return;
    }
    try {
      const me = await api.getMe();
      setMe(me);
    } catch {
      setAccessToken(null);
      setState({ status: "unknown", me: null });
    }
  }, [setMe]);

  const loginAsGuest = useCallback(async () => {
    const res = await api.authAnonymous(localStorage.getItem("device_secret"));
    setAccessToken(res.access_token);
    if (res.device_secret) localStorage.setItem("device_secret", res.device_secret);
    await refreshMe();
  }, [refreshMe]);

  const loginWithPassword = useCallback(async (email: string, password: string) => {
    const res = await api.authLogin(email, password);
    setAccessToken(res.access_token);
    await refreshMe();
  }, [refreshMe]);

  const registerWithPassword = useCallback(async (email: string, password: string) => {
    const res = await api.authRegister(email, password);
    setAccessToken(res.access_token);
    await refreshMe();
  }, [refreshMe]);

  const logout = useCallback(() => {
    setAccessToken(null);
    setState({ status: "unknown", me: null });
  }, []);

  useEffect(() => { void refreshMe(); }, [refreshMe]);

  const value = useMemo<AuthContextValue>(() => ({
    state,
    isGuest: state.status === "guest",
    isAuthenticated: state.status === "authenticated",
    refreshMe,
    setMe,
    logout,
    loginAsGuest,
    loginWithPassword,
    registerWithPassword,
  }), [state, refreshMe, setMe, logout, loginAsGuest, loginWithPassword, registerWithPassword]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}