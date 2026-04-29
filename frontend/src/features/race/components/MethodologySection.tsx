import { Box, Container, Typography } from "@mui/material";
import { GlossaryTerm } from "../../../components/glossary/GlossaryTerm";

/**
 * Flat aside section — methodology prose with GlossaryTerm wraps.
 *
 * Visual contract (UIRACE-03):
 *   - Flat Box component="aside" — no MUI elevation components (UIRACE-03 flat section)
 *   - bgcolor: background.default (dominant 60% per UI-SPEC Color section)
 *   - py: 6 (2xl spacing)
 *
 * ARIA: role="complementary" on <aside> (UI-SPEC ARIA Landmarks line 243).
 *
 * Content contract (UIRACE-07 first-mention):
 *   - ttff, recovery_rate, hardness_profile wrapped in <GlossaryTerm>
 *   - FirstMentionProvider (Plan 01) handles first-mention popover vs Tooltip branch
 *   - Safe outside FirstMentionProvider (GlossaryTerm.useFirstMention returns null → Tooltip)
 */
export function MethodologySection() {
  return (
    <Box
      component="aside"
      role="complementary"                            // UI-SPEC ARIA Landmarks line 243
      data-testid="race-methodology-section"
      sx={{ bgcolor: "background.default", py: 6 }}  // dominant 60% + 2xl spacing
    >
      <Container maxWidth="lg" disableGutters>
        <Typography
          variant="overline"
          sx={{ color: "secondary.main", letterSpacing: "0.16em" }}
        >
          Methodology
        </Typography>

        <Typography variant="h2" sx={{ color: "primary.main", mb: 2 }}>
          How we measure failure recovery
        </Typography>

        <Typography variant="body1" sx={{ maxWidth: 760, color: "text.secondary" }}>
          We measure each lane by{" "}
          <GlossaryTerm term="ttff">TTFF</GlossaryTerm>,{" "}
          <GlossaryTerm term="recovery_rate">recovery rate</GlossaryTerm>, and the{" "}
          <GlossaryTerm term="hardness_profile">hardness profile</GlossaryTerm>{" "}
          of each task. Faults are injected deterministically; the recovery state machine
          classifies each run as recovered, gave_up, kept_going_without_noticing,
          kept_going_to_failure, or indeterminate within a K=3 turn window.
        </Typography>
      </Container>
    </Box>
  );
}
