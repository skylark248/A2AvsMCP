import Tooltip from "@mui/material/Tooltip";
import type { ReactNode } from "react";
import { glossaryTerms } from "../../lib/glossary/glossaryTerms";

interface GlossaryTermProps {
  term: string;
  children: ReactNode;
}

export function GlossaryTerm({ term, children }: GlossaryTermProps) {
  const definition = glossaryTerms[term];
  if (!definition) return <>{children}</>;
  return (
    <Tooltip title={definition} arrow>
      <span
        style={{
          borderBottom: "1px dashed currentColor",
          cursor: "help",
          textDecoration: "none",
        }}
      >
        {children}
      </span>
    </Tooltip>
  );
}
