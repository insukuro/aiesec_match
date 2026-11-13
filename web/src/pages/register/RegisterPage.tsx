import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthContext";
import { AuthCard } from "../../shared/ui/AuthCard";
import { Button } from "../../shared/ui/Button";
import { TextField } from "../../shared/ui/TextField";
import { PasswordField } from "../../shared/ui/PasswordField";
import { ROUTES } from "../../app/routes";
import { useToast } from "../../shared/ui/Toast";
import { errorMessage } from "../../shared/lib/errors";
import { checkPassword } from "../../shared/lib/password";

export function RegisterPage() {
  const nav = useNavigate();
  const toast = useToast();
  const { state, registerWithPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [touched, setTouched] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => { document.title = "Регистрация — AIESEC Match"; }, []);

  useEffect(() => {
    if (state.status === "authenticated") nav(ROUTES.onboarding(0), { replace: true });
  }, [state.status, nav]);

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const passwordCheck = checkPassword(password, emailValid ? email : undefined);
  const canSubmit = emailValid && passwordCheck.ok && !busy;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!canSubmit) return;
    setBusy(true);
    try {
      await registerWithPassword(email.trim().toLowerCase(), password);
      toast.show("Аккаунт создан", "success");
      nav(ROUTES.onboarding(0));
    } catch (err) {
      toast.show(errorMessage(err), "error");
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
        <Button type="submit" size="lg" block disabled={!canSubmit}>
          {busy ? "Создаём…" : "Создать аккаунт"}
        </Button>
      </form>
    </AuthCard>
  );
}