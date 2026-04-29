import { Box, Typography } from "@mui/material";

interface CharacteristicFailureBannerProps {
  /** Static header text (e.g. "Characteristic failure:"). Plan 06 passes from headline template. */
  header: string;
  /** Dynamic italic clause (e.g. "gave up after 3 turns"). Rendered as React text — no innerHTML (T-08-08). */
  clause: string;
}

/**
 * Full-bleed banner: 4px primary left rule + h2 heading + italic dynamic clause.
 *
 * Visual contract (UIRACE-03):
 *   - borderLeft: 4px solid primary.main
 *   - borderRadius: 0
 *   - p: 3 (24px — lg spacing per scale)
 *
 * ARIA: role="banner" (UI-SPEC ARIA Landmarks line 240)
 *   Note: UI-SPEC accepts dual role="banner" (AppShell header + this section banner).
 *   Threat T-08-11 reviewed and accepted.
 *
 * Typography (UI-SPEC Display — 25.6px / 1.6rem / 700):
 *   - h2 with fontSize="1.6rem", fontWeight=700
 *   - dynamic clause span with fontStyle="italic" (UIRACE-03)
 *
 * T-08-08 mitigation: clause + header rendered exclusively as React text children (auto-escaped).
 * No XSS surface — acceptance criteria grep enforces zero innerHTML-bypass usage.
 */
export function CharacteristicFailureBanner({ header, clause }: CharacteristicFailureBannerProps) {
  return (
    <Box
      role="banner"                                    // UI-SPEC ARIA Landmarks line 240
      data-testid="characteristic-failure-banner"
      sx={{
        borderLeft: "4px solid",                       // UIRACE-03 banner 4px primary rule
        borderColor: "primary.main",
        bgcolor: "background.paper",
        p: 3,                                          // 24px (lg per spacing scale)
        borderRadius: 0,                               // UIRACE-03 banner=0
      }}
    >
      <Typography
        variant="h2"
        component="h1"
        sx={{ fontSize: "1.6rem", fontWeight: 700, lineHeight: 1.2 }}  // Display 25.6px/700 per UI-SPEC
      >
        {header}{" "}
        <Typography
          component="span"
          sx={{ fontStyle: "italic", fontSize: "1.6rem", fontWeight: 700 }}  // UIRACE-03 italic dynamic clause
        >
          {clause}
        </Typography>
      </Typography>
    </Box>
  );
}
