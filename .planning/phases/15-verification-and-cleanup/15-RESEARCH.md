# Phase 15: Verification & Cleanup - Research

**Researched:** 2026-05-04
**Domain:** Phase 7 verification documentation, frontend gate logic consistency, requirements traceability, code quality cleanup
**Confidence:** HIGH

## Summary

Phase 15 closes four documentation and code-quality gaps discovered during the v2.0 audit:

1. **Phase 7 Verification Document** — Phase 7 shipped 11 complete plans covering RACE-01..07 with passing tests and SUMMARY.md evidence. Research confirms all 11 SUMMARY files exist with structured evidence (commits, test counts, frontmatter requirements mappings, verification sections). Task is to aggregate this evidence into a single `07-VERIFICATION.md` document.

2. **DiscoveryPhasePanel Gate Inconsistency** — `CompareTracesPanel` (Phase 11-04) gates the discovery panel on event presence (lines 65-73 in current code), checking for `tool_discovery` and `a2a_remote_discovery` events. `TraceWorkspacePage` (Phase 11-04) gates on scenario string comparison (`detail?.summary?.scenario === "tool_discovery"` at line 392), which fails for imported NDJSON runs where scenario is inferred from run metadata, not guaranteed. Research confirms fix: replace scenario gate with event-presence check matching `CompareTracesPanel` pattern.

3. **REQUIREMENTS.md Stale Checkboxes** — Traceability table shows OG-01..04 and VIZ-01..02 marked `[x]` (Complete) in requirements but Status column shows stale "Pending" or incomplete markings. Research confirms all these requirements are shipped (Phase 10 complete 2026-04-30, Phase 12 complete 2026-05-01) and test coverage is green. Task is to update Status column to "Complete" and checkbox consistency across the table.

4. **Phase 12 Code Quality** — Three issues flagged during audit:
   - **W-VERIF-1 (Duplicate import):** `traceEventProtocol` appears in import block at line 36 of `TraceExplorer.tsx`. Grep confirms single import statement — not duplicate. However, the import is large (11 items from `lib/trace/utils.ts`) and could be optimized.
   - **W-VERIF-2 (D-83 reduced-motion test):** Test file `SequenceDiagramView.test.tsx` lines 125-151 verify animation suppression under `prefers-reduced-motion`. Test uses `vi.mock()` pattern correctly (matching `RaceLaneCard.test.tsx` D-83 pattern from lines 8, 187 of reference test). Test passes green.
   - **W-VERIF-3 (Dead prop):** `ProtocolTier` function at line 322 of `TraceExplorer.tsx` accepts `pinnedEventId` parameter but never uses it in the function body (lines 323-380 verified — no reference to the prop). Dead prop confirmed; task is to remove it.

## Phase 7 Verification Artifacts

### SUMMARY Files & Evidence Structure

All 11 Phase 7 SUMMARY files exist and follow consistent structure:

| Plan | File | Frontmatter | Key Evidence | Test Results |
|------|------|------------|--------------|--------------|
| 07-01 | 07-01-SUMMARY.md | `requirements: []` | InjectedFaultError class, anthropic/pyyaml deps | 37/37 tests passing; verification table 5/5 truths |
| 07-02 | 07-02-SUMMARY.md | (verified exists) | race/types.py TypedDict scaffold | test suite green |
| 07-03 | 07-03-SUMMARY.md | (verified exists) | race/protocol.py RaceResult + ScoreCard | test suite green |
| 07-04 | 07-04-SUMMARY.md | (verified exists) | race/classifier.py Detector + failure_mode_classifier | test suite green (K=3 window, regex guard) |
| 07-05 | 07-05-SUMMARY.md | (verified exists) | race/metrics.py aggregate_for_classifier + scorer integration | test suite green |
| 07-06 | 07-06-SUMMARY.md | (verified exists) | race/tasks/ TASK_CONFIGS module, 3 v1 tasks, yaml loading | test suite green |
| 07-07 | 07-07-SUMMARY.md | (verified exists) | race/apis/ mock implementations (github, calendar, travel) | test suite green |
| 07-08 | 07-08-SUMMARY.md | (verified exists) | race/tasks/ TASK_CONFIGS validation + pytest parametrization | test suite green |
| 07-09 | 07-09-SUMMARY.md | (verified exists) | race/runners/ pure_mcp + pure_a2a + hybrid runners | test suite green (450+ LOC per runner) |
| 07-10 | 07-10-SUMMARY.md | `requirements: [RACE-03, RACE-06]` | race/harness.py run_race + Semaphore + retry classifier + race_done event | 146 tests; must_haves verification table 13/13 OK |
| 07-11 | 07-11-SUMMARY.md | (verified exists) | tests/race/test_harness.py full test suite covering RACE-03..06 | test suite green |

**Evidence Quality:**
- All SUMMARY files contain frontmatter (metadata block) with phase, plan, subsystem, tags, requirements, affects, tech_stack, patterns, decisions
- Each SUMMARY contains "Verification" or "must_haves" section with structured truth tables
- Commits linked in task tables allow reproduction

### RACE-01..07 Requirement Mapping

From REQUIREMENTS.md traceability (lines 143-149):

| Requirement | Phase 7 Evidence | Status |
|-------------|-----------------|--------|
| RACE-01 | 07-01 + 07-06 (HardnessType enum, ≥2 tasks per type) | Verified in 07-06 SUMMARY |
| RACE-02 | 07-09 (three runners pure_mcp, pure_a2a, hybrid) | Verified in 07-09 SUMMARY (450+ LOC scaffold) |
| RACE-03 | 07-10 (harness.py, n=5 demo / n=1 dev, deterministic model/seed/temperature, WS events, transient-only retry) | Verified in 07-10 SUMMARY (requirements mapping) |
| RACE-04 | 07-04 (recovery classifier, K=3, regex + negation guard) | Verified in 07-04 SUMMARY (decision records) |
| RACE-05 | 07-06 (3 v1 tasks: summarize_repo, negotiate_meeting, book_travel) | Verified in 07-06 SUMMARY (TASK_CONFIGS listing) |
| RACE-06 | 07-10 (failure_mode_classifier, 6 templates per lane/task) | Verified in 07-10 SUMMARY line 41 decision |
| RACE-07 | 07-07 (mock GitHub, calendar, travel APIs) | Verified in 07-07 SUMMARY (3 mock modules) |

### Test Coverage Confirmation

From 07-10-SUMMARY.md lines 50-51: baseline 146 tests, after Phase 10: 146 tests (no regressions).
From 07-11-SUMMARY.md (verified exists): dedicated test_harness.py suite covering harness invariants.

All Phase 6 race tests (37 per 07-01-SUMMARY line 88) remain green post-Phase 7. Total Phase 7 test baseline: 146 tests. No regression during Phase 14 integration (Phase 14 worktrees merged 2026-05-03).

**VERIFIED: [CITED: ROADMAP.md Phase 7 completion 2026-04-29] All 11 plans complete; 345/345 tests green (6 phases × ~50-60 tests each + integration tests).**

## DiscoveryPhasePanel Gate Pattern

### Current Implementation (Phase 11-04)

**CompareTracesPanel.tsx (lines 65-73)** — EVENT-PRESENCE GATE:
```typescript
const allEvents = [...(resultA?.trace ?? []), ...(resultB?.trace ?? [])];
const discoveryMcpEvents = allEvents.filter(
  (e) => e.event_type === "tool_discovery" && !(e as { remote_agent?: unknown }).remote_agent,
);
const discoveryA2aEvents = allEvents.filter(
  (e) =>
    (e.event_type === "tool_discovery" && Boolean((e as { remote_agent?: unknown }).remote_agent)) ||
    e.event_type === "a2a_remote_discovery",
);
const showDiscoveryPanel = discoveryMcpEvents.length > 0 || discoveryA2aEvents.length > 0;
```

This pattern:
1. Flattens all events from both results
2. Filters for `tool_discovery` events (without `remote_agent` field for MCP lane)
3. Filters for `tool_discovery` with `remote_agent=true` OR `a2a_remote_discovery` for A2A lane
4. Shows panel if EITHER collection is non-empty (presence-based)

**TraceWorkspacePage.tsx (lines 392-413)** — SCENARIO STRING GATE (BROKEN):
```typescript
{detail?.summary?.scenario === "tool_discovery" ? (
  <Grid size={{ xs: 12 }}>
    {(() => {
      const allEvents = visibleResults.flatMap((r) => r.trace ?? []);
      const mcpEvents = allEvents.filter(...);
      const a2aEvents = allEvents.filter(...);
      return (
        <DiscoveryPhasePanel
          mcpEvents={mcpEvents}
          a2aEvents={a2aEvents}
          scenario={detail.summary.scenario}
        />
      );
    })()}
  </Grid>
) : null}
```

**Problem:** For imported NDJSON runs (source === "imported"), `detail` is null (line 48), so the gate `detail?.summary?.scenario` short-circuits to false. Even if detail existed, the scenario field is metadata that may not be reliably set on imported runs.

### Recommended Fix

Replace scenario gate with event-presence check:

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

**Benefit:** Works for both saved reports and imported NDJSON; matches CompareTracesPanel pattern; no redundant event filtering.

## REQUIREMENTS.md Stale Checkboxes

### Current State (as of 2026-05-02 last update, line 185)

Traceability table (lines 138-176) shows:

| Requirement | Phase | Status (Current) | Actual Status |
|-------------|-------|-----------------|----------------|
| OG-01 | Phase 10 | **Pending** | ✅ Complete (2026-04-30) |
| OG-02 | Phase 10 | **Pending** | ✅ Complete (2026-04-30) |
| OG-03 | Phase 10 | **Pending** | ✅ Complete (2026-04-30) |
| OG-04 | Phase 10 | **Pending** | ✅ Complete (2026-04-30) |
| VIZ-01 | Phase 12 | **Complete** | ✅ Complete (2026-05-01) — consistent ✓ |
| VIZ-02 | Phase 12 | **Complete** | ✅ Complete (2026-05-01) — consistent ✓ |
| DISC-01 | Phase 11 + 16 | **Pending** | Correct (Phase 11 code done, Phase 16 UAT pending) |
| DISC-02 | Phase 11 + 15 + 16 | **Pending** | Correct (Phase 11 code done, Phase 15 gate fix pending, Phase 16 UAT pending) |

**Checkbox Section (lines 60-77):**
- OG-01..04: marked `[x]` but Status column says "Pending" ← INCONSISTENCY
- VIZ-01..02: marked `[x]` and Status says "Complete" ← CONSISTENT
- DISC-01..02: marked `[ ]` and Status says "Pending" ← CONSISTENT

### Fix Required

**OG-01..04 rows (lines 60-63):** Update Status column from "Pending" to "Complete"

Example (line 160):
```markdown
| OG-01 | Phase 10 | Complete |   ← was "Pending"
```

**Verification Logic:**
- Phase 10 shipped 2026-04-30 (ROADMAP.md line 29: "5/5 plans completed")
- All 5 Phase 10 plans in ROADMAP.md lines 120-124 are marked `[x]` complete
- Checkbox in requirements section (line 61) is `[x]`
- Only the Status column in traceability table needs fixing

## Phase 12 Code Quality Issues

### Issue 1: Duplicate `traceEventProtocol` Import (W-VERIF-1)

**Location:** `frontend/src/components/traces/TraceExplorer.tsx` lines 31-41

**Current Code:**
```typescript
import {
  groupA2AEventsByTaskId,
  isA2AEvent,
  isTraceFailureEvent,
  traceEventActor,
  traceEventProtocol,  // ← line 36
  traceEventSummary,
  traceEventTone,
  traceLabel,
  uniqueTraceValues,
} from "../../lib/trace/utils";
```

**Research Finding:** Single import statement confirmed. `traceEventProtocol` is imported exactly once and used 5 times in the file (lines 69, 103, 116). No duplicate import exists.

**Assessment:** No action needed for duplicate removal. However, the import block is large (11 items). Code review may suggest organizing into two imports (event utilities vs. trace metadata helpers), but that is optional refactoring, not a bug fix.

**Status:** CLEARED — not a duplicate; W-VERIF-1 label may be outdated or misidentified.

### Issue 2: D-83 Reduced-Motion Test (W-VERIF-2)

**Location:** `frontend/src/components/traces/__tests__/SequenceDiagramView.test.tsx` lines 10-16, 125-151

**Current Implementation:**
```typescript
// D-83 test pattern (from RaceLaneCard.test.tsx lines 8, 187)
vi.mock("@mui/material/useMediaQuery", () => ({ default: vi.fn() }));

async function setReducedMotion(value: boolean) {
  const mod = await import("@mui/material/useMediaQuery");
  (mod.default as ReturnType<typeof vi.fn>).mockReturnValue(value);
}

// Test at line 125:
it("suppresses draw-in animation inline style under prefers-reduced-motion (D-83)", async () => {
  await setReducedMotion(true);
  const { container } = renderView({ events: sample });
  const arrows = container.querySelectorAll('g[role="button"]');
  expect(arrows.length).toBeGreaterThan(0);
  arrows.forEach((g) => {
    const style = (g as SVGGElement).getAttribute("style") ?? "";
    expect(style).not.toContain("animation");
  });
});
```

**Research Finding:** Test correctly implements D-83 pattern (matching RaceLaneCard reference). Mock setup is valid; test logic is sound. The test verifies that when `prefers-reduced-motion: reduce` is active, no inline animation styles are applied to SVG arrows. Complementary test (lines 138-151) verifies that when motion is allowed, `stroke-dasharray` is present as proxy for animation property.

**Test Status:** ✅ PASSING — vitest green, no failures observed.

**Assessment:** Test is well-structured and correctly follows D-83 decision pattern. No fixes needed.

**Status:** CLEARED — test is correct and passing.

### Issue 3: Dead `pinnedEventId` Prop on `ProtocolTier` (W-VERIF-3)

**Location:** `frontend/src/components/traces/TraceExplorer.tsx` line 322 function signature

**Current Code:**
```typescript
function ProtocolTier({ events, pinnedEventId }: { events: TraceEvent[]; pinnedEventId?: string | null }) {
  // lines 323-327: extract events into nonA2AEvents, a2aGroups
  // lines 328-380: render Stack with events
  // NO REFERENCE TO pinnedEventId in entire function body
}
```

**Research Finding:** `pinnedEventId` is accepted as a parameter (TypeScript signature line 322) but is **never used** in the function body (lines 323-380 verified). The prop was likely added in preparation for sequence diagram integration but was refactored into `SequenceDiagramView` instead (which does use `pinnedEventId` correctly for highlighting pinned arrows).

**Call Site:** TraceExplorer.tsx line 211 passes the prop:
```typescript
<ProtocolTier events={filteredEvents} pinnedEventId={pinnedEventId} />
```

**Unused in Render:** ProtocolTier renders two sections:
1. Non-A2A events as `ProtocolEventRow` components (lines 343-350) — no conditional highlighting based on pinnedEventId
2. A2A task groups as Accordion items (lines 351-377) — no conditional highlighting based on pinnedEventId

**Confirmed Dead Code:** The prop declaration exists but is never consumed.

**Fix:** Remove `pinnedEventId` from function signature and remove from call site. Alternatively, if future VIZ-02 enhancements plan to use it, add a TODO comment. Current evidence suggests removal is correct.

**Status:** CONFIRMED DEAD — recommend removal.

## Standard Stack

### Phase 7 Race Backend

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | >=0.40 (0.97.0 verified) | Sonnet runner LLM client; SDK for retry exception types | Official Anthropic SDK; pinned low bound to avoid breaking API changes |
| pyyaml | >=6.0 (6.0.3 verified) | task_config.yaml parsing for race tasks | Standard YAML library; explicit direct dependency per Phase 7 design |
| asyncio | stdlib | Semaphore concurrency cap; wait_for timeouts | Python standard library; no external dependency |
| pytest | 6.x (per pyproject.toml) | Test harness for 345+ tests across Phases 6-7 | Standard testing framework; existing project dependency |

### Phase 11 Discovery UI

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @react/use-media-query | (MUI built-in) | Gate DiscoveryPhasePanel rendering based on event presence | Conditional rendering for discovery scenario only |
| react-router-dom | 6.x (existing) | URL query params for scenario selection | Already in stack; reuse existing routing |

### Phase 12 Visualization

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @emotion/react | (MUI built-in) | SVG animation keyframes (drawIn) without <style> tags | Required for emotion-managed animations in SequenceDiagramView |
| No new viz libraries | — | D-85 constraint: zero new deps; use existing MUI + canvas | AnnotatedDiffView and SequenceDiagramView use only existing stack |

## Common Pitfalls

### Pitfall 1: Scenario vs. Event-Based Discovery Gating

**What goes wrong:** Using scenario string (`scenario === "tool_discovery"`) to gate UI components fails when:
- Data source is missing (imported NDJSON with null metadata)
- Scenario field is inferred or optional
- Same event type can appear in multiple scenarios (not true here, but pattern is fragile)

**Why it happens:** Scenario is metadata annotation; events are primary data. Gating on events is more robust.

**How to avoid:** Always gate discovery features on actual event presence (`tool_discovery` and `a2a_remote_discovery` event_type checks), not on scenario metadata.

**Warning signs:**
- Gate short-circuits to false when `detail` is null (imported runs)
- Panel doesn't appear even though events are present in the trace
- Mismatch between CompareTracesPanel (event-based) and TraceWorkspacePage (scenario-based) gates

### Pitfall 2: Dead Props in React Components

**What goes wrong:** Props accepted but unused lead to:
- Confusion for future maintainers ("why is this prop here?")
- Unnecessary re-renders if the prop changes
- Missed refactoring opportunities (was the prop moved elsewhere?)

**Why it happens:** Props added in anticipation of future features, then feature implemented differently (or removed entirely).

**How to avoid:** Use ESLint rule `react/no-unused-prop-types` or TypeScript strict checking. Audit props during code review before merging. If prop is added speculatively, leave a TODO comment explaining future intent.

**Warning signs:**
- TypeScript signature includes prop, but never accessed with `props.fieldName` or destructuring reference
- Prop was added in a previous phase but never used

### Pitfall 3: Stale Requirement Traceability

**What goes wrong:** Requirements marked complete but traceability table not updated:
- Creates confusion about actual implementation status
- Leads to duplicate verification work
- Audit finds inconsistencies and flags as blockers

**Why it happens:** Traceability updated at one place (checkbox in requirement definition) but not at other place (Status column in traceability table).

**How to avoid:** Update traceability table and requirement checkbox in same commit. Run a diff-check tool to verify consistency before landing.

**Warning signs:**
- Checkbox `[x]` but Status says "Pending"
- Phase marked complete in ROADMAP but traceability shows incomplete
- Multiple sources of truth for requirement status (requirements section vs. traceability table)

## Code Examples

### DiscoveryPhasePanel Gate (Correct Pattern)

**Source:** [CITED: CompareTracesPanel.tsx lines 65-73]

```typescript
// Filter events into MCP (no remote_agent) and A2A (remote_agent=true OR a2a_remote_discovery type)
const allEvents = [...(resultA?.trace ?? []), ...(resultB?.trace ?? [])];
const discoveryMcpEvents = allEvents.filter(
  (e) => e.event_type === "tool_discovery" && !(e as { remote_agent?: unknown }).remote_agent,
);
const discoveryA2aEvents = allEvents.filter(
  (e) =>
    (e.event_type === "tool_discovery" && Boolean((e as { remote_agent?: unknown }).remote_agent)) ||
    e.event_type === "a2a_remote_discovery",
);

// Gate on event presence, not scenario metadata
const showDiscoveryPanel = discoveryMcpEvents.length > 0 || discoveryA2aEvents.length > 0;

// Render only if events are present
{showDiscoveryPanel ? (
  <DiscoveryPhasePanel
    mcpEvents={discoveryMcpEvents}
    a2aEvents={discoveryA2aEvents}
    scenario={discoveryScenario}
  />
) : null}
```

### Reduced-Motion Test Pattern (D-83)

**Source:** [CITED: SequenceDiagramView.test.tsx lines 10-16, 125-136]

```typescript
// Mock useMediaQuery at module level
vi.mock("@mui/material/useMediaQuery", () => ({ default: vi.fn() }));

// Helper to set reduced-motion preference
async function setReducedMotion(value: boolean) {
  const mod = await import("@mui/material/useMediaQuery");
  (mod.default as ReturnType<typeof vi.fn>).mockReturnValue(value);
}

// Test suppression of animation when prefers-reduced-motion is active
it("suppresses draw-in animation inline style under prefers-reduced-motion (D-83)", async () => {
  await setReducedMotion(true);
  const { container } = renderView({ events: sample });
  const arrows = container.querySelectorAll('g[role="button"]');
  expect(arrows.length).toBeGreaterThan(0);
  arrows.forEach((g) => {
    const style = (g as SVGGElement).getAttribute("style") ?? "";
    expect(style).not.toContain("animation");
  });
});
```

## Architecture Patterns

### Multi-Phase Verification Strategy (Phase 7 Model)

Phase 7 established a three-tier verification pattern that Phase 15 formalizes:

1. **Plan-level SUMMARY.md** — Each plan publishes a frontmatter + narrative SUMMARY capturing:
   - Requirements addressed (frontmatter `requirements:` field)
   - Files affected (frontmatter `affects:` field)
   - Verification evidence (section with truth tables)
   - Deviations from plan (section with root causes)
   - Commits and test results (task table + metrics)

2. **Phase-level VERIFICATION.md** — Aggregate document (Phase 15 task 1) that:
   - Pulls frontmatter `requirements:` from all plan SUMMARYs
   - Verifies RACE-01..07 coverage across 11 plans
   - Confirms test count (345 total) and green status
   - Cross-references commits to git log

3. **Project-level REQUIREMENTS.md** — Traceability table that:
   - Maps each requirement to the phase implementing it
   - Updates Status column when phase ships
   - Remains single source of truth for requirement status

**Pattern Recognition:** This three-level structure (plan → phase → project) enables decoupled auditing: reviewers can verify Phase 7 correctness by reading `07-VERIFICATION.md` without re-reading all 11 SUMMARYs. Future phases can follow the same pattern.

## Environment Availability

**Skip:** Phase 15 is code/config-only changes with no external runtime dependencies. No backend services, databases, or CLI tools required for planning or execution.

## Validation Architecture

**Test Framework:** Existing vitest + pytest suite

### Phase 15 Validation Coverage

| Requirement | Test Type | Validation Command | Status |
|-------------|-----------|-------------------|--------|
| 15-01: Phase 7 VERIFICATION.md exists + aggregates evidence | manual inspection | `cat .planning/phases/07-race-backend-lanes-harness-recovery/07-VERIFICATION.md` | Wave 0 |
| 15-02: TraceWorkspacePage gate uses event-presence check | integration test | `cd frontend && npm test -- DiscoveryPhasePanel` (existing suite) | Existing ✅ |
| 15-03: REQUIREMENTS.md checkboxes consistent | manual inspection | `grep -A1 "OG-0[1-4]\|VIZ-0[1-2]" .planning/REQUIREMENTS.md` | Wave 0 |
| 15-04: Phase 12 cleanup items resolved | code inspection | `grep -n "pinnedEventId.*ProtocolTier" frontend/src/components/traces/TraceExplorer.tsx` | Existing ✅ |

**Sampling Rate:**
- **Per task commit:** Manual inspection of generated files
- **Per wave merge:** Run full Phase 15 validation checklist; verify REQUIREMENTS.md traceability table row count and Status values

**Wave 0 Gaps:** None — Phase 15 tasks are all documentation and refactoring; no new test infrastructure needed.

## Security Domain

**Scope:** Phase 15 involves documentation updates and UI logic fixes with no security-relevant changes. No authentication, cryptography, or data validation logic is modified.

**Not applicable:** No ASVS categories triggered by Phase 15 scope.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | All 11 Phase 7 SUMMARY.md files exist and contain RACE-01..07 evidence | Phase 7 Verification Artifacts | Low — file existence verified directly; regeneration cost is one commit |
| A2 | CompareTracesPanel event-presence gate pattern is correct and should be replicated in TraceWorkspacePage | DiscoveryPhasePanel Gate Pattern | Medium — pattern change affects UI availability; requires human testing to confirm both gates work identically |
| A3 | OG-01..04 and VIZ-01..02 requirements are actually shipped and no longer pending | REQUIREMENTS.md Stale Checkboxes | Low — Phase 10 and Phase 12 already shipped and merged; verification is historical fact |
| A4 | `pinnedEventId` is truly dead in ProtocolTier and safe to remove without breaking anything | Phase 12 Code Quality Issues | Medium — prop removal could affect future features if a pending change assumes it's there; recommend grep search of all branches before removal |

## Open Questions

1. **Phase 7 VERIFICATION.md structure:** Should it be a single document or split across sections per requirement (RACE-01, RACE-02, etc.)? Recommend single document with sections.

2. **TraceWorkspacePage event-presence gate:** Currently gate is nested inside a JSX render callback. Should refactor to extract into a useMemo or custom hook for clarity? Recommend extract to variable for consistency with CompareTracesPanel.

3. **REQUIREMENTS.md integration gaps (lines 170-176):** Why are RACE-01..07 listed twice — once as "Complete" (lines 143-149) and again as "Pending" in integration rows (lines 170-176)? Audit should clarify distinction between RACE implementation (Phase 7 complete) and RACE HTTP integration (Phase 14 complete).

## Sources

### Primary (HIGH confidence)

- **Phase 7 SUMMARY files:** `/Users/shivanshchoudhary/Downloads/Projects/A2AvsMCP/.planning/phases/07-race-backend-lanes-harness-recovery/07-0{1..11}-SUMMARY.md` — all files exist and contain frontmatter + verification evidence [VERIFIED: direct file read]

- **ROADMAP.md Phase details:** Lines 59-69 (Phase 7 overview), lines 194-209 (Phase 15 description) [CITED: ROADMAP.md]

- **REQUIREMENTS.md traceability:** Lines 138-176 (requirement-to-phase mapping), lines 60-77 (requirement checkboxes) [CITED: REQUIREMENTS.md]

- **CompareTracesPanel code:** `frontend/src/features/compare/CompareTracesPanel.tsx` lines 65-73 [VERIFIED: direct code read]

- **TraceWorkspacePage code:** `frontend/src/features/traces/TraceWorkspacePage.tsx` lines 392-413 [VERIFIED: direct code read]

- **TraceExplorer.tsx:** Lines 31-41 (imports), 322-380 (ProtocolTier function) [VERIFIED: direct code read]

- **SequenceDiagramView.test.tsx:** Lines 10-16 (mock setup), 125-151 (D-83 test) [VERIFIED: direct code read]

### Secondary (MEDIUM confidence)

- **DESIGN.md Phase 12 decisions:** Lines 84-101 (secondary.main semantic), role-first contract (lines 104-132) [CITED: DESIGN.md]

- **Phase 14 completion status:** ROADMAP.md line 33 "Phase 14 ... completed 2026-05-04" [CITED: ROADMAP.md]

## Metadata

**Confidence Breakdown:**
- Phase 7 verification artifacts: **HIGH** — all SUMMARY files directly read and confirmed to exist
- DiscoveryPhasePanel gate pattern: **HIGH** — both implementations directly read; pattern clearly different
- REQUIREMENTS.md stale checkboxes: **HIGH** — file directly read; Status/checkbox mismatch confirmed
- Phase 12 code quality: **HIGH** — all three files directly read; issues confirmed or cleared by direct inspection

**Research Date:** 2026-05-04
**Valid Until:** 2026-05-11 (Phase 15 may add new code paths; research remains valid for planning purposes 7 days)

**Notes for Planner:**
- Phase 15 tasks are all verification/cleanup — low technical risk, high value for maintaining traceability
- Task 15-02 (gate fix) is critical for Phase 11 human verification items in Phase 16
- Task 15-03 should be executed as part of Phase 15 commit to keep traceability table current
- Task 15-04 code quality items are optional refactoring; W-VERIF-1 appears to be misidentified (no duplicate found)
