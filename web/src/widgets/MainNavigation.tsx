import { NavigationBar } from "../shared/ui/NavigationBar";
import { ROUTES } from "../app/routes";

export function MainNavigation() {
  return (
    <NavigationBar
      items={[
        { to: ROUTES.dashboard, label: "Обзор", icon: null },
        { to: ROUTES.results, label: "Подбор", icon: null },
        { to: ROUTES.history, label: "История", icon: null },
        { to: ROUTES.notifications, label: "Уведомления", icon: null },
        { to: ROUTES.profile, label: "Профиль", icon: null },
        { to: ROUTES.settings, label: "Настройки", icon: null },
      ]}
    />
  );
}