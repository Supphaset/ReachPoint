# v2 volunteer pages

Decided with the user on 16 Oct 2026. The judge page (`/`) stays the demo. Volunteers get five more pages under
`/v`, reading the same live state: nothing to fill in except a one-line plan and one tap on a case.

| Page | Path | Main user | Answers |
|---|---|---|---|
| City overview | `/v` | coordinator, laptop | Where is help most missing right now? |
| Live feed | `/v/feed` | coordinator, laptop | What just came in, and what did the AI do with it? |
| Zone | `/v/zone/:id` | both; works on a phone | How deep, who is there, who needs what first, who is coming? |
| Case | `/v/case/:id` | both | This family's whole story, with the words it came from |
| Plan a trip | `/v/plan` | boat team, phone | Which families in my zones, what water on the way, who else goes? |

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
