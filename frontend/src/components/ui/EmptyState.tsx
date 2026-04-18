export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-dashed border-line bg-raised p-5">
      <p className="font-semibold text-primary">{title}</p>
      <p className="mt-2 text-sm text-muted">{body}</p>
    </div>
  );
}

