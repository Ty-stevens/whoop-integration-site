import type { ReactNode } from "react";

export function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-md border border-line bg-raised px-2 py-1 text-xs font-semibold uppercase text-muted">
      {children}
    </span>
  );
}

