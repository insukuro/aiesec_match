import { errorMessage } from "../lib/errors";

export interface ErrorBannerProps {
  error: unknown;
  onRetry?: () => void;
  onReload?: () => void;
}

export function ErrorBanner({ error, onRetry, onReload }: ErrorBannerProps) {
  return (
    <div className="ui-error" role="alert">
      <div className="ui-error__text">{errorMessage(error)}</div>
      <div className="ui-error__actions">
        {onRetry && <button type="button" onClick={onRetry}>Повторить</button>}
        {onReload && <button type="button" onClick={onReload}>Загрузить актуальный</button>}
      </div>
    </div>
  );
}