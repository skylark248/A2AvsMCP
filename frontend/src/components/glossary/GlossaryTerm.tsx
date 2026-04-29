import Popover from "@mui/material/Popover";
import Button from "@mui/material/Button";
import Tooltip from "@mui/material/Tooltip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useState, type ReactNode } from "react";
import { glossaryTerms } from "../../lib/glossary/glossaryTerms";
import { useFirstMention } from "../../features/race/context/FirstMentionProvider";

interface GlossaryTermProps {
  term: string;
  children: ReactNode;
}

export function GlossaryTerm({ term, children }: GlossaryTermProps) {
  const definition = glossaryTerms[term];
  // safe: returns null outside FirstMentionProvider (Run/Compare pages still use GlossaryTerm)
  const firstMention = useFirstMention();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  if (!definition) return <>{children}</>;

  const isFirstMention = firstMention !== null && !firstMention.hasSeen(term);

  if (isFirstMention) {
    return (
      <>
        <span
          role="button"
          tabIndex={0}
          onClick={(e) => setAnchorEl(e.currentTarget as HTMLElement)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              setAnchorEl(e.currentTarget as HTMLElement);
            }
          }}
          style={{ borderBottom: "1px dashed currentColor", cursor: "help" }}
          data-testid={`glossary-term-first-${term}`}
        >
          {children}
        </span>
        <Popover
          open={Boolean(anchorEl)}
          anchorEl={anchorEl}
          onClose={() => setAnchorEl(null)}
          anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
          transformOrigin={{ vertical: "top", horizontal: "left" }}
        >
          <Stack spacing={1.5} sx={{ p: 2, maxWidth: 360 }}>
            <Typography variant="h6">{term}</Typography>
            <Typography variant="body2">{definition}</Typography>
            <Button
              size="small"
              variant="contained"
              onClick={() => {
                firstMention!.markSeen(term);
                setAnchorEl(null);
              }}
            >
              Got it
            </Button>
          </Stack>
        </Popover>
      </>
    );
  }

  // Subsequent mentions OR outside FirstMentionProvider: existing Tooltip branch (preserve).
  return (
    <Tooltip title={definition} arrow>
      <span
        style={{
          borderBottom: "1px dashed currentColor",
          cursor: "help",
          textDecoration: "none",
        }}
        data-testid={`glossary-term-tooltip-${term}`}
      >
        {children}
      </span>
    </Tooltip>
  );
}
