---
status: testing
phase: all-phases-1-to-13
source: [all SUMMARY.md files, phases 1-13]
started: 2026-05-02T05:33:00.000Z
updated: 2026-05-02T05:33:00.000Z
---

## Current Test

number: 1
name: Transport badge appears on MCP/hybrid cards
expected: |
  Start the app (python serve_ui.py). Run a demo in MCP or hybrid mode.
  View the run card — a transport chip badge should appear in the card header
  showing the active transport label (e.g., "in_process").
awaiting: user response

## Tests

### 1. Transport badge appears on MCP/hybrid cards
expected: Start the app. Run a demo in MCP or hybrid mode. View the run card — a transport chip badge appears in the card header showing the active transport label (e.g., "in_process").
result: [pending]

### 2. Trace events carry phase, step_index, parallel_batch_id
expected: Run a platform scenario in MCP mode. Inspect the trace — every event carries `phase: "discovery" | "execution"`, tool_call events have sequential step_index starting at 1, and task_submit events from parallel dispatch share a single parallel_batch_id.
result: [pending]

### 3. TraceExplorer accordion shows Summary Strip + three-tier tabs
expected: Open the trace explorer on any run. Confirm the always-visible Summary Strip shows event counts. Protocol Events and Full Trace tiers are collapsed by default and expand on click.
result: [pending]

### 4. Talking-point card renders below metric chips
expected: Run a `device_failure_warranty_refund` or `vip_parallel_escalation` scenario. Below the metric chips, a colored Paper card displays the talking-point headline, sentence, and callout.
result: [pending]

### 5. Outcome metric chips show elapsed time, round-trips, agent count
expected: View any run card. Below the mode header, three chips appear: elapsed time (with protocol color background), combined round-trips count, and agent count. Old granular chips (tool_calls, a2a_messages, failures) should not appear.
result: [pending]

### 6. ParallelAgentTimeline shows stacked swimlane bars
expected: Open the trace explorer for the `vip_parallel_escalation` scenario. Between the metrics row and talking point, a horizontal timeline appears with one bar per agent showing relative execution timing (invisible offset + visible duration).
result: [pending]

### 7. CompareTracesPanel side-by-side layout works
expected: Open the Compare page with multiple runs. Mode A and Mode B dropdowns appear at the top. Two trace explorers occupy left and right columns with synced scroll.
result: [pending]

### 8. Glossary first-mention Popover then Tooltip
expected: On first visit to Run/Compare pages, hover over a glossary term (e.g., "mcp"). A Popover with definition and "Got it" button appears. Click "Got it" — on subsequent hovers, a plain Tooltip appears instead.
result: [pending]

### 9. Role-first phrasing + runtime indicator on cards
expected: View a run card. Mode header shows expanded phrasing (e.g., "Tool Access Protocol (MCP)") in dotted-underline glossary term style. A "Mock Runtime" or "OpenAI Runtime" chip appears.
result: [pending]

### 10. Failure summary chips render error-colored badges
expected: On a run with detected failures, scroll below the talking point. Error-colored Chips display failure descriptions.
result: [pending]

### 11. Race WebSocket /api/race/ws accepts connection
expected: The app is running. Connect to `/api/race/ws?run_id=test-run` (or start a race from the UI). Connection establishes and events stream without 400/401 errors.
result: [pending]

### 12. failure_mode_classifier produces locked headline
expected: Run a race (or trigger replay). Each lane shows one of the six locked outcome headlines: "recovered", "gave up", "kept going without noticing", "kept going to failure", "indeterminate", or "lane_failed".
result: [pending]

### 13. RacePage pre-race idle state
expected: Navigate to `/race`. Before starting a race, the page renders a pre-race idle state with a "Start Race" button and no lane cards visible yet.
result: [pending]

### 14. RacePage live race streams lane events
expected: Start a race from the `/race` page. Three lane cards appear (pure_mcp, pure_a2a, hybrid), each updating live as websocket events arrive. Status strip shows "Running".
result: [pending]

### 15. RacePage done state shows results + heatmap
expected: After a race completes, all three lanes show their final state with recovery metrics, characteristic failure banner appears, and heatmap renders at the bottom.
result: [pending]

### 16. Mobile <480px shows OG fallback on race replay
expected: Shrink browser to <480px wide on `/race/<run_id>` replay. The three-lane card layout is replaced with an img loading the OG PNG (or a graceful fallback if OG not generated).
result: [pending]

### 17. GET /api/race/heatmap returns structured cell data
expected: Call GET `/api/race/heatmap` (or trigger it via the UI). Response contains cells with hardness_type, lane, dominant_tag, recovery_rate (num/den), and a baseline footer with model/seed/task_ids.
result: [pending]

### 18. Race replay /race/{run_id} loads without live LLM
expected: Navigate to `/race/<a-known-run_id>`. Page loads from recorded data without making any new LLM calls. ReplayScrubber appears and controls playback.
result: [pending]

### 19. HardnessFailureHeatmap cells have correct colors and fractions
expected: View the heatmap on `/race`. Each populated cell shows the correct background color + icon from the failureTagColor map, and a recovery fraction like "12/15".
result: [pending]

### 20. GET /race/{run_id}/og.png returns 1200x630 PNG
expected: Call `/race/<run_id>/og.png` in the browser. A 1200×630 PNG renders showing the race UI snapshot. Second request returns cached file from `data/og/`.
result: [pending]

### 21. RacePage ?og=1 mode hides chrome elements
expected: Navigate to `/race/<run_id>?og=1`. Status strip, scrubber, and methodology section are hidden. Visible content is the 3-lane + banner area wrapped with data-og-anchor attribute.
result: [pending]

### 22. CopyHeadlineImageButton copies or downloads PNG
expected: On a completed race replay, click the "Copy headline image" button beside the characteristic failure banner. A PNG is either copied to clipboard or downloaded as `race-<runId>.png`.
result: [pending]

### 23. DiscoveryPhasePanel shows MCP tools + A2A agents side-by-side
expected: Run the `tool_discovery` scenario and view the trace. A two-column accordion panel appears ABOVE the trace list showing discovered tools (left) and agent cards (right) with skill chips.
result: [pending]

### 24. tool_discovery scenario unknown SKU triggers fallback
expected: Run the `tool_discovery` scenario. The unknown product "NebulaSync Hub" cannot be matched — `search_docs` appears in the trace's tools_used, and the affected tool card shows a warning border + WarningAmberRoundedIcon.
result: [pending]

### 25. SequenceDiagramView renders 5-lifeline SVG
expected: Open any trace in Sequence view (toggle in TraceExplorer). A hand-drawn SVG appears with 5 vertical lifelines: User, Orchestrator, LLM, Tool, Remote Agent. Arrows connect them showing message flow.
result: [pending]

### 26. TraceExplorer toggle between List and Sequence views
expected: In the trace explorer, a toggle control switches between "List" and "Sequence" views. Both views render their respective content without errors.
result: [pending]

### 27. AnnotatedDiffView highlights divergent rows
expected: Switch the Compare page to "Annotated diff" mode. Divergent rows show color tinting (green added, pink removed, orange border for field divergence) and "+" / "−" / "≠" glyphs in the gutter.
result: [pending]

### 28. CompareTracesPanel toggle Side-by-side vs Annotated diff
expected: In the Compare page, a toggle switches between "Side-by-side" and "Annotated diff" views. Both render correctly without errors or blank panels.
result: [pending]

### 29. DESIGN.md covers all 5 design token categories
expected: Open `.planning/DESIGN.md`. It contains sections for: (1) failureTagColor map with 5 entries, (2) methodology-as-flat rule, (3) secondary.main as replay-pill semantic, (4) role-first first-mention contract, (5) primary/secondary palette intent.
result: [pending]

### 30. App cold start boots cleanly
expected: Kill any running server. Run `python serve_ui.py`. Server starts on port 8008 without errors. Navigate to `http://localhost:8008` — the app loads with nav, and a basic demo run can be triggered.
result: [pending]

## Summary

total: 30
passed: 0
issues: 0
pending: 30
skipped: 0
blocked: 0

## Gaps

[none yet]
