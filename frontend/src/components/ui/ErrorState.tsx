export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-400 bg-red-950/30 p-4 text-sm text-red-100">
      {message}
    </div>
  );
}

