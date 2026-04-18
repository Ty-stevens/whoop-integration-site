import type { ReactNode } from "react";

export function PageHeader({
  title,
  eyebrow,
  children
}: {
  title: string;
  eyebrow?: string;
  children?: ReactNode;
}) {
  return (
    <header className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div>
        {eyebrow ? <p className="text-sm font-semibold uppercase text-accent">{eyebrow}</p> : null}
        <h2 className="mt-1 text-3xl font-semibold tracking-normal">{title}</h2>
      </div>
      {children}
    </header>
  );
}

