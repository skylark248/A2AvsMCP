import FullscreenExitOutlinedIcon from "@mui/icons-material/FullscreenExitOutlined";
import FullscreenOutlinedIcon from "@mui/icons-material/FullscreenOutlined";
import KeyboardCommandKeyOutlinedIcon from "@mui/icons-material/KeyboardCommandKeyOutlined";
import LaunchOutlinedIcon from "@mui/icons-material/LaunchOutlined";
import SlideshowOutlinedIcon from "@mui/icons-material/SlideshowOutlined";
import { Button, Card, CardContent, Chip, Grid, Stack, Typography } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { useAppUi } from "../../app/ui/AppUiProvider";

const presets = [
  {
    title: "Happy Path Comparison",
    description: "Lead with scorecards and trend evidence, then pivot into a clean trace walkthrough.",
    route: "/trends?mode_sort=overall",
    cta: "Open trend view",
    speakerNotes: [
      "Start with the recommended mode trend so the audience gets the high-level conclusion first.",
      "Use report detail after this to show how the scorecard maps to a single concrete run.",
      "Finish with traces only if the audience wants to see why the protocols differ operationally.",
    ],
    flow: ["Open trends", "Discuss recommended mode", "Jump to a saved report", "Optional trace walkthrough"],
    chips: ["happy path", "comparison", "executive-friendly"],
  },
  {
    title: "Failure Resilience Demo",
    description: "Show how outages and retries change recommendation logic and protocol behavior.",
    route: "/traces?mode=all",
    cta: "Open trace workspace",
    speakerNotes: [
      "Call out failure signals first so the audience knows this is not a happy-path run.",
      "Use the trace workspace to compare how MCP-heavy and A2A-heavy modes surface stress differently.",
      "Return to reports afterward to anchor the technical story back to the recommendation outcome.",
    ],
    flow: [
      "Open traces",
      "Filter to a saved failure run",
      "Compare failure signals by mode",
      "Return to report recommendation",
    ],
    chips: ["resilience", "trace-first", "technical audience"],
  },
  {
    title: "Enterprise Hybrid Story",
    description: "Center the hybrid narrative for more realistic tool-plus-delegation architecture storytelling.",
    route: "/reports?recommended=hybrid&sort=recent",
    cta: "Open report library",
    speakerNotes: [
      "Use report filters to find runs where hybrid is already the recommended demo mode.",
      "Highlight the combination of tool load and collaboration load rather than just the final answer.",
      "Bring in trace comparison only after the audience understands the business case for hybrid.",
    ],
    flow: [
      "Open filtered reports",
      "Pick a hybrid-led report",
      "Show analytics and rationale",
      "Optional trace comparison",
    ],
    chips: ["enterprise", "hybrid", "architecture story"],
  },
] as const;

export function PresentationPage() {
  const navigate = useNavigate();
  const { isPresentationChromeHidden, setPresentationChromeHidden, showToast } = useAppUi();
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selectedPreset = presets[selectedIndex] ?? presets[0];

  const togglePresentationLayout = useCallback(async () => {
    const nextChromeState = !isPresentationChromeHidden;
    setPresentationChromeHidden(nextChromeState);

    if (!document.fullscreenElement && nextChromeState) {
      try {
        await document.documentElement.requestFullscreen?.();
      } catch {
        showToast({ message: "Reduced chrome enabled. Browser fullscreen was unavailable.", severity: "info" });
        return;
      }
      showToast({ message: "Fullscreen presentation mode enabled.", severity: "success" });
      return;
    }

    if (document.fullscreenElement && !nextChromeState) {
      try {
        await document.exitFullscreen?.();
      } catch {
        showToast({ message: "Demo chrome restored.", severity: "info" });
        return;
      }
      showToast({ message: "Fullscreen presentation mode exited.", severity: "success" });
      return;
    }

    showToast({
      message: nextChromeState ? "Reduced chrome presentation mode enabled." : "Demo chrome restored.",
      severity: "success",
    });
  }, [isPresentationChromeHidden, setPresentationChromeHidden, showToast]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName ?? "";
      if (tagName === "INPUT" || tagName === "TEXTAREA" || target?.isContentEditable) {
        return;
      }

      if (event.key === "ArrowRight" || event.key.toLowerCase() === "j") {
        event.preventDefault();
        setSelectedIndex((current) => (current + 1) % presets.length);
        return;
      }

      if (event.key === "ArrowLeft" || event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSelectedIndex((current) => (current - 1 + presets.length) % presets.length);
        return;
      }

      if (event.key === "Enter") {
        event.preventDefault();
        navigate(selectedPreset.route);
        return;
      }

      if (event.key >= "1" && event.key <= String(presets.length)) {
        event.preventDefault();
        const nextIndex = Number(event.key) - 1;
        const preset = presets[nextIndex];
        setSelectedIndex(nextIndex);
        if (preset) {
          navigate(preset.route);
        }
        return;
      }

      if (event.key.toLowerCase() === "c") {
        event.preventDefault();
        const shareUrl = `${window.location.origin}${selectedPreset.route}`;
        void navigator.clipboard
          .writeText(shareUrl)
          .then(() => showToast({ message: `Copied preset link for ${selectedPreset.title}.`, severity: "success" }))
          .catch(() => showToast({ message: `Copy this preset link: ${shareUrl}`, severity: "info" }));
      }

      if (event.key.toLowerCase() === "f") {
        event.preventDefault();
        void togglePresentationLayout();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [navigate, selectedPreset, showToast, togglePresentationLayout]);

  useEffect(() => {
    return () => {
      setPresentationChromeHidden(false);
    };
  }, [setPresentationChromeHidden]);

  return (
    <Stack spacing={isPresentationChromeHidden ? 2 : 3} data-testid="presentation-page">
      <Stack
        direction={{ xs: "column", md: "row" }}
        justifyContent="space-between"
        spacing={2}
        alignItems={{ md: "flex-start" }}
      >
        <Stack spacing={1}>
          <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
            Presentation Mode
          </Typography>
          <Typography variant={isPresentationChromeHidden ? "h3" : "h2"} sx={{ color: "primary.main" }}>
            Guided demo presets and speaker-note flows are ready.
          </Typography>
          <Typography variant="body1" sx={{ maxWidth: 820, color: "text.secondary" }}>
            Presentation mode now acts like a launchpad for repeatable demos. Each preset points to a sharable filtered
            workspace and includes concise speaker notes so you can keep the story tight in front of an audience.
          </Typography>
        </Stack>
        <Button
          variant={isPresentationChromeHidden ? "contained" : "outlined"}
          startIcon={
            isPresentationChromeHidden ? (
              <FullscreenExitOutlinedIcon fontSize="small" />
            ) : (
              <FullscreenOutlinedIcon fontSize="small" />
            )
          }
          onClick={() => void togglePresentationLayout()}
        >
          {isPresentationChromeHidden ? "Exit live demo layout" : "Enter live demo layout"}
        </Button>
      </Stack>

      <Card variant="outlined">
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} justifyContent="space-between">
            <Stack spacing={0.5}>
              <Stack direction="row" spacing={1} alignItems="center">
                <KeyboardCommandKeyOutlinedIcon color="secondary" fontSize="small" />
                <Typography variant="subtitle2">Presenter Shortcuts</Typography>
              </Stack>
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                `1-3` open presets, `Left/Right` or `K/J` move focus, `Enter` opens the selected preset, `C` copies its
                link, and `F` toggles the fullscreen live-demo layout.
              </Typography>
            </Stack>
            <Chip label={`Focused preset: ${selectedIndex + 1}`} color="secondary" variant="outlined" />
          </Stack>
        </CardContent>
      </Card>

      <Grid container spacing={isPresentationChromeHidden ? 1.5 : 2}>
        {presets.map((preset, index) => {
          const selected = index === selectedIndex;
          return (
            <Grid key={preset.title} size={{ xs: 12, lg: isPresentationChromeHidden ? 12 : 4 }}>
              <Card
                sx={{
                  height: "100%",
                  border: selected ? "2px solid rgba(184, 92, 56, 0.48)" : undefined,
                  boxShadow: selected ? "0 20px 40px rgba(23, 71, 95, 0.12)" : undefined,
                  background: selected
                    ? "linear-gradient(180deg, rgba(255, 250, 244, 0.98), rgba(247, 241, 231, 0.98))"
                    : undefined,
                }}
              >
                <CardContent>
                  <Stack spacing={1.5} sx={{ height: "100%" }}>
                    <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                      <Stack direction="row" spacing={1} alignItems="center">
                        <SlideshowOutlinedIcon color="secondary" />
                        <Typography variant={isPresentationChromeHidden ? "h5" : "h6"}>{preset.title}</Typography>
                      </Stack>
                      <Chip label={`Preset ${index + 1}`} size="small" color={selected ? "secondary" : "default"} />
                    </Stack>

                    <Typography variant="body2" sx={{ color: "text.secondary" }}>
                      {preset.description}
                    </Typography>

                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      {preset.chips.map((chip) => (
                        <Chip key={chip} label={chip} size="small" />
                      ))}
                    </Stack>

                    <Grid container spacing={1.5}>
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Card variant="outlined" sx={{ height: "100%" }}>
                          <CardContent>
                            <Stack spacing={0.75}>
                              <Typography variant="subtitle2">Suggested Flow</Typography>
                              {preset.flow.map((step, flowIndex) => (
                                <Typography key={step} variant="body2" sx={{ color: "text.secondary" }}>
                                  {flowIndex + 1}. {step}
                                </Typography>
                              ))}
                            </Stack>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Card variant="outlined" sx={{ height: "100%" }}>
                          <CardContent>
                            <Stack spacing={0.75}>
                              <Typography variant="subtitle2">Speaker Notes</Typography>
                              {preset.speakerNotes.map((note) => (
                                <Typography key={note} variant="body2" sx={{ color: "text.secondary" }}>
                                  - {note}
                                </Typography>
                              ))}
                            </Stack>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>

                    <Stack direction="row" spacing={1} sx={{ mt: "auto" }}>
                      <Button
                        variant={selected ? "contained" : "outlined"}
                        onClick={() => {
                          setSelectedIndex(index);
                          navigate(preset.route);
                        }}
                        endIcon={<LaunchOutlinedIcon fontSize="small" />}
                      >
                        {preset.cta}
                      </Button>
                      <Button component={RouterLink} to={preset.route} variant="text">
                        Open in page
                      </Button>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Stack>
  );
}
