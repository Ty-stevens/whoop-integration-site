export function LoadingState({ message = "Loading" }: { message?: string }) {
  return <div className="rounded-md border border-line bg-raised p-4 text-sm text-muted">{message}</div>;
}

