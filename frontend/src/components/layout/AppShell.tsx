import { NavLink, Outlet } from "react-router-dom";

import { Badge } from "../ui/Badge";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/goals", label: "Goals" },
  { to: "/recovery-strain", label: "Recovery" },
  { to: "/training-log", label: "Training Log" },
  { to: "/reports/six-month", label: "6-Month" },
  { to: "/settings", label: "Settings" }
];

export function AppShell() {
  return (
    <div className="min-h-screen bg-background text-primary">
      <div className="border-b border-line bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 rounded-sm bg-accent shadow-[0_0_18px_rgba(55,221,119,0.55)]" />
              <h1 className="text-2xl font-semibold tracking-normal">EnduraSync</h1>
              <Badge>Private</Badge>
            </div>
            <p className="mt-1 text-sm text-muted">Training control center for WHOOP-derived progress.</p>
          </div>
          <nav className="flex flex-wrap gap-2">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  [
                    "rounded-md border px-3 py-2 text-sm font-medium transition",
                    isActive
                      ? "border-accent bg-accent text-black"
                      : "border-line bg-raised text-muted hover:border-accent hover:text-primary"
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
      <main className="mx-auto max-w-7xl px-5 py-7">
        <Outlet />
      </main>
    </div>
  );
}
