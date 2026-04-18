export function ProgressBar({
  value,
  color = "var(--color-accent)"
}: {
  value: number;
  color?: string;
}) {
  const clamped = Math.max(0, Math.min(value, 100));

  return (
    <div className="h-3 overflow-hidden rounded-sm bg-black/40">
      <div className="h-full rounded-sm" style={{ width: `${clamped}%`, background: color }} />
    </div>
  );
}

