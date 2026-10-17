import { describe, expect, it } from "vitest";
import { initialSelection, selectionReducer } from "./selection";

describe("sector / zone map-list selection", () => {
  it("a zone selected from either map or list selects its containing sector", () => {
    const state = selectionReducer(initialSelection, { type: "zone", id: "D12", sector: "D" });
    expect(state).toEqual({ sector: "D", zone: "D12", hover: null });
    expect(selectionReducer(state, { type: "zone", id: "A2", sector: "A" })).toEqual({ sector: "A", zone: "A2", hover: null });
  });
  it("sector selection and the all-sectors reset clear an incompatible zone and hover", () => {
    const state = { sector: "D", zone: "D12", hover: "A" };
    expect(selectionReducer(state, { type: "sector", id: "A" })).toEqual({ sector: "A", zone: null, hover: null });
    expect(selectionReducer(state, { type: "sector", id: null })).toEqual(initialSelection);
  });
  it("hover preserves the selected zone; closing its panel preserves sector zoom", () => {
    const state = { sector: "D", zone: "D12", hover: null };
    const hover = selectionReducer(state, { type: "hover", id: "B" });
    expect(hover).toEqual({ ...state, hover: "B" });
    expect(selectionReducer(hover, { type: "hover", id: null })).toEqual(state);
    expect(selectionReducer(state, { type: "close" })).toEqual({ sector: "D", zone: null, hover: null });
  });
});
