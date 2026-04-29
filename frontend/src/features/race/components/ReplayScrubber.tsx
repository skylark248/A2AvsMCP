/**
 * ReplayScrubber — MUI Slider with throttled aria-live announcements.
 * D-49: throttle to 1 announcement per 200ms during drag; full announcement on release.
 * UI-SPEC line 50: minimum hit area 40px.
 * UI-SPEC line 128: prefers-reduced-motion disables CSS transitions.
 */

import type React from "react";
import { Box, Slider, Stack, Typography } from "@mui/material";
import { useEffect, useRef, useState } from "react";

const ANNOUNCE_THROTTLE_MS = 200;

export function ReplayScrubber({
  value,
  max,
  onScrub,
}: {
  value: number;
  max: number;
  onScrub: (turnIndex: number) => void;
}) {
  // Live announcement text — throttled during drag, full on release (D-49).
  const [announceText, setAnnounceText] = useState<string>(
    `Turn ${value} of ${max}`,
  );
  const lastAnnounceRef = useRef<number>(0);
  const pendingValueRef = useRef<number | null>(null);

  // Keep announcement in sync when the controlled `value` prop changes from outside.
  useEffect(() => {
    setAnnounceText(`Turn ${value} of ${max}`);
  }, [value, max]);

  const toSingleValue = (raw: number | number[]): number =>
    Array.isArray(raw) ? (raw[0] ?? 0) : raw;

  const handleChange = (_evt: Event, raw: number | number[]) => {
    const next = toSingleValue(raw);
    onScrub(next);

    const now = Date.now();
    pendingValueRef.current = next;
    if (now - lastAnnounceRef.current >= ANNOUNCE_THROTTLE_MS) {
      // Throttle gate: enough time has elapsed — announce now.
      setAnnounceText(`Turn ${next} of ${max}`);
      lastAnnounceRef.current = now;
      pendingValueRef.current = null;
    }
    // Otherwise: pending value recorded; will be flushed on release.
  };

  // onChangeCommitted fires on drag release (mouseup / touchend / keyup).
  // Flush the pending value regardless of throttle (D-49 + CONTEXT specifics line 117).
  const handleChangeCommitted = (
    _evt: Event | React.SyntheticEvent,
    raw: number | number[],
  ) => {
    const next = toSingleValue(raw);
    setAnnounceText(`Turn ${next} of ${max}`);
    lastAnnounceRef.current = Date.now();
    pendingValueRef.current = null;
  };

  return (
    <Stack spacing={1} sx={{ px: 2, py: 1 }}>
      {/* UI-SPEC line 50: minimum hit area 40px around the Slider */}
      <Box sx={{ minHeight: 40 }} data-testid="race-scrubber">
        <Slider
          value={value}
          min={0}
          max={max}
          step={1}
          onChange={handleChange}
          onChangeCommitted={handleChangeCommitted}
          aria-label="Replay turn scrubber"
          sx={{
            /* UI-SPEC line 128: disable transitions for prefers-reduced-motion users */
            "@media (prefers-reduced-motion: reduce)": {
              transitionDuration: "0ms !important",
              "& .MuiSlider-thumb, & .MuiSlider-track": {
                transitionDuration: "0ms !important",
              },
            },
          }}
        />
      </Box>

      {/* aria-live="polite" — throttled during drag, full on release (D-49) */}
      <Box aria-live="polite" data-testid="race-scrubber-announce">
        <Typography variant="caption">{announceText}</Typography>
      </Box>
    </Stack>
  );
}
