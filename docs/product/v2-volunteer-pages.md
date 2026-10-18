# v2 volunteer pages

Decided with the user on 16 Oct 2026. The judge page (`/`) stays the demo. Volunteers get five more pages under
`/v`, reading the same live state: nothing to fill in except a one-line plan and one tap on a case.

| Page | Path | Main user | Answers |
|---|---|---|---|
| City overview | `/v` | coordinator, laptop | Where is help most missing right now? |
| Live feed | `/v/feed` | coordinator, laptop | What just came in, and what did the AI do with it? |
| Zone | `/v/zone/:id` | both; works on a phone | How deep, who is there, who needs what first, who is coming? |
| Case | `/v/case/:id` | both | This family's whole story, with the words it came from |
| Zone plan | `/v` zone panel | volunteer team, phone | Suggest, edit and post a visiting order using the team’s capacity and current zone records |
| Mission | `/v/mission/:zoneId` | volunteer team, phone | Follow the posted order, record outcomes and check modelled unheard streets |

## Rules

- **One tap only.** On a case a team can record *Picked up* or *Nobody there*. That closes the loop: the household's
  status changes, the victim's phone is told, and the board counts it. No measurements, no forms.
- **Privacy by plan.** Everyone sees a household's zone, its dot and its needs. The exact address and the raw message
  text show only to a team that has posted a plan covering that zone (team name kept in the browser). Elsewhere
  house numbers are masked. The scenario has no phone numbers; contact goes through ReachPoint's own messages.
- **Every claim shows its source.** Facts carry their quote and message; merges carry their reason; depth carries
  model vs reports and any doubtful label with why.
- **Priority, not assignment.** Families are sorted (urgent, lost contact, can't walk, elderly, children, deep water),
  but nobody is assigned. Teams choose by posting plans.

## Priority score (sorting only)

urgent and open 100 · lost contact 60 · can't walk 30 · water ≥ 1.2 m at the house 20 · elderly 15 · children 10 ·
safe or evacuated go last. Boat suggested where water at the house is ≥ 0.5 m (Earth's desk threshold, decision 0017).

## Zone suggestions — owner decision, 18 Oct 2026

[Decision 0011](../decisions/0011-zone-plan-suggestions.md) replaces the separate free-text copilot screen with an
optional Gemini suggestion inside the zone plan form. The server assembles the room context and checks IDs, vehicle
access, per-run seats, quotes, numbers and unheard street names. Unavailable, capped or invalid model replies fall
back to a labelled rules plan. Unknown household sizes require confirmation before allocating seats. Suggestions
remain editable; posting stores the chosen order for that team’s mission. Moving households repacks runs to preserve capacity.
Flooded building counts remain model estimates; household ranges are separately labelled estimates, not requests.
