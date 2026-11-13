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

export function LoginPage() {
  const nav = useNavigate();
  const toast = useToast();
  const { state, loginWithPassword, loginAsGuest } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { document.title = "Вход — AIESEC Match"; }, []);

  useEffect(() => {
    if (state.status === "authenticated") nav(ROUTES.results, { replace: true });
  }, [state.status, nav]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await loginWithPassword(email, password);
      nav(ROUTES.results);
    } catch (err) {
      toast.show(errorMessage(err), "error");
    } finally {
      setBusy(false);
    }
  };

  const continueAsGuest = async () => {
    setBusy(true);
    try {
      await loginAsGuest();
      nav(ROUTES.onboarding(0));
    } catch (err) {
      toast.show(errorMessage(err), "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthCard
      title="Вход"
      subtitle="Войдите, чтобы получить доступ к профилю и истории."
      footer={<span className="muted">Нет аккаунта? <Link to={ROUTES.register}>Зарегистрироваться</Link></span>}
    >
      <form className="stack" onSubmit={submit}>
        <label className="field">
          <span className="field__label">Email</span>
          <TextField value={email} onChange={setEmail} type="email" autoComplete="email" required />
        </label>
        <label className="field">
          <span className="field__label">Пароль</span>
          <PasswordField value={password} onChange={setPassword} autoComplete="current-password" />
        </label>
        <Button type="submit" size="lg" block disabled={busy}>
          {busy ? "Входим…" : "Войти"}
        </Button>
        <Button type="button" variant="text" onClick={continueAsGuest} disabled={busy}>
          Продолжить как гость
        </Button>
      </form>
    </AuthCard>
  );
}