import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--color-background)",
        surface: "var(--color-surface)",
        raised: "var(--color-surface-raised)",
        line: "var(--color-line)",
        primary: "var(--color-text-primary)",
        muted: "var(--color-text-muted)",
        accent: "var(--color-accent)",
        signal: "var(--color-signal)"
      },
      boxShadow: {
        tactical: "0 18px 60px rgba(0, 0, 0, 0.32)"
      }
    }
  },
  plugins: []
} satisfies Config;

