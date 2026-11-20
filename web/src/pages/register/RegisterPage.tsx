import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../../features/auth/AuthContext";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import { getAccessToken } from "../../shared/api/client";
import type { ConsentKind } from "../../shared/api/types";
import { AuthCard } from "../../shared/ui/AuthCard";
import { Button } from "../../shared/ui/Button";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Skeleton } from "../../shared/ui/Skeleton";
import { TextField } from "../../shared/ui/TextField";
import { PasswordField } from "../../shared/ui/PasswordField";
import { ROUTES } from "../../app/routes";
import { useToast } from "../../shared/ui/Toast";
import { errorMessage } from "../../shared/lib/errors";
import { checkPassword } from "../../shared/lib/password";

export function RegisterPage() {
  const nav = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const { state, registerWithPassword, refreshMe } = useAuth();
  const consentsQ = useQuery({ queryKey: qk.consents, queryFn: fetchers.consents });
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [touched, setTouched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [accountCreated, setAccountCreated] = useState(false);
  const [accepted, setAccepted] = useState<Record<ConsentKind, boolean>>({
    pd_processing: false,
    marketing: false,
  });

  useEffect(() => { document.title = "Регистрация — AIESEC Match"; }, []);

  useEffect(() => {
    if (state.status === "authenticated" && !accountCreated) {
      nav(ROUTES.onboarding(0), { replace: true });
    }
  }, [accountCreated, state.status, nav]);

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const passwordCheck = checkPassword(password, emailValid ? email : undefined);
  const requiredConsentsAccepted = consentsQ.data?.consents
    .filter((consent) => consent.required)
    .every((consent) => accepted[consent.kind]) ?? false;
  const canSubmit = emailValid && passwordCheck.ok && requiredConsentsAccepted && !busy;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!canSubmit) return;
    setBusy(true);
    setAccountCreated(true);
    try {
      await registerWithPassword(email.trim().toLowerCase(), password);
      for (const consent of consentsQ.data?.consents ?? []) {
        if (accepted[consent.kind]) await api.postConsent(consent.kind, consent.version);
      }
      await refreshMe();
      toast.show("Аккаунт создан", "success");
      nav(ROUTES.onboarding(0));
    } catch (err) {
      if (getAccessToken()) {
        void queryClient.invalidateQueries({ queryKey: qk.consents });
        toast.show("Аккаунт создан, но согласия не сохранены. Завершите настройку в профиле.", "error");
        nav(ROUTES.settings, { replace: true });
      } else {
        setAccountCreated(false);
        toast.show(errorMessage(err), "error");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthCard
      title="Регистрация"
      subtitle="Создайте аккаунт, чтобы сохранять профиль, историю и подборки."
      footer={<span className="muted">Уже есть аккаунт? <Link to={ROUTES.login}>Войти</Link></span>}
    >
      <form className="stack" onSubmit={submit} noValidate>
        {consentsQ.isLoading && <Skeleton lines={4} />}
        {consentsQ.error && (
          <ErrorBanner error={consentsQ.error} onRetry={() => consentsQ.refetch()} />
        )}
        <label className="field">
          <span className="field__label">Email</span>
          <TextField
            value={email}
            onChange={setEmail}
            type="email"
            autoComplete="email"
            required
            onBlur={() => setTouched(true)}
          />
          {touched && !emailValid && email.length > 0 && (
            <span className="field__error">Введите корректный email</span>
          )}
        </label>
        <label className="field">
          <span className="field__label">Пароль</span>
          <PasswordField
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            minLength={8}
            email={emailValid ? email : undefined}
            showStrength
          />
          <span className="field__hint">Минимум 8 символов, буква и цифра</span>
        </label>
        {consentsQ.data?.consents.map((consent) => (
          <section className="ui-card stack" key={consent.kind}>
            <div>
              <h2 className="section__title">{consent.title}</h2>
              <p>{consent.text}</p>
              <p className="muted">Версия {consent.version}</p>
            </div>
            <label className="row">
              <input
                type="checkbox"
                checked={accepted[consent.kind]}
                required={consent.required}
                onChange={(event) => {
                  setAccepted((current) => ({
                    ...current,
                    [consent.kind]: event.target.checked,
                  }));
                }}
              />
              <span>{consent.label}{consent.required ? " *" : ""}</span>
            </label>
          </section>
        ))}
        <Button type="submit" size="lg" block disabled={!canSubmit}>
          {busy ? "Создаём…" : "Создать аккаунт"}
        </Button>
      </form>
    </AuthCard>
  );
}