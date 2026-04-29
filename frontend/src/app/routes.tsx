import React, { Suspense, lazy } from "react";
import { CircularProgress, Stack } from "@mui/material";
import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { FirstMentionProvider } from "../features/race/context/FirstMentionProvider";

const LearningPage = lazy(() =>
  import("../features/learn/LearningPage").then((module) => ({
    default: module.LearningPage,
  })),
);
const RunWorkspacePage = lazy(() =>
  import("../features/run-workspace/RunWorkspacePage").then((module) => ({
    default: module.RunWorkspacePage,
  })),
);
const ReportsPage = lazy(() =>
  import("../features/reports/ReportsPage").then((module) => ({
    default: module.ReportsPage,
  })),
);
const ReportDetailPage = lazy(() =>
  import("../features/reports/ReportDetailPage").then((module) => ({
    default: module.ReportDetailPage,
  })),
);
const TrendsPage = lazy(() =>
  import("../features/trends/TrendsPage").then((module) => ({
    default: module.TrendsPage,
  })),
);
const TraceWorkspacePage = lazy(() =>
  import("../features/traces/TraceWorkspacePage").then((module) => ({
    default: module.TraceWorkspacePage,
  })),
);
const PresentationPage = lazy(() =>
  import("../features/presentation/PresentationPage").then((module) => ({
    default: module.PresentationPage,
  })),
);

const TelemetryPage = lazy(() =>
  import("../features/telemetry/TelemetryPage").then((module) => ({
    default: module.TelemetryPage,
  })),
);

const ComparePage = lazy(() =>
  import("../features/compare/ComparePage").then((module) => ({
    default: module.ComparePage,
  })),
);

const RacePage = lazy(() =>
  import("../features/race/RacePage").then((module) => ({
    default: module.RacePage,
  })),
);
function PageLoader() {
  return (
    <Stack alignItems="center" sx={{ py: 10 }}>
      <CircularProgress size={32} />
    </Stack>
  );
}

function withSuspense(element: React.ReactNode) {
  return <Suspense fallback={<PageLoader />}>{element}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      {
        index: true,
        element: withSuspense(<RunWorkspacePage />),
      },
      {
        path: "learn",
        element: withSuspense(<LearningPage />),
      },
      {
        path: "reports",
        element: withSuspense(<ReportsPage />),
      },
      {
        path: "reports/:reportName",
        element: withSuspense(<ReportDetailPage />),
      },
      {
        path: "traces",
        element: withSuspense(<TraceWorkspacePage />),
      },
      {
        path: "trends",
        element: withSuspense(<TrendsPage />),
      },
      {
        path: "presentation",
        element: withSuspense(<PresentationPage />),
      },
      {
        path: "telemetry",
        element: withSuspense(<TelemetryPage />),
      },
      {
        path: "compare",
        element: withSuspense(<ComparePage />),
      },
      {
        path: "race",
        element: withSuspense(
          <FirstMentionProvider>
            <RacePage />
          </FirstMentionProvider>,
        ),
      },
      {
        path: "race/:run_id",
        element: withSuspense(
          <FirstMentionProvider>
            <RacePage />
          </FirstMentionProvider>,
        ),
      },
    ],
  },
]);
