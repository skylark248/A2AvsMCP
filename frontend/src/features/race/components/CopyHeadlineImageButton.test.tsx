import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CopyHeadlineImageButton } from "./CopyHeadlineImageButton";

// Hoisted mock for html2canvas — vi.mock is hoisted above imports.
const html2canvasMock = vi.fn();
vi.mock("html2canvas", () => ({ default: html2canvasMock }));

function makeFakeCanvas(blob: Blob | null): HTMLCanvasElement {
  return {
    toBlob: (cb: (b: Blob | null) => void) => cb(blob),
  } as unknown as HTMLCanvasElement;
}

describe("CopyHeadlineImageButton", () => {
  const runId = "test-run";
  let originalClipboard: typeof navigator.clipboard | undefined;
  let originalClipboardItem: typeof window.ClipboardItem | undefined;

  beforeEach(() => {
    html2canvasMock.mockReset();
    const anchor = document.createElement("div");
    anchor.setAttribute("data-og-anchor", "");
    document.body.appendChild(anchor);
    originalClipboard = navigator.clipboard;
    originalClipboardItem = window.ClipboardItem;
  });

  afterEach(() => {
    document.body.innerHTML = "";
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: originalClipboard,
    });
    // @ts-expect-error — restore original ClipboardItem (may be undefined)
    window.ClipboardItem = originalClipboardItem;
  });

  it("writes to clipboard via ClipboardItem on success", async () => {
    const blob = new Blob(["x"], { type: "image/png" });
    html2canvasMock.mockResolvedValue(makeFakeCanvas(blob));
    // @ts-expect-error — assign fake constructor
    window.ClipboardItem = function (_items: Record<string, Blob>) {
      return {} as ClipboardItem;
    };
    const writeMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { write: writeMock },
    });

    render(<CopyHeadlineImageButton runId={runId} />);
    const btn = screen.getByTestId("copy-headline-image-button");
    fireEvent.click(btn);

    await waitFor(() =>
      expect(screen.getByText("Copied to clipboard")).toBeInTheDocument(),
    );
    expect(writeMock).toHaveBeenCalledTimes(1);
  });

  it("falls back to download when ClipboardItem is undefined", async () => {
    const blob = new Blob(["x"], { type: "image/png" });
    html2canvasMock.mockResolvedValue(makeFakeCanvas(blob));
    // @ts-expect-error — explicitly remove ClipboardItem
    window.ClipboardItem = undefined;
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { write: vi.fn() },
    });
    const clickSpy = vi.fn();
    const origCreate = document.createElement.bind(document);
    const createSpy = vi
      .spyOn(document, "createElement")
      .mockImplementation((tag: string) => {
        const el = origCreate(tag);
        if (tag === "a") {
          (el as HTMLAnchorElement).click = clickSpy;
        }
        return el;
      });

    render(<CopyHeadlineImageButton runId={runId} />);
    fireEvent.click(screen.getByTestId("copy-headline-image-button"));

    await waitFor(() =>
      expect(screen.getByText("Downloaded")).toBeInTheDocument(),
    );
    expect(clickSpy).toHaveBeenCalledTimes(1);
    createSpy.mockRestore();
  });

  it("shows error when html2canvas rejects", async () => {
    html2canvasMock.mockRejectedValue(new Error("boom"));
    render(<CopyHeadlineImageButton runId={runId} />);
    fireEvent.click(screen.getByTestId("copy-headline-image-button"));
    await waitFor(() =>
      expect(screen.getByText("Capture failed — retry")).toBeInTheDocument(),
    );
  });

  it("shows error when [data-og-anchor] is missing", async () => {
    document.body.innerHTML = ""; // remove anchor seeded in beforeEach
    render(<CopyHeadlineImageButton runId={runId} />);
    fireEvent.click(screen.getByTestId("copy-headline-image-button"));
    await waitFor(() =>
      expect(screen.getByText("Capture failed — retry")).toBeInTheDocument(),
    );
    expect(html2canvasMock).not.toHaveBeenCalled();
  });
});
