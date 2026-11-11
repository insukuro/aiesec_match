import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/api/endpoints";
import { setAccessToken } from "../../shared/api/client";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";
import { useToast } from "../../shared/ui/Toast";

export function RegisterPage() {
  const nav = useNavigate();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  useEffect(() => { document.title = "Регистрация — AIESEC Match"; }, []);

  const register = async () => {
    setBusy(true);
    try {
      const res = await api.authAnonymous(localStorage.getItem("device_secret"));
      setAccessToken(res.access_token);
      if (res.device_secret) localStorage.setItem("device_secret", res.device_secret);
      toast.show("Аккаунт создан", "success");
      nav(ROUTES.onboarding(0));
    } catch {
      toast.show("Не удалось создать аккаунт", "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="page">
      <h1 className="page__title">Регистрация</h1>
      <p className="muted">
        В этой версии аккаунт создаётся автоматически — без email и пароля.
        Вы всегда сможете вернуться к нему на этом устройстве.
      </p>
      <Button onClick={register} disabled={busy} size="lg" block>
        {busy ? "Создаём…" : "Создать аккаунт"}
      </Button>
    </main>
  );
}