import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="page">
      <h1 className="page__title">Страница не найдена</h1>
      <Link to="/">На главную</Link>
    </main>
  );
}