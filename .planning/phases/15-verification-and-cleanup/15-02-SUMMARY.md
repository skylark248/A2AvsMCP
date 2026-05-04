---
phase: 15-verification-and-cleanup
plan: 02
type: code-fix
status: complete
completed_date: 2026-05-04
duration_seconds: 45
---

# Phase 15 Plan 02: Fix TraceWorkspacePage DiscoveryPhasePanel Gate — Summary

## Objective

Fix TraceWorkspacePage DiscoveryPhasePanel gate: Replace scenario-string gate with event-presence check matching CompareTracesPanel pattern. This enables the discovery panel to render for imported NDJSON runs where metadata is unavailable.

## What Shipped

### `frontend/src/features/traces/TraceWorkspacePage.tsx`

Updated lines 392-413 (DiscoveryPhasePanel rendering):

**Before:**
```typescript
{detail?.summary?.scenario === "tool_discovery" ? (
  <Grid size={{ xs: 12 }}>
    {(() => {
      const allEvents = visibleResults.flatMap((r) => r.trace ?? []);
      const mcpEvents = allEvents.filter(...);
      const a2aEvents = allEvents.filter(...);
      return <DiscoveryPhasePanel mcpEvents={mcpEvents} a2aEvents={a2aEvents} scenario={detail.summary.scenario} />;
    })()}
  </Grid>
) : null}
```

**After:**
```typescript
{(() => {
  const allEvents = visibleResults.flatMap((r) => r.trace ?? []);
  const mcpEvents = allEvents.filter(
    (e) => e.event_type === "tool_discovery" && !(e as { remote_agent?: unknown }).remote_agent,
  );
  const a2aEvents = allEvents.filter(
    (e) =>
      (e.event_type === "tool_discovery" && Boolean((e as { remote_agent?: unknown }).remote_agent)) ||
      e.event_type === "a2a_remote_discovery",
  );
  const showDiscoveryPanel = mcpEvents.length > 0 || a2aEvents.length > 0;
  
  if (!showDiscoveryPanel) return null;
  
  return (
    <Grid size={{ xs: 12 }}>
      <DiscoveryPhasePanel
        mcpEvents={mcpEvents}
        a2aEvents={a2aEvents}
        scenario={detail?.summary?.scenario ?? "tool_discovery"}
      />
    </Grid>
  );
})()}
```

**Key changes:**
1. Move event filtering outside the JSX conditional
2. Compute `showDiscoveryPanel` as boolean based on event array lengths
3. Gate JSX render on `showDiscoveryPanel` value, not scenario metadata
4. Add fallback for scenario: `detail?.summary?.scenario ?? "tool_discovery"` (handles imported NDJSON runs with missing metadata)

## Why This Matters

**Before:** DiscoveryPhasePanel only rendered when `detail?.summary?.scenario === "tool_discovery"`. For imported NDJSON runs, `detail` is null, so metadata is unavailable. The panel never appeared.

**After:** DiscoveryPhasePanel renders when discovery events are present (detected via event_type), regardless of metadata availability. Works for both:
- Saved reports (with detail.summary)
- Imported NDJSON runs (detail=null)

Pattern now matches CompareTracesPanel (lines 65-73), establishing consistency across the codebase.

## Key Files Modified

| File | Lines Changed | Reason |
|------|---------------|--------|
| `frontend/src/features/traces/TraceWorkspacePage.tsx` | 392-413 | Event-presence gate replacing scenario metadata check |

## Test Results

✓ All 335 frontend tests pass (38 test files, no regressions)

## Self-Check

✓ Scenario-string gate replaced with event-presence check (lines 402-404)  
✓ Call site (line 409) passes events to DiscoveryPhasePanel  
✓ Scenario fallback added for imported runs (line 411)  
✓ Pattern matches CompareTracesPanel event filter (same logic)  
✓ TypeScript compiles cleanly  
✓ All frontend tests pass (335/335)  
✓ No regressions in TraceWorkspacePage functionality  

## Self-Check: PASSED
