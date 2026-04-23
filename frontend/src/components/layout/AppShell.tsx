import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import CompareArrowsOutlinedIcon from "@mui/icons-material/CompareArrowsOutlined";
import InsightsOutlinedIcon from "@mui/icons-material/InsightsOutlined";
import SchoolOutlinedIcon from "@mui/icons-material/SchoolOutlined";
import PlayCircleOutlineOutlinedIcon from "@mui/icons-material/PlayCircleOutlineOutlined";
import QueryStatsOutlinedIcon from "@mui/icons-material/QueryStatsOutlined";
import SlideshowOutlinedIcon from "@mui/icons-material/SlideshowOutlined";
import TimelineOutlinedIcon from "@mui/icons-material/TimelineOutlined";
import { AppBar, Box, Button, Container, Stack, Toolbar, Typography } from "@mui/material";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useAppUi } from "../../app/ui/AppUiProvider";

const navItems = [
  { to: "/", label: "Runs", icon: <PlayCircleOutlineOutlinedIcon fontSize="small" /> },
  { to: "/learn", label: "Learn", icon: <SchoolOutlinedIcon fontSize="small" /> },
  { to: "/reports", label: "Reports", icon: <AssessmentOutlinedIcon fontSize="small" /> },
  { to: "/traces", label: "Traces", icon: <TimelineOutlinedIcon fontSize="small" /> },
  { to: "/compare", label: "Compare", icon: <CompareArrowsOutlinedIcon fontSize="small" /> },
  { to: "/trends", label: "Trends", icon: <InsightsOutlinedIcon fontSize="small" /> },
  { to: "/presentation", label: "Presentation", icon: <SlideshowOutlinedIcon fontSize="small" /> },
  { to: "/telemetry", label: "Telemetry", icon: <QueryStatsOutlinedIcon fontSize="small" /> },
];

export function AppShell() {
  const location = useLocation();
  const { isPresentationChromeHidden } = useAppUi();
  const isPresentationRoute = location.pathname === "/presentation";
  const reduceChrome = isPresentationRoute && isPresentationChromeHidden;

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: reduceChrome
          ? "linear-gradient(180deg, #fffaf4 0%, #f6eddc 100%)"
          : "radial-gradient(circle at top left, rgba(184, 92, 56, 0.14), transparent 28%), linear-gradient(180deg, #f7f1e7 0%, #efe8da 100%)",
      }}
    >
      {!reduceChrome ? (
        <AppBar
          position="sticky"
          color="transparent"
          elevation={0}
          sx={{ backdropFilter: "blur(14px)", borderBottom: "1px solid rgba(16, 32, 51, 0.08)" }}
        >
          <Toolbar sx={{ gap: 2, flexWrap: "wrap", py: 1 }}>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="overline" sx={{ letterSpacing: "0.16em", color: "secondary.main" }}>
                Protocol Learning Lab
              </Typography>
              <Typography variant="h6" sx={{ color: "primary.main" }}>
                A2A vs MCP Demo Platform
              </Typography>
            </Box>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
              {navItems.map((item) => (
                <Button
                  key={item.to}
                  component={NavLink}
                  to={item.to}
                  end={item.to === "/"}
                  startIcon={item.icon}
                  variant="text"
                  sx={{
                    color: "text.primary",
                    "&.active": {
                      bgcolor: "rgba(23, 71, 95, 0.08)",
                      color: "primary.main",
                    },
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Stack>
          </Toolbar>
        </AppBar>
      ) : null}
      <Container
        maxWidth={reduceChrome ? false : "xl"}
        sx={{ py: reduceChrome ? 2 : 4, px: reduceChrome ? { xs: 2, md: 4 } : undefined }}
      >
        <Outlet />
      </Container>
    </Box>
  );
}
