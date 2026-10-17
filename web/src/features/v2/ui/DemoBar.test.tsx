import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { DemoBar, type DemoControls } from "./DemoBar";
import { ReportTabs } from "../V2Page";
import { DepthBars } from "./DepthBars";
import { traceGroups, TraceTimeline } from "./TraceTimeline";
import type { TraceEntry } from "./trace";

const family: DemoControls = { enabled: false, busy: false, result: "", done: [], onSimulate: vi.fn().mockResolvedValue(undefined) };
const action = vi.fn().mockResolvedValue(undefined);

describe("demo bar enablement", () => {
  it("disables all five family events until the family has a zone; the clock folds behind one chip", () => {
    const html = renderToStaticMarkup(<DemoBar onAction={action} family={family} />);
    expect(html.match(/disabled=""/g)).toHaveLength(5);
    expect(html).toContain("Clock");
    expect(html).not.toContain("Reset");
    expect(html).toContain("Share a location in the phone first");
    expect(html).toContain("Next");
  });
  it("enables controls after location, shows finished events and suggests the next one", () => {
    const html = renderToStaticMarkup(<DemoBar at="06:30" onAction={action} family={{ ...family, enabled: true, done: ["rain"], result: "Rain sent" }} />);
    expect(html).not.toContain("disabled=");
    expect(html).toContain('class="chip dark done"');
    expect(html).toContain('class="chip dark next"');
    expect(html).toContain("Rain sent");
    expect(html).toContain("06:30");
  });
  it("locks family events during a request", () => {
    const html = renderToStaticMarkup(<DemoBar onAction={action} family={{ ...family, enabled: true, busy: true }} />);
    expect(html.match(/disabled=""/g)).toHaveLength(5);
    expect(action).not.toHaveBeenCalled();
  });
  it("keeps the replay clock available on pages without a family session", () => {
    const html = renderToStaticMarkup(<DemoBar onAction={action} />);
    expect(html).not.toContain("disabled=");
    expect(html).toContain("Reset");
    expect(html).toContain("Flood the system");
    expect(html).not.toContain("Family events");
  });
});

describe("report evidence", () => {
  it("folds older turns without dropping any decisions", () => {
    const lines: TraceEntry[] = [
      { id: "a", turn: 1, who: "rules", at: "06:00", atH: 0, what: "Located" },
      { id: "b", turn: 1, who: "physics", at: "06:00", atH: 0, what: "Depth" },
      { id: "c", turn: 2, who: "gemini", at: "06:01", atH: 1, what: "Read report" },
    ];
    expect(traceGroups(lines).map(([, group]) => group.length)).toEqual([2, 1]);
    const html = renderToStaticMarkup(<MemoryRouter><TraceTimeline lines={lines} activeTurn={1} onActiveTurn={() => undefined} /></MemoryRouter>);
    expect(html.match(/<details/g)).toHaveLength(1);
    expect(html).toContain('data-turn="1"');
    expect(html).toContain("is-linked");
    for (const line of lines) expect(html).toContain(line.what);
  });
  it("shows actual depth and uncertainty values, leaving missing depth unknown", () => {
    const html = renderToStaticMarkup(<DepthBars model={1.6} corrected={[0.8, 0.5, 1.2]} at="06:01" />);
    expect(html).toContain("1.6 m");
    expect(html).toContain("0.8 m");
    expect(html).toContain("0.5–1.2 m");
    expect(html).not.toContain("0.9–1.3");
    const unknown = renderToStaticMarkup(<DepthBars model={null} corrected={null} />);
    expect(unknown).toContain("Depth unknown");
    expect(unknown).not.toContain("0.0 m");
  });
});


describe("phone navigation", () => {
  it("exposes chat, evidence and map views with exactly one selected view", () => {
    const html = renderToStaticMarkup(<ReportTabs tab="map" onChange={() => undefined} />);
    expect(html).toContain("แชท");
    expect(html).toContain("Decisions");
    expect(html).toContain("แผนที่");
    expect(html.match(/aria-pressed="true"/g)).toHaveLength(1);
    expect(html).toContain('aria-pressed="true">แผนที่');
  });
  it("provides a collapsed mobile demo handle while retaining all controls", () => {
    const html = renderToStaticMarkup(<DemoBar onAction={action} />);
    expect(html).toContain('class="rp-demo-handle" aria-expanded="false"');
    expect(html).toContain("Reset");
    expect(html).toContain("Rain alert");
  });
});
