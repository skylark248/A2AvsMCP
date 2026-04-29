import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

interface FirstMentionContextValue {
  hasSeen: (term: string) => boolean;
  markSeen: (term: string) => void;
}

const FirstMentionContext = createContext<FirstMentionContextValue | null>(null);

export function FirstMentionProvider({ children }: { children: ReactNode }) {
  // D-51: Set reset on mount. No sessionStorage / localStorage.
  const [seen, setSeen] = useState<Set<string>>(() => new Set());

  const hasSeen = useCallback((term: string) => seen.has(term), [seen]);
  const markSeen = useCallback((term: string) => {
    setSeen((prev) => {
      if (prev.has(term)) return prev;
      const next = new Set(prev);
      next.add(term);
      return next;
    });
  }, []);

  const value = useMemo(() => ({ hasSeen, markSeen }), [hasSeen, markSeen]);
  return <FirstMentionContext.Provider value={value}>{children}</FirstMentionContext.Provider>;
}

// Returns null outside provider (NOT throw) — GlossaryTerm is also used on Run/Compare pages.
// Backward-compat note per 08-PATTERNS.md line 608.
export function useFirstMention(): FirstMentionContextValue | null {
  return useContext(FirstMentionContext);
}
