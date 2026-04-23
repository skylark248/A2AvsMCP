import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});

Object.defineProperty(navigator, "clipboard", {
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
  configurable: true,
});

if (!window.URL.createObjectURL) {
  Object.defineProperty(window.URL, "createObjectURL", {
    value: vi.fn(() => "blob:mock"),
    configurable: true,
  });
}

if (!window.URL.revokeObjectURL) {
  Object.defineProperty(window.URL, "revokeObjectURL", {
    value: vi.fn(),
    configurable: true,
  });
}
