import { traceEventTone, traceEventProtocol } from "./utils";
import type { TraceEvent } from "../types/api";

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

/** Get protocol color by mode string, with fallback to baseline grey */
export function getProtocolColor(mode: string): string {
  return protocolColor[mode] ?? protocolColor.baseline;
}

/** Border color for trace event rows — tone takes priority, then protocol */
export function eventBorderColor(event: TraceEvent): string {
  const tone = traceEventTone(event);
  if (tone === "error") return toneColor.error;
  if (tone === "warning") return toneColor.warning;
  if (tone === "success") return toneColor.success;
  const proto = traceEventProtocol(event);
  return protocolColor[proto] ?? protocolColor.baseline;
}
