# v2 evaluation: Hat Yai scenario, 21–28 Nov 2025

Run by `python api/scripts/eval_v2.py`. The scenario uses real water data (gauge X.44, rain, satellite, terrain,
building outlines) and synthetic people and messages, so these numbers describe behaviour on realistic messages,
not field accuracy. Reference readings for depth are the rule reader's band for the same words.

| Measure | Result | Target |
|---|---|---|
| Messages read by the model in batch (claude:claude-haiku-5-5) | 100% (1016/1016) | — |
| Facts shown with the person's exact words | 100% (enforced: a fact whose quote isn't in the message is dropped) | ≥ 95% |
| Depth from words in the same band as the reference reading | 100% (881/881) | ≥ 85% |
| People count read correctly (first-hand reports) | 100% (158/158) | — |
| Neighbour side read correctly (left, right, across) | 100% (50/50) | — |
| "Still safe" replies wrongly marked urgent | 0% (0/359) | low |
| Households counted vs real families heard about | 284–287 vs 265 (the range keeps possible duplicates apart) | truth inside the range |
| Households wrongly merged (two families as one) | 1% (4/287) | ≤ 3% |
| Neighbour words matched to the exact building | 100% (50/50) | ≥ 85% |
| Planted wrong reports flagged doubtful | 93% (13/14) | ≥ 80% |
| Honest reports wrongly flagged doubtful | 3% (23/836) | low |
| Most likely depth at a household vs the true depth there (mean error) | 0.14 m over 752 reports (median 0.12 m) | ≤ 0.2 m |
| Zone water surface vs the true zone surface (mean error, 6 moments) | 0.32 m over 45 zone-moments | — |

Level error by moment (mean absolute, metres):

- 23 Nov 18:00: 0.12 m across 4 zones
- 24 Nov 06:00: 0.32 m across 4 zones
- 24 Nov 18:00: 0.29 m across 8 zones
- 25 Nov 09:00: 0.33 m across 10 zones
- 25 Nov 21:00: 0.34 m across 10 zones
- 26 Nov 12:00: 0.41 m across 9 zones
