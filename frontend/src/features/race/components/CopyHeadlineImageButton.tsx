import { useState } from "react";
import { Button } from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";

interface CopyHeadlineImageButtonProps {
  runId: string;
}

type Feedback = "copied" | "downloaded" | "error" | null;

/**
 * Phase 10 OG-03: client-side canvas snapshot of the [data-og-anchor] region.
 * - D-64: html2canvas lazy-loaded via dynamic import on first click.
 * - D-65: ClipboardItem write primary; download fallback when clipboard rejects.
 * - Mounts in live UI only (RacePage gates on !isOg + banner-visible page state).
 */
export function CopyHeadlineImageButton({ runId }: CopyHeadlineImageButtonProps) {
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<Feedback>(null);

  async function onClick(): Promise<void> {
    if (busy || !runId) return;
    setBusy(true);
    setFeedback(null);
    try {
      const anchor = document.querySelector<HTMLElement>("[data-og-anchor]");
      if (!anchor) {
        setFeedback("error");
        return;
      }
      const { default: html2canvas } = await import("html2canvas");
      const canvas = await html2canvas(anchor, {
        backgroundColor: "#ffffff",
        scale: 2,
        useCORS: true,
        logging: false,
      });
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob(resolve, "image/png"),
      );
      if (!blob) {
        setFeedback("error");
        return;
      }
      // Primary: ClipboardItem (D-65).
      const clipboardOk =
        typeof window.ClipboardItem !== "undefined" &&
        typeof navigator.clipboard?.write === "function";
      if (clipboardOk) {
        try {
          await navigator.clipboard.write([
            new ClipboardItem({ "image/png": blob }),
          ]);
          setFeedback("copied");
          return;
        } catch {
          /* fall through to download */
        }
      }
      // Fallback: download via synthetic <a>.
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `race-${runId}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setFeedback("downloaded");
    } catch {
      setFeedback("error");
    } finally {
      setBusy(false);
    }
  }

  if (!runId) return null;

  const label =
    busy
      ? "Capturing…"
      : feedback === "copied"
        ? "Copied to clipboard"
        : feedback === "downloaded"
          ? "Downloaded"
          : feedback === "error"
            ? "Capture failed — retry"
            : "Copy headline image";

  return (
    <Button
      onClick={onClick}
      disabled={busy}
      startIcon={<ContentCopyIcon />}
      variant="outlined"
      data-testid="copy-headline-image-button"
      aria-live="polite"
    >
      {label}
    </Button>
  );
}
