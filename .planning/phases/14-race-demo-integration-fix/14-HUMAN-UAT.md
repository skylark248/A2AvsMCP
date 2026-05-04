---
status: partial
phase: 14-race-demo-integration-fix
source: [14-VERIFICATION.md]
started: 2026-05-04T00:00:00+05:30
updated: 2026-05-04T00:00:00+05:30
---

## Current Test

[awaiting human testing]

## Tests

### 1. Live Race End-to-End Stream
expected: With app running (`python serve_ui.py`), navigate to /race. Click "Start Race" button (data-testid="race-start-button"). Button appears in pre-race state. After click: button disappears, RaceStatusStrip updates, turn events appear in all 3 lane cards within a few seconds. No 422 errors on WebSocket connect in browser console.
result: [pending]

### 2. Replay Scrubber Seek Behavior
expected: Navigate to /race/<run_id> using a known run_id from data/runs/. Drag ReplayScrubber from right (max = total_events - 1) toward 0. Lane cards update to show partial replay. At position 0, only first event applied. At max, full replay shown.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
