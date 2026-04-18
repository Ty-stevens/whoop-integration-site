import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { DashboardPage } from "../routes/DashboardPage";
import { GoalsPage } from "../routes/GoalsPage";
import { NotFoundPage } from "../routes/NotFoundPage";
import { RecoveryStrainPage } from "../routes/RecoveryStrainPage";
import { SixMonthReportPage } from "../routes/SixMonthReportPage";
import { SettingsPage } from "../routes/SettingsPage";
import { TrainingLogPage } from "../routes/TrainingLogPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "goals", element: <GoalsPage /> },
      { path: "recovery-strain", element: <RecoveryStrainPage /> },
      { path: "training-log", element: <TrainingLogPage /> },
      { path: "reports/six-month", element: <SixMonthReportPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> }
    ]
  }
]);
