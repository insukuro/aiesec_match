export function Skeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="ui-skeleton" aria-busy="true" aria-live="polite">
      {Array.from({ length: lines }).map((_, i) => <div key={i} className="ui-skeleton__line" />)}
    </div>
  );
}