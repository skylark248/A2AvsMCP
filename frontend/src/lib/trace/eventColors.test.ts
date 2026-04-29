import { describe, it, expect } from "vitest";
import { protocolColor, toneColor, failureTagColor } from "./eventColors";

describe("eventColors — regression guard: existing exports", () => {
  it("protocolColor has mcp, a2a, hybrid, baseline keys", () => {
    expect(protocolColor.mcp).toBe("#1976d2");
    expect(protocolColor.a2a).toBe("#7b1fa2");
    expect(protocolColor.hybrid).toBe("#2e7d32");
    expect(protocolColor.baseline).toBe("#757575");
  });

  it("toneColor has error, warning, success, info keys", () => {
    expect(toneColor.error).toBe("#c62828");
    expect(toneColor.warning).toBe("#ed6c02");
    expect(toneColor.success).toBe("#2e7d32");
    expect(toneColor.info).toBe("#757575");
  });
});

describe("failureTagColor map — UIRACE-04 / D-46", () => {
  it("has exactly 5 keys", () => {
    expect(Object.keys(failureTagColor)).toHaveLength(5);
    expect(Object.keys(failureTagColor)).toEqual(
      expect.arrayContaining([
        "recovered",
        "gave_up",
        "kept_going_without_noticing",
        "kept_going_to_failure",
        "indeterminate",
      ]),
    );
  });

  it("each entry has bg, text, Icon, label fields — no missing, no extra", () => {
    for (const [_key, value] of Object.entries(failureTagColor)) {
      const keys = Object.keys(value).sort();
      expect(keys).toEqual(["Icon", "bg", "label", "text"]);
    }
  });

  it("recovered entry has correct bg and label", () => {
    expect(failureTagColor.recovered.bg).toBe("#e8f5e9");
    expect(failureTagColor.recovered.label).toBe("Recovered");
  });

  it("gave_up entry has correct bg and label", () => {
    expect(failureTagColor.gave_up.bg).toBe("#fce4ec");
    expect(failureTagColor.gave_up.label).toBe("Gave Up");
  });

  it("kept_going_without_noticing entry has correct bg and label", () => {
    expect(failureTagColor.kept_going_without_noticing.bg).toBe("#fff3e0");
    expect(failureTagColor.kept_going_without_noticing.label).toBe("Kept Going (Unaware)");
  });

  it("kept_going_to_failure entry has correct bg and label", () => {
    expect(failureTagColor.kept_going_to_failure.bg).toBe("#fbe9e7");
    expect(failureTagColor.kept_going_to_failure.label).toBe("Kept Going to Failure");
  });

  it("indeterminate entry has correct bg and label", () => {
    expect(failureTagColor.indeterminate.bg).toBe("#f5f5f5");
    expect(failureTagColor.indeterminate.label).toBe("Indeterminate");
  });

  it("each entry Icon is a non-null component (function or object — MUI icons are forwardRef objects)", () => {
    for (const [key, value] of Object.entries(failureTagColor)) {
      expect(value.Icon, `${key} Icon should be defined`).toBeDefined();
      expect(value.Icon, `${key} Icon should be non-null`).not.toBeNull();
      // MUI SvgIcon components are React.forwardRef objects; typeof === "object" is valid.
      expect(
        ["function", "object"].includes(typeof value.Icon),
        `${key} Icon typeof should be function or object, got ${typeof value.Icon}`,
      ).toBe(true);
    }
  });
});
