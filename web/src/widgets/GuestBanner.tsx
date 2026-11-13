import { Link } from "react-router-dom";
import { ROUTES } from "../app/routes";

export function GuestBanner() {
  return (
    <div className="ui-card guest-banner" role="status">
      <div>
        <strong>Гостевой режим</strong>
        <p className="muted" style={{ margin: "var(--space-1) 0 0" }}>
          Профиль, история и подборки доступны только в аккаунте.{" "}
          <Link to={ROUTES.register}>Создать аккаунт</Link>{" "}
          или <Link to={ROUTES.login}>войти</Link>.
        </p>
      </div>
    </div>
  );
}