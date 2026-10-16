# ReachPoint web app

Owner of the foundation (shell, tokens, shared components, data hooks): user. This is connection **C10** in the [integration map](../docs/collaboration/integration-map.md). Each person builds their own screens on it.

```bash
cd web && npm install
npm run dev        # http://localhost:5173
npm run check      # type-check, token check, tests
```

`npm run build` defaults to API data because the built app is served by the backend. `/desk` therefore loads caller reviews without requiring `?data=api`, including after returning through the home page. Build the offline demo explicitly with `VITE_DATA=fixtures npm run build`; URL overrides (`?data=api` / `?data=fixtures`) still take precedence. Development and test defaults remain fixtures.

The caller desk lists all submitted form, chat and voice requests as area-led cards on the left. Automatic AI review proposes the address/coordinates, boat/truck candidate, emergency level and optional volunteer prep notes. Approved cards use a subtle teal tint; AI/Human provenance badges are neutral. Queue cards show labeled 💊 medication indicators from current review evidence and 🚤 boat indicators from current transport suggestions, omitting stale or unresolved recommendations. The detail pane shows results first, with **Edit details** and **Approve review**. Human approval is separate from review provenance; only original phone, help type and submitted location are required for approval; derived location, classifications and notes may remain unresolved. Approval advances caller tracking to Reviewing request, with team progress pending a separate team acceptance. Corrections clear approval until the updated results are approved. Volunteer prep notes omit repeated “Caller reports:” prefixes and shorter excerpts already covered by a fuller line. Original evidence and saved history remain intact. Caller fields, evidence, reasons and history expand on demand. The separate case-creation panel is removed from `/desk`. On narrow screens select a card and use “Back to requests” to return. Offline records remain readable, with review writes disabled. Full address geocoding requires server configuration; the UI shows unresolved values and disabled AI honestly.

| Path | What |
|---|---|
| `src/shell/` | App shell: wordmark, role routes, top nav on desktop, bottom tab bar under 768 px |
| `src/ui/tokens.css` | **The only place** colours, fonts, sizes and spacing are defined. Proposed 12 Oct; `/design-consultation` may change values, not names |
| `src/ui/components.tsx` | `PriorityBadge`, `StatusChip`, `CountBadge`, `ProposalCard`, `Banner`, `LastUpdated`, `BigButton`, `EstimateRange`, `Skeleton`. See them all at `/dev/ui` |
| `src/ui/states.ts` | One colour + icon + Thai/English label per state (the Thai labels need a native-speaker check) |
| `src/data/useView.ts` | `useView(path)`: one derived view, with loading / ready (live or offline) / missing / error |
| `src/data/source.ts` | Today: the shared fixtures in `contract/fixtures/`. Later: Firestore listeners, same return shape |
| `src/data/api.ts` | Typed API client for the friend's FastAPI (`VITE_API_URL`); every write carries a `submissionId` |
| `src/data/contract.ts` | Draft view types, hand-written from the fixtures until the generated types land (T2) |
| `src/features/briefing/` | Area and zone briefing: list first, offline schematic map, zone sheet on phones |
| `src/features/team/` | Team screens: waiting list (shared order), take families, my jobs (exact point after taking, window, progress, finish, hand back), team status |
| `src/features/split/` | Coordinator split panel (`/desk/split`): situation line, team rows, still unmet, why (solver facts), Ask these N teams, What-if, stale diff |
| `src/data/teamStore.ts` | Team view + actions in fixture mode, applying the C6 claim rules; becomes API calls + a listener |

## Rules for screens

- Use tokens and shared components only. `npm run check:tokens` fails on raw colours outside `tokens.css`.
- Red means one thing: RED priority. Errors are ink, delays and holds amber.
- Unknown is `null` with a reason and shows as "Unknown", never 0. Zones with no reports show "No reports yet · not checked", never "safe".
- Estimates are always ranges, always labelled "estimate", and never added to reviewed counts.
- Shared views show landmark-level locations only (D25).

## Screen states (dev switches)

Add to any URL: `?variant=empty|stale|layer-missing` (fixture variant), `?offline=1`, `?fail=view|tiles`, `?claim=already-taken|not-enough-capacity|need-changed|allocation-closed|version-conflict` (first claim returns that result), `?ask=stale` (split panel ask gets VERSION_CONFLICT), `?variant=all-unmet` on `/desk/split`. The list is on `/dev/ui`.
