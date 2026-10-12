# ReachPoint web app

Owner of the foundation (shell, tokens, shared components, data hooks): user. This is connection **C10** in the [integration map](../docs/collaboration/integration-map.md). Each person builds their own screens on it.

```bash
cd web && npm install
npm run dev        # http://localhost:5173
npm run check      # type-check, token check, tests
```

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
| `src/data/teamStore.ts` | Team view + actions in fixture mode, applying the C6 claim rules; becomes API calls + a listener |

## Rules for screens

- Use tokens and shared components only. `npm run check:tokens` fails on raw colours outside `tokens.css`.
- Red means one thing: RED priority. Errors are ink, delays and holds amber.
- Unknown is `null` with a reason and shows as "Unknown", never 0. Zones with no reports show "No reports yet · not checked", never "safe".
- Estimates are always ranges, always labelled "estimate", and never added to reviewed counts.
- Shared views show landmark-level locations only (D25).

## Screen states (dev switches)

Add to any URL: `?variant=empty|stale|layer-missing` (fixture variant), `?offline=1`, `?fail=view|tiles`, `?claim=already-taken|not-enough-capacity|need-changed|allocation-closed|version-conflict` (first claim returns that result). The list is on `/dev/ui`.
