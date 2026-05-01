import { keyframes } from "@emotion/react";
import { Alert, Box, Chip, Typography, useMediaQuery, useTheme } from "@mui/material";
import { useEffect, useRef, useState } from "react";

import { getProtocolColor, toneColor } from "../../lib/trace/eventColors";
import type { TraceEvent } from "../../lib/types/api";
import {
  isTraceFailureEvent,
  traceEventActor,
  traceEventProtocol,
  traceLabel,
} from "../../lib/trace/utils";

// ---------------------------------------------------------------------------
// Props interface (verbatim from UI-SPEC lines 150-156)
// ---------------------------------------------------------------------------
export interface SequenceDiagramViewProps {
  events: TraceEvent[];
  pinnedEventId?: string | null;
  onPinEvent?: (eventId: string | null) => void;
  protocol?: "mcp" | "a2a" | "hybrid";
}

// ---------------------------------------------------------------------------
// Module-level constants (UI-SPEC Spacing scale)
// ---------------------------------------------------------------------------
const LANES = ["User", "Orchestrator", "LLM", "Tool", "Remote Agent"] as const;
type Lane = (typeof LANES)[number];
const LANE_WIDTH = 192; // px (UI-SPEC: 24 × 8)
const LANE_HEADER_Y = 24;
const FIRST_ARROW_Y = 48; // 2xl token
const ROW_HEIGHT = 32;
const HIT_AREA_HEIGHT = 24; // a11y minimum, UI-SPEC Spacing exception
const TOTAL_WIDTH = LANE_WIDTH * LANES.length; // 960

// ---------------------------------------------------------------------------
// Draw-in animation (W-1 mitigation — emotion keyframes, NOT <style> tag)
// ---------------------------------------------------------------------------
const drawIn = keyframes`
  from { stroke-dashoffset: 1000; }
  to   { stroke-dashoffset: 0; }
`;

// ---------------------------------------------------------------------------
// Lane mapping helper (12-RESEARCH.md Code Examples §"Lane mapping helper")
// Case-insensitive (W-2 mitigation: backend may emit "User" capitalized or
// "orchestrator-1" with suffix — bare equality misses these).
// ---------------------------------------------------------------------------
function laneOf(event: TraceEvent): Lane | null {
  const actor = traceEventActor(event);
  const a = actor.toLowerCase();

  // User
  if (event.event_type === "user_input" || a === "user" || a.startsWith("user")) {
    return "User";
  }

  // Orchestrator
  if (
    a === "orchestrator" ||
    a.startsWith("orchestrator") ||
    a === "agent" ||
    a === "planner" ||
    a === "router" ||
    a === "system"
  ) {
    return "Orchestrator";
  }

  // LLM
  if (
    event.event_type.startsWith("llm_") ||
    a === "llm" ||
    a === "claude" ||
    a.startsWith("llm")
  ) {
    return "LLM";
  }

  // Remote Agent (check before Tool — remote_agent truthy means A2A)
  if (
    event.remote_agent ||
    event.event_type.startsWith("a2a_remote_") ||
    a.startsWith("remote")
  ) {
    return "Remote Agent";
  }

  // Tool
  if (event.tool || event.server) {
    return "Tool";
  }

  // Unmapped — emit console.warn and return null to trigger Alert
  console.warn(
    "[SequenceDiagramView] unmapped actor",
    actor,
    "for event",
    event.event_type,
  );
  return null;
}

// ---------------------------------------------------------------------------
// Turn index coercion (same as diffAlign.ts)
// ---------------------------------------------------------------------------
function turnIndexOf(event: TraceEvent): number {
  return Number((event as { turn_index?: unknown }).turn_index ?? 0);
}

// ---------------------------------------------------------------------------
// Lane X center position
// ---------------------------------------------------------------------------
function laneX(lane: Lane): number {
  const idx = LANES.indexOf(lane);
  return idx * LANE_WIDTH + LANE_WIDTH / 2;
}

// ---------------------------------------------------------------------------
// Derive source lane heuristic
// Source: if event.sender is set, map sender via laneOf rules; else default to
// "Orchestrator" for tool calls and "User" for user_input. This heuristic keeps
// the diagram useful without requiring a dedicated source field on every event.
// ---------------------------------------------------------------------------
function sourceLaneOf(event: TraceEvent): Lane {
  // If a sender field exists, create a synthetic event-like object to map it
  if (event.sender) {
    const senderLower = String(event.sender).toLowerCase();
    if (senderLower === "user" || senderLower.startsWith("user")) return "User";
    if (
      senderLower === "orchestrator" ||
      senderLower.startsWith("orchestrator") ||
      senderLower === "agent" ||
      senderLower === "system" ||
      senderLower === "planner" ||
      senderLower === "router"
    )
      return "Orchestrator";
    if (senderLower === "llm" || senderLower === "claude" || senderLower.startsWith("llm"))
      return "LLM";
    if (senderLower.startsWith("remote")) return "Remote Agent";
  }

  // Heuristic defaults
  if (event.event_type === "user_input") return "User";
  if (event.tool || event.server || event.event_type === "tool_call") return "Orchestrator";
  return "Orchestrator";
}

// ---------------------------------------------------------------------------
// Label truncation (48 chars + ellipsis per UI-SPEC)
// ---------------------------------------------------------------------------
function buildLabel(event: TraceEvent): string {
  const base = traceLabel(event);
  const suffix = event.tool ?? event.remote_agent ?? "";
  const full = suffix ? `${base} · ${suffix}` : base;
  return full.length > 48 ? full.slice(0, 47) + "…" : full;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function SequenceDiagramView({
  events,
  pinnedEventId = null,
  onPinEvent,
  protocol,
}: SequenceDiagramViewProps): JSX.Element {
  const prefersReducedMotion = useMediaQuery("(prefers-reduced-motion: reduce)");
  const theme = useTheme();
  const [liveText, setLiveText] = useState("");
  const prevPinnedRef = useRef<string | null>(null);

  // aria-live announcement on pin change
  useEffect(() => {
    if (pinnedEventId === prevPinnedRef.current) return;
    prevPinnedRef.current = pinnedEventId ?? null;

    if (pinnedEventId === null) {
      setLiveText("Pin cleared.");
    } else {
      // Find event for announcement
      const event = events.find((e) => String(e.index) === pinnedEventId);
      if (event) {
        setLiveText(`Pinned: ${traceLabel(event)}, turn ${turnIndexOf(event)}`);
      }
    }
  }, [pinnedEventId, events]);

  // ---------------------------------------------------------------------------
  // Empty state
  // ---------------------------------------------------------------------------
  if (events.length === 0) {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          py: 6,
          gap: 1,
        }}
      >
        <Typography variant="body2" color="text.disabled">
          No events to diagram
        </Typography>
        <Typography variant="body2" color="text.disabled">
          Run the scenario to populate the sequence diagram.
        </Typography>
      </Box>
    );
  }

  // ---------------------------------------------------------------------------
  // Classify events into rows
  // ---------------------------------------------------------------------------
  interface ArrowRow {
    event: TraceEvent;
    targetLane: Lane;
    sourceLane: Lane;
    turnIdx: number;
    isSelf: boolean;
    unmapped: boolean;
  }

  let unmappedCount = 0;
  const rows: ArrowRow[] = events.map((event) => {
    const target = laneOf(event);
    const unmapped = target === null;
    if (unmapped) unmappedCount++;
    const targetLane: Lane = target ?? "Tool"; // fallback for render
    const src = sourceLaneOf(event);
    const isSelf = src === targetLane;
    return {
      event,
      targetLane,
      sourceLane: src,
      turnIdx: turnIndexOf(event),
      isSelf,
      unmapped,
    };
  });

  const svgHeight = FIRST_ARROW_Y + events.length * ROW_HEIGHT + 32;

  const secondaryMain = theme.palette.secondary.main;

  return (
    <>
      {/* aria-live announcement region (off-screen) */}
      <Box
        sx={{ position: "absolute", left: -9999, width: 1, height: 1, overflow: "hidden" }}
        role="status"
        aria-live="polite"
      >
        {liveText}
      </Box>

      {/* Warning Alert for unmapped events */}
      {unmappedCount > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Some events couldn't be placed on a lifeline — see console for details.
        </Alert>
      )}

      <Box sx={{ overflowX: "auto", width: "100%" }}>
        <svg
          width="100%"
          viewBox={`0 0 ${TOTAL_WIDTH} ${svgHeight}`}
          role="img"
          aria-label="Sequence diagram of trace events"
          style={{ display: "block", minWidth: TOTAL_WIDTH }}
        >
          {/* === Layer 1: Lifelines + Lane headers (decorative) === */}
          <g aria-hidden="true">
            {LANES.map((lane) => {
              const x = laneX(lane);
              return (
                <g key={lane}>
                  {/* Lane header */}
                  <text
                    x={x}
                    y={LANE_HEADER_Y}
                    textAnchor="middle"
                    fontSize={11}
                    fontWeight={600}
                    fill={theme.palette.text.primary}
                  >
                    {lane}
                  </text>
                  {/* Lifeline */}
                  <line
                    x1={x}
                    y1={FIRST_ARROW_Y}
                    x2={x}
                    y2={svgHeight - 16}
                    stroke="rgba(16, 32, 51, 0.18)"
                    strokeWidth={1}
                    strokeDasharray="4 4"
                    aria-hidden="true"
                  />
                </g>
              );
            })}
          </g>

          {/* === Layer 2: Event arrows === */}
          <g>
            {rows.map((row, i) => {
              const { event, sourceLane, targetLane, turnIdx, isSelf } = row;
              const isPinned = pinnedEventId === String(event.index);
              const y = FIRST_ARROW_Y + i * ROW_HEIGHT;
              const sx = laneX(sourceLane);
              const tx = laneX(targetLane);

              // Stroke color (B-2 mitigation)
              const eventProto = traceEventProtocol(event);
              const isNarrowProto =
                eventProto === "mcp" || eventProto === "a2a" || eventProto === "hybrid";
              const strokeColor = isTraceFailureEvent(event)
                ? toneColor.warning
                : isNarrowProto
                  ? getProtocolColor(eventProto)
                  : getProtocolColor(protocol ?? "baseline");

              const strokeWidth = isPinned ? 2 : 1.5;
              const labelText = buildLabel(event);
              const ariaLabel = `${sourceLane} → ${targetLane}: ${traceLabel(event)}, turn ${turnIdx}`;

              // Hit area bounds
              const hitX = isSelf ? Math.min(sx, tx) - 4 : Math.min(sx, tx);
              const hitW = isSelf ? 32 : Math.abs(tx - sx);

              return (
                <g
                  key={`${event.index}-${event.event_type}`}
                  role="button"
                  tabIndex={0}
                  aria-label={ariaLabel}
                  onClick={() => onPinEvent?.(isPinned ? null : String(event.index))}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onPinEvent?.(isPinned ? null : String(event.index));
                    }
                  }}
                  // Draw-in animation (gated on reduced-motion)
                  // sx prop doesn't work on SVG <g>; apply via style when reduced motion is off
                  style={
                    prefersReducedMotion
                      ? undefined
                      : {
                          animation: `${drawIn} 200ms ease-out forwards`,
                          strokeDasharray: 1000,
                        }
                  }
                >
                  {/* Transparent hit area */}
                  <rect
                    x={hitX}
                    y={y - HIT_AREA_HEIGHT / 2}
                    width={hitW}
                    height={HIT_AREA_HEIGHT}
                    fill="transparent"
                    style={{ cursor: "pointer" }}
                  />

                  {/* Pinned highlight rect */}
                  {isPinned && (
                    <rect
                      x={hitX - 2}
                      y={y - HIT_AREA_HEIGHT / 2 - 2}
                      width={hitW + 4}
                      height={HIT_AREA_HEIGHT + 4}
                      stroke={secondaryMain}
                      strokeWidth={4}
                      fill="none"
                      rx={4}
                    />
                  )}

                  {/* Arrow line (or loop for self-messages) */}
                  {isSelf ? (
                    // Self-message: 24px loop arc on the right side of the lifeline
                    <path
                      d={`M ${sx},${y - 8} a 12,12 0 1,1 0.01,0`}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      fill="none"
                    />
                  ) : (
                    <>
                      <line
                        x1={sx}
                        y1={y}
                        x2={tx}
                        y2={y}
                        stroke={strokeColor}
                        strokeWidth={strokeWidth}
                      />
                      {/* Arrowhead at target end */}
                      {tx > sx ? (
                        <polygon
                          points={`${tx},${y} ${tx - 8},${y - 4} ${tx - 8},${y + 4}`}
                          fill={strokeColor}
                        />
                      ) : (
                        <polygon
                          points={`${tx},${y} ${tx + 8},${y - 4} ${tx + 8},${y + 4}`}
                          fill={strokeColor}
                        />
                      )}
                    </>
                  )}

                  {/* Arrow label */}
                  <text
                    x={isSelf ? sx + 20 : (sx + tx) / 2}
                    y={y - 6}
                    textAnchor="middle"
                    fontSize={12}
                    fontWeight={400}
                    fill={theme.palette.text.primary}
                  >
                    {labelText}
                  </text>

                  {/* Pinned chip (foreignObject) */}
                  {isPinned && (
                    <foreignObject
                      x={Math.max(sx, tx) + 8}
                      y={y - 12}
                      width={80}
                      height={24}
                    >
                      <Chip label="Pinned" size="small" color="secondary" />
                    </foreignObject>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </Box>
    </>
  );
}
