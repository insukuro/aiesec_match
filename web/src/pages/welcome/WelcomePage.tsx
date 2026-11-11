import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import { setAccessToken } from "../../shared/api/client";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";
import { useToast } from "../../shared/ui/Toast";

export function WelcomePage() {
  const nav = useNavigate();
  const toast = useToast();
  const { data: me } = useQuery({ queryKey: qk.me, queryFn: fetchers.me, retry: 0, staleTime: 30_000 });

  const startAnonymously = async () => {
    try {
      const secret = localStorage.getItem("device_secret");
      const res = await api.authAnonymous(secret);
      setAccessToken(res.access_token);
      if (res.device_secret) localStorage.setItem("device_secret", res.device_secret);
      nav(ROUTES.onboarding(0));
    } catch {
      toast.show("Не удалось начать. Попробуйте ещё раз.", "error");
    }
  };

  const startTelegram = async () => {
    const tg = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
    if (!tg?.initData) { toast.show("Telegram недоступен", "error"); return; }
    try {
      const res = await api.authTelegram(tg.initData);
      setAccessToken(res.access_token);
      nav(me?.has_profile ? ROUTES.results : ROUTES.onboarding(0));
    } catch {
      toast.show("Не удалось войти через Telegram", "error");
    }
  };

  return (
    <main className="page">
      <header className="section">
        <h1 className="page__title">AIESEC Match</h1>
        <p className="muted">
          Найдём стажировку или волонтёрский проект AIESEC за 5 минут.
          Ответьте на несколько вопросов — мы подберём программы Global Talent,
          Global Teacher и Global Volunteer под ваш профиль.
        </p>
      </header>

      <div className="stack">
        <Button size="lg" onClick={startAnonymously} block>Начать</Button>
        <Button variant="outline" size="lg" onClick={() => nav(ROUTES.login)} block>Войти</Button>
        <Button variant="text" onClick={startTelegram}>Продолжить через Telegram</Button>
      </div>

      <footer className="section muted" style={{ fontSize: "var(--fs-caption)" }}>
        Нажимая «Начать», вы принимаете{" "}
        <Link to="/legal/privacy">политику обработки персональных данных</Link>.
      </footer>
    </main>
  );
}