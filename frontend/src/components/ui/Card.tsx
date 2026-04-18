import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-md border border-line bg-surface p-5 shadow-tactical ${className}`}>
      {children}
    </section>
  );
}

