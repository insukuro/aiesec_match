import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, type PropsWithChildren } from "react";
import { api } from "../../shared/api/endpoints";
import { getAccessToken, setAccessToken } from "../../shared/api/client";
import type { Me } from "../../shared/api/types";

export type AuthState =
  | { status: "loading" }
  | { status: "authenticated"; me: Me }
  | { status: "unknown" };

type AuthAction = { type: "authenticated"; me: Me } | { type: "unknown" };

function authReducer(_state: AuthState, action: AuthAction): AuthState {
  return action.type === "authenticated"
    ? { status: "authenticated", me: action.me }
    : { status: "unknown" };
}

interface AuthContextValue {
  state: AuthState;
  isAuthenticated: boolean;
  me: Me | null;
  refreshMe: () => Promise<void>;
  setMe: (me: Me | null) => void;
  logout: () => void;
  loginWithPassword: (email: string, password: string) => Promise<void>;
  registerWithPassword: (email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(authReducer, { status: "loading" });

  const setMe = useCallback((me: Me | null) => {
    if (!me) {
      dispatch({ type: "unknown" });
      return;
    }
    dispatch({ type: "authenticated", me });
  }, [dispatch]);

  const refreshMe = useCallback(async () => {
    if (!getAccessToken()) {
      dispatch({ type: "unknown" });
      return;
    }
    try {
      const me = await api.getMe();
      setMe(me);
    } catch (error) {
      dispatch({ type: "unknown" });
      throw error;
    }
  }, [dispatch, setMe]);

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
    dispatch({ type: "unknown" });
  }, []);

  useEffect(() => {
    void refreshMe().catch(() => undefined);
  }, [refreshMe]);

  const me = "me" in state ? state.me : null;

  const value = useMemo<AuthContextValue>(() => ({
    state,
    isAuthenticated: state.status === "authenticated",
    me,
    refreshMe,
    setMe,
    logout,
    loginWithPassword,
    registerWithPassword,
  }), [state, me, refreshMe, setMe, logout, loginWithPassword, registerWithPassword]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}