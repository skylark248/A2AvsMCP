import Chip from "@mui/material/Chip";
import { failureTagColor } from "../../../lib/trace/eventColors";
import type { FailureTag } from "../../../lib/types/race";

interface FailureStateBadgeProps {
  tag: FailureTag;
}

// UIRACE-04: color is never sole channel — always paired with Icon + label.
// UIRACE-03: badge border-radius = 4px (compact pill).
// UI-SPEC line 49: minimum 44px height for WCAG 2.5.5 touch target.
export function FailureStateBadge({ tag }: FailureStateBadgeProps) {
  const cfg = failureTagColor[tag];
  const Icon = cfg.Icon;
  return (
    <Chip
      icon={<Icon />}
      label={cfg.label}
      data-testid="failure-state-badge"
      data-tag={tag}
      sx={{
        bgcolor: cfg.bg,
        color: cfg.text,
        borderRadius: "4px", // UIRACE-03 badge=4
        height: 44, // UI-SPEC line 49 — WCAG 2.5.5 touch target
        fontWeight: 600,
        "& .MuiChip-icon": { color: cfg.text },
      }}
    />
  );
}
