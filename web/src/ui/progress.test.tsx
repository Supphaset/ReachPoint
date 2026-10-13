import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LangProvider } from "../i18n/lang";
import { S } from "../i18n/strings";
import type { Job } from "../data/contract";
import { statusStep, jobStep } from "./progress";
import { ProgressTracker } from "./ProgressTracker";

describe("family progress", () => {
  it.each([
    ["received", 0], ["reviewed", 1], ["waiting", 1], ["taken", 2], ["window", 2],
    ["held", 2], ["on_the_way", 3], ["on_scene", 3], ["done", 4],
    ["already_left", 2], ["not_found", 2], ["needs_more_help", 2],
    ["closed", null], ["unexpected", null],
  ])("maps %s without implying a pickup", (state, step) => {
    expect(statusStep(state as string)).toBe(step);
  });

  it("labels a hold and marks exactly one current step, with future steps grey", () => {
    const html = renderToStaticMarkup(<LangProvider lang="en"><ProgressTracker steps={S.progress.family} current={2} held label={S.progress.familyLabel} /></LangProvider>);
    expect(html).toContain("On hold");
    expect(html.match(/aria-current="step"/g)).toHaveLength(1);
    expect(html.match(/class="is-past"/g)).toHaveLength(2);
    expect(html.match(/class="is-future"/g)).toHaveLength(2);
  });

  it("localizes every step and never marks unknown as current", () => {
    const html = renderToStaticMarkup(<LangProvider lang="th"><ProgressTracker steps={S.progress.family} current={null} label={S.progress.familyLabel} /></LangProvider>);
    expect(html).toContain("รับคำขอแล้ว");
    expect(html).not.toContain("Received");
    expect(html).not.toContain("aria-current");
  });
});

const windowEstimate = { start: "2026-10-11T04:00:00Z", end: "2026-10-11T05:00:00Z", setAt: "2026-10-11T03:00:00Z" };
describe("job progress", () => {
  it.each<[Job["state"], Job["window"], number]>([
    ["taken", null, 0], ["taken", windowEstimate, 1],
    ["on_the_way", windowEstimate, 2], ["on_scene", windowEstimate, 3],
    ["closed", null, 4], ["held", null, 0], ["held", windowEstimate, 0],
  ])("maps %s with window %j to %s", (state, window, expected) => {
    expect(jobStep({ state, window })).toBe(expected);
  });
});
