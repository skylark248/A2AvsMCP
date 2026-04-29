import { traceEventTone, traceEventProtocol } from "./utils";
import type { TraceEvent } from "../types/api";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";
import VisibilityOffOutlinedIcon from "@mui/icons-material/VisibilityOffOutlined";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import type { ComponentType } from "react";
import type { FailureTag } from "../types/race";

/** Canonical protocol palette (D-11) */
export const protocolColor: Record<string, string> = {
  mcp: "#1976d2",
  a2a: "#7b1fa2",
  hybrid: "#2e7d32",
  baseline: "#757575",
};

/** Tone colors for trace event severity */
export const toneColor = {
  error: "#c62828",
  warning: "#ed6c02",
  success: "#2e7d32",
  info: "#757575",
} as const;

const BASELINE = "#757575";

/** Get protocol color by mode string, with fallback to baseline grey */
export function getProtocolColor(mode: string): string {
  return protocolColor[mode] ?? BASELINE;
}

/** Border color for trace event rows — tone takes priority, then protocol */
export function eventBorderColor(event: TraceEvent): string {
  const tone = traceEventTone(event);
  if (tone === "error") return toneColor.error;
  if (tone === "warning") return toneColor.warning;
  if (tone === "success") return toneColor.success;
  const proto = traceEventProtocol(event);
  return protocolColor[proto] ?? BASELINE;
}

interface FailureTagStyle {
  bg: string;
  text: string;
  Icon: ComponentType;
  label: string;
}

// UIRACE-04 + 08-UI-SPEC.md Failure Tag Color Map. Single source of truth.
// Consumed by FailureStateBadge (Plan 04) AND HeatmapScaffold (Plan 05).
// Color paired with icon + label — UIRACE-04 forbids color as sole channel.
export const failureTagColor: Record<FailureTag, FailureTagStyle> = {
  recovered:                   { bg: "#e8f5e9", text: "#1b5e20", Icon: CheckCircleOutlineIcon,   label: "Recovered" },
  gave_up:                     { bg: "#fce4ec", text: "#880e4f", Icon: CancelOutlinedIcon,        label: "Gave Up" },
  kept_going_without_noticing: { bg: "#fff3e0", text: "#e65100", Icon: VisibilityOffOutlinedIcon, label: "Kept Going (Unaware)" },
  kept_going_to_failure:       { bg: "#fbe9e7", text: "#bf360c", Icon: ErrorOutlineIcon,          label: "Kept Going to Failure" },
  indeterminate:               { bg: "#f5f5f5", text: "#424242", Icon: HelpOutlineIcon,           label: "Indeterminate" },
};
