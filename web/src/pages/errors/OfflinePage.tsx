import { Link } from "react-router-dom";

export function OfflinePage() {
  return (
    <main className="page">
      <h1 className="page__title">Нет соединения</h1>
      <p className="muted">Проверьте сеть и попробуйте снова.</p>
      <Link to="/">На главную</Link>
    </main>
  );
}