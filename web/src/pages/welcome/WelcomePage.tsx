import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/api/endpoints";
import { setAccessToken } from "../../shared/api/client";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";
import { useToast } from "../../shared/ui/Toast";
import { useAuth } from "../../features/auth/AuthContext";
import { errorMessage } from "../../shared/lib/errors";

export function WelcomePage() {
  const nav = useNavigate();
  const toast = useToast();
  const { state, me, setMe } = useAuth();

  useEffect(() => {
    if (state.status === "authenticated") {
      nav(me?.has_profile ? ROUTES.dashboard : ROUTES.onboarding(0), { replace: true });
    }
  }, [state.status, me?.has_profile, nav]);
  const startTelegram = async () => {
    const tg = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
    if (!tg?.initData) { toast.show("Telegram недоступен", "error"); return; }
    try {
      const res = await api.authTelegram(tg.initData);
      setAccessToken(res.access_token);
      const me = await api.getMe();
      setMe(me);
      nav(me.has_profile ? ROUTES.dashboard : ROUTES.onboarding(0));
    } catch (error) {
      toast.show(errorMessage(error), "error");
    }
  };

  return (
    <main className="page page--entry">
      <header className="section">
        <h1 className="page__title">AIESEC Match</h1>
        <p className="muted">
          Найдём стажировку или волонтёрский проект AIESEC за 5 минут.
          Ответьте на несколько вопросов — мы подберём программы Global Talent,
          Global Teacher и Global Volunteer под ваш профиль.
        </p>
      </header>

      <div className="stack">
        <Button size="lg" onClick={() => nav(ROUTES.register)} block>Создать аккаунт</Button>
        <Button variant="outline" size="lg" onClick={() => nav(ROUTES.login)} block>Войти</Button>
        {(window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp?.initData && (
          <Button variant="text" onClick={startTelegram}>Войти через Telegram</Button>
        )}
      </div>

      <footer className="section muted" style={{ fontSize: "var(--fs-caption)" }}>
        Продолжая, вы сможете заполнить профиль и получить персональные рекомендации.
      </footer>
    </main>
  );
}