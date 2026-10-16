# v2 evaluation: Hat Yai scenario, 21–28 Nov 2025

Run by `python api/scripts/eval_v2.py`. The scenario uses real water data (gauge X.44, rain, satellite, terrain,
building outlines) and synthetic people and messages, so these numbers describe behaviour on realistic messages,
not field accuracy. Reference readings for depth are the rule reader's band for the same words.

| Measure | Result | Target |
|---|---|---|
| Messages read by the model in batch (claude:claude-haiku-5-5) | 95% (1368/1436) | — |
| Facts shown with the person's exact words | 100% (enforced: a fact whose quote isn't in the message is dropped) | ≥ 95% |
| Depth from words in the same band as the reference reading | 100% (1245/1245) | ≥ 85% |
| People count read correctly (first-hand reports) | 100% (158/158) | — |
| Neighbour direction read correctly (north, south, east, west) | 100% (59/59) | — |
| "Still safe" replies wrongly marked urgent | 0% (0/591) | low |
| Households counted vs real families heard about | 284–285 vs 284 (the range keeps possible duplicates apart) | truth inside the range |
| Households wrongly merged (two families as one) | 2% (5/285) | ≤ 3% |
| Neighbour words matched to the exact building | 100% (62/62) | ≥ 85% |
| Planted wrong reports flagged doubtful | 92% (12/13) | ≥ 80% |
| Honest reports wrongly flagged doubtful | 4% (52/1252) | low |
| Depth at a household from the model + OTHER reports (this one left out), mean error | 0.24 m over 1183 reports (median 0.20 m); model alone 0.50 m | better than the model alone |
| Zone water surface vs the true zone surface (mean error, 6 moments) | 1.13 m over 72 zone-moments | — |

Level error by moment (mean absolute, metres):

- 23 Nov 18:00: 1.04 m across 12 zones
- 24 Nov 06:00: 0.64 m across 12 zones
- 24 Nov 18:00: 0.87 m across 12 zones
- 25 Nov 09:00: 1.47 m across 12 zones
- 25 Nov 21:00: 1.41 m across 12 zones
- 26 Nov 12:00: 1.33 m across 12 zones
