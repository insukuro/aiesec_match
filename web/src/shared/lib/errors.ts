import { ApiError } from "../api/client";
import type { Problem } from "../api/types";

export function asProblem(err: unknown): Problem | null {
  if (err instanceof ApiError) return err.problem;
  if (err instanceof Error) return { type: "about:blank", title: err.message, status: 0 };
  return null;
}

export function errorMessage(err: unknown): string {
  const p = asProblem(err);
  if (!p) return "Неизвестная ошибка";
  switch (p.type) {
    case "/problems/validation": return "Проверьте поля формы";
    case "/problems/unauthorized": return "Нужно войти заново";
    case "/problems/consent-required": return "Требуется согласие на обработку данных";
    case "/problems/profile-incomplete": return "Профиль заполнен не полностью";
    case "/problems/version-conflict": return "Профиль изменён в другом месте";
    case "/problems/rate-limited": return "Слишком много запросов";
    case "/problems/matcher-unavailable":
    case "/problems/matcher-timeout":
      return "Сервис подбора временно недоступен";
    default: return p.detail || p.title;
  }
}