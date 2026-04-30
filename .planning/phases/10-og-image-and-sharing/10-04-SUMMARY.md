---
phase: 10-og-image-and-sharing
plan: 04
subsystem: ui
tags: [og-image, copy-headline, html2canvas, clipboard, download-fallback, action-slot]

requires:
  - phase: 10-og-image-and-sharing
    provides: data-og-anchor sentinel set by RacePage `?og=1` mode (10-03)
  - phase: 08-race-page-ui-visual-contract
    provides: CharacteristicFailureBanner (additive actionSlot extension)
provides:
  - CopyHeadlineImageButton component (lazy html2canvas + ClipboardItem primary + download fallback)
  - CharacteristicFailureBanner.actionSlot optional prop for right-aligned action mounts
  - html2canvas runtime dep (1.4.1)
affects: []

tech-stack:
  added: [html2canvas@1.4.1]
  patterns:
    - "Dynamic import for heavy optional libs: `const { default: html2canvas } = await import('html2canvas')` keeps the initial page bundle free of the ~45KB library until the user actually clicks (D-64)."
    - "Browser-API feature-detect with try/catch + fall-through: ClipboardItem may exist but `clipboard.write` may still reject (Safari/Firefox image/png restrictions). Treat reject as fall-through, not error (D-65)."
    - "actionSlot prop pattern: presentational components accept an optional ReactNode slot for adding actions without coupling them to the consuming feature. Defaults to undefined → zero-impact on existing snapshot/render tests."

key-files:
  created:
    - frontend/src/features/race/components/CopyHeadlineImageButton.tsx
    - frontend/src/features/race/components/CopyHeadlineImageButton.test.tsx
  modified:
    - frontend/package.json (+ html2canvas dep)
    - frontend/package-lock.json (+ html2canvas tree)
    - frontend/src/features/race/components/CharacteristicFailureBanner.tsx (+ actionSlot prop, Stack layout)
    - frontend/src/features/race/RacePage.tsx (+ CopyHeadlineImageButton import + mount via actionSlot)

key-decisions:
  - "Button mount gated on `!isOg && run_id` so OG screenshots never embed the button. The OG render path (which is the path needing this button as its 503 fallback) does NOT need the button — by definition the user is on the live UI when they click it."
  - "ClipboardItem feature-detect uses `typeof window.ClipboardItem !== 'undefined'`. Some browsers expose ClipboardItem but reject image/png writes — caught by try/catch and falls through to download (D-65)."
  - "html2canvas resolved as 1.4.1 (verified in node_modules/html2canvas/package.json). 1.4.1 ships its own .d.ts so no @types/html2canvas needed."

patterns-established:
  - "Async-action button feedback FSM: `null → busy → terminal('copied' | 'downloaded' | 'error') → null on next click`. Button label drives ARIA-live announcements."
  - "Synthetic `<a download>` blob downloader as the universal fallback when ClipboardItem path fails — avoids Permissions-Policy gating issues and works in all evergreen browsers."

requirements-completed: [OG-03]

duration: 11min
completed: 2026-04-30
---

# Phase 10 — Plan 04 Summary

**Client-side OG-03 fallback: CopyHeadlineImageButton lazy-loads html2canvas, snapshots `[data-og-anchor]` to a PNG blob, writes via ClipboardItem (primary) or downloads as `race-<runId>.png` (fallback). Mounted beside CharacteristicFailureBanner via a new actionSlot prop, gated on `!isOg && run_id`.**

## Performance

- **Duration:** ~11 min
- **Started:** 2026-04-30T21:52:00Z
- **Completed:** 2026-04-30T21:55:00Z
- **Tasks:** 3/3
- **Files modified:** 4 (2 created, 2 modified, plus package.json/lock)

## Accomplishments

- `html2canvas@1.4.1` declared as runtime dep + installed.
- `CopyHeadlineImageButton.tsx` shipped with: lazy `import('html2canvas')`, scale=2 + useCORS=true canvas render, ClipboardItem primary write, synthetic `<a download>` fallback, 4-state feedback (idle / busy / copied / downloaded / error).
- 4 vitest cases lock the clipboard / download / html2canvas-error / missing-anchor branches.
- `CharacteristicFailureBanner` gains optional `actionSlot?: ReactNode` prop (additive — Phase 8 tests untouched).
- RacePage mounts the button via `actionSlot={!isOg && run_id ? <CopyHeadlineImageButton runId={run_id} /> : undefined}` — clean OG screenshots guaranteed.
- Full frontend suite: 286 passed (Phase 9 baseline 280 + 6 new across 10-03/10-04).

## Task Commits

1. **Task 1: html2canvas dep + CopyHeadlineImageButton.tsx** — `9092da8` (feat)
2. **Task 2: 4 vitest cases for the button** — `2f52a87` (test)
3. **Task 3: actionSlot prop + RacePage mount** — `9c90d5a` (feat)

## Files Created/Modified

- `frontend/src/features/race/components/CopyHeadlineImageButton.tsx` (created, 100 LOC) — MUI Button, lazy html2canvas, clipboard + download paths, feedback states.
- `frontend/src/features/race/components/CopyHeadlineImageButton.test.tsx` (created, 111 LOC, 4 tests) — vi.mock("html2canvas") + ClipboardItem stubbing patterns.
- `frontend/package.json` (modified) — `"html2canvas": "^1.4.1"` added to dependencies.
- `frontend/package-lock.json` (modified) — html2canvas tree resolved.
- `frontend/src/features/race/components/CharacteristicFailureBanner.tsx` (modified, +18/-2) — actionSlot prop; Stack direction=row layout; existing visual contract preserved.
- `frontend/src/features/race/RacePage.tsx` (modified, +5/-1) — CopyHeadlineImageButton import + actionSlot wiring on banner.

## Decisions Made

- **Button mount gated on `!isOg && run_id`.** OG screenshots NEVER embed the button (clean card invariant). Live mode without run_id (no replay) hides the button (component would no-op anyway, but short-circuiting avoids spurious DOM nodes).
- **try/catch around ClipboardItem write with fall-through to download.** Some browsers expose ClipboardItem but reject image/png writes (Safari Permissions-Policy variants). Treat any rejection as a non-error fall-through, not user-facing failure.
- **Single-mount via actionSlot, not multiple consumers.** Keeps RacePage as the only place that knows when to show the button. CharacteristicFailureBanner stays decoupled from feature concerns.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Required] CharacteristicFailureBanner Stack import + restructure**
- **Found during:** Task 3 (banner edit).
- **Issue:** Plan said "wrap header + actionSlot so they render side-by-side", suggesting `<Stack direction="row">`. Existing banner had no Stack import; required adding `Stack` to the MUI imports.
- **Fix:** Added `Stack` to `@mui/material` import; wrapped header `<Typography>` and conditional `<Box>{actionSlot}</Box>` inside `<Stack direction="row" alignItems="center" justifyContent="space-between" spacing={2}>`.
- **Files modified:** frontend/src/features/race/components/CharacteristicFailureBanner.tsx.
- **Verification:** TypeScript compiles; full frontend suite green (banner snapshot/render tests still pass with `actionSlot=undefined`).
- **Committed in:** 9c90d5a.

---

**Total deviations:** 1 auto-fixed (required for actionSlot to render side-by-side).
**Impact on plan:** No scope creep. Banner visual contract unchanged when actionSlot is omitted.

## Issues Encountered

None — Wave 3 ran cleanly inline after Wave 2 quota recovery established the pattern.

## User Setup Required

None — pure frontend addition.

## Next Phase Readiness

- 10-05 (mobile `<img>` consumer for `/race/{run_id}/og.png`) is independent: it touches only the mobile placeholder branch (RacePage line 79-85) which 10-03 left untouched. Wave 4 can run unblocked.

---
*Phase: 10-og-image-and-sharing*
*Completed: 2026-04-30*
