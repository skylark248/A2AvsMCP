---
phase: 15-verification-and-cleanup
plan: 04
type: code-cleanup
status: complete
completed_date: 2026-05-04
duration_seconds: 30
---

# Phase 15 Plan 04: Remove Dead pinnedEventId Prop from ProtocolTier — Summary

## Objective

Remove dead pinnedEventId prop from ProtocolTier: The `pinnedEventId` parameter is accepted in the ProtocolTier function signature but never used in the function body. Remove both the parameter declaration and the argument at the call site.

## What Shipped

### `frontend/src/components/traces/TraceExplorer.tsx`

Removed dead `pinnedEventId` parameter from ProtocolTier:

**Call site (line 293) — Before:**
```typescript
<ProtocolTier events={filteredEvents} pinnedEventId={pinnedEventId} />
```

**Call site (line 293) — After:**
```typescript
<ProtocolTier events={filteredEvents} />
```

**Function signature (line 322) — Before:**
```typescript
function ProtocolTier({ events, pinnedEventId }: { events: TraceEvent[]; pinnedEventId?: string | null }) {
```

**Function signature (line 322) — After:**
```typescript
function ProtocolTier({ events }: { events: TraceEvent[] }) {
```

## Why This Matters

`pinnedEventId` was in the ProtocolTier function signature but never accessed or used in the function body (322-379). This dead prop:

1. Creates confusion for maintainers (looks like it's used but isn't)
2. Causes unnecessary re-renders when `pinnedEventId` changes
3. Violates React performance best practices

**Note:** `pinnedEventId` IS used elsewhere in the TraceExplorer component for scroll-to-pin behavior (lines 82, 87, 98) in the sequence diagram view, which uses a different code path. Those usages remain unchanged.

## Cleanup Verification

✓ `pinnedEventId` parameter removed from function signature  
✓ `pinnedEventId` argument removed from call site  
✓ No references to `pinnedEventId` in ProtocolTier function body  
✓ `pinnedEventId` state (line 60) in TraceExplorer component unchanged (used for sequence diagram scroll-to-pin, lines 82/87/98)  
✓ SequenceDiagram still receives `pinnedEventId` prop (line 265) — unchanged  
✓ All frontend tests pass (335/335)  
✓ No regressions introduced  

## Key Files Modified

| File | Lines Changed | Reason |
|------|---------------|--------|
| `frontend/src/components/traces/TraceExplorer.tsx` | 293, 322 | Remove dead pinnedEventId prop |

## Test Results

✓ All 335 frontend tests pass (38 test files, no regressions)

## Self-Check

✓ ProtocolTier signature cleaned (line 322)  
✓ ProtocolTier call site cleaned (line 293)  
✓ pinnedEventId state remains in TraceExplorer (used for sequence diagram)  
✓ pinnedEventId usages (lines 82/87/98) unchanged (different code path)  
✓ TypeScript compiles cleanly  
✓ All frontend tests pass (335/335)  

## Self-Check: PASSED
