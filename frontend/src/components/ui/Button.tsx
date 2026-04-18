import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "danger";

export function Button({
  children,
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: ButtonVariant;
}) {
  const variantClass =
    variant === "primary"
      ? "border-accent bg-accent text-black hover:bg-signal"
      : variant === "danger"
        ? "border-red-400 bg-red-400 text-black hover:bg-red-300"
        : "border-line bg-raised text-primary hover:border-accent";

  return (
    <button
      {...props}
      className={[
        "rounded-md border px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50",
        variantClass,
        props.className ?? ""
      ].join(" ")}
    >
      {children}
    </button>
  );
}

