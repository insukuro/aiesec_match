import { NavigationBar } from "../shared/ui/NavigationBar";
import { ROUTES } from "../app/routes";

export function MainNavigation() {
  return (
    <NavigationBar
      items={[
        { to: ROUTES.results, label: "Рекомендации", icon: "✨" },
        { to: ROUTES.history, label: "История", icon: "🗂" },
        { to: ROUTES.profile, label: "Профиль", icon: "👤" },
        { to: ROUTES.settings, label: "Настройки", icon: "⚙" },
      ]}
    />
  );
}