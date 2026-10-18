import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { IncomingCall, Captions, CallSummary, respondToCall } from "./IncomingCall";
import { UiLangProvider } from "./lang";
import { v2 } from "../api";

describe("outbound safety call", () => {
  it.each(["safetyCheck", "lostContact"] as const)("renders %s with readable actions and zone/time", kind => {
    const html = renderToStaticMarkup(<UiLangProvider initialLang="en"><IncomingCall sid="S1" incoming={{ kind, at: "07:00", reason: "Check" }} zone="D12" busy={false} onAnswer={vi.fn()} onDecline={vi.fn()} onError={vi.fn()} /></UiLangProvider>);
    for (const text of ["ReachPoint is calling", "D12", "07:00", "Answer", "Decline"]) expect(html).toContain(text);
    expect(html).toContain(kind === "safetyCheck" ? "Safety check" : "haven&#x27;t heard");
  });
  it.each(["answer", "decline"] as const)("sends %s to the API before continuing", async action => {
    const request = vi.spyOn(v2, "incoming").mockResolvedValue({ incoming: null, kind: "safetyCheck" });
    const done = vi.fn();
    await respondToCall("S1", action, done);
    expect(request).toHaveBeenCalledWith("S1", action);
    expect(done).toHaveBeenCalledOnce();
    request.mockRestore();
  });
  it("keeps the ringing view on API failure", async () => {
    const request = vi.spyOn(v2, "incoming").mockRejectedValue(new Error("offline"));
    const done = vi.fn();
    await expect(respondToCall("S1", "answer", done)).rejects.toThrow("offline");
    expect(done).not.toHaveBeenCalled();
    request.mockRestore();
  });
  it("renders heard and said captions and retains them in the summary", () => {
    const lines = [{ speaker: "said" as const, text: "Is the water higher?" }, { speaker: "heard" as const, text: "Chest deep now" }];
    const captions = renderToStaticMarkup(<UiLangProvider initialLang="en"><Captions lines={lines} /></UiLangProvider>);
    expect(captions).toContain("ReachPoint:");
    expect(captions).toContain("You:");
    const summary = renderToStaticMarkup(<CallSummary lines={lines} seconds={72} update="water now chest-deep, 2 people" />);
    expect(summary).toContain("1:12");
    expect(summary).toContain("water now chest-deep, 2 people");
    expect(summary).toContain("Is the water higher?");
    expect(summary).toContain("Chest deep now");
  });
});
