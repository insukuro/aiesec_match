import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/api/endpoints";
import { setAccessToken } from "../../shared/api/client";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";
import { useToast } from "../../shared/ui/Toast";

export function LoginPage() {
  const nav = useNavigate();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  useEffect(() => { document.title = "Вход — AIESEC Match"; }, []);

  const restore = async () => {
    setBusy(true);
    try {
      const secret = localStorage.getItem("device_secret");
      const res = await api.authAnonymous(secret);
      setAccessToken(res.access_token);
      if (res.device_secret) localStorage.setItem("device_secret", res.device_secret);
      const me = await api.getMe();
      if (me.has_profile) {
        nav(ROUTES.results);
      } else {
        nav(ROUTES.onboarding(0));
      }
    } catch {
      toast.show("Не удалось восстановить сессию", "error");
    } finally {
      setBusy(false);
    }
  };

  const tgLogin = async () => {
    const tg = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
    if (!tg?.initData) { toast.show("Telegram недоступен", "error"); return; }
    try {
      const res = await api.authTelegram(tg.initData);
      setAccessToken(res.access_token);
      nav(ROUTES.results);
    } catch {
      toast.show("Ошибка Telegram-авторизации", "error");
    }
  };

  return (
    <main className="page">
      <h1 className="page__title">Вход</h1>
      <div className="stack">
        <Button onClick={restore} disabled={busy} size="lg" block>
          {busy ? "Проверяем…" : "Продолжить на этом устройстве"}
        </Button>
        <Button variant="outline" onClick={tgLogin} size="lg" block>
          Войти через Telegram
        </Button>
      </div>
    </main>
  );
}