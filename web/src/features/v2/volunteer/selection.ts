export interface Selection { sector: string | null; zone: string | null; hover: string | null }
export type SelectionAction =
  | { type: "sector"; id: string | null }
  | { type: "zone"; id: string; sector: string | null }
  | { type: "hover"; id: string | null }
  | { type: "close" };
export const initialSelection: Selection = { sector: null, zone: null, hover: null };
export function selectionReducer(state: Selection, action: SelectionAction): Selection {
  switch (action.type) {
    case "sector": return { sector: action.id, zone: null, hover: null };
    case "zone": return { sector: action.sector, zone: action.id, hover: null };
    case "hover": return { ...state, hover: action.id };
    case "close": return { ...state, zone: null };
  }
}
