# v2 evaluation: Hat Yai scenario, 21–28 Nov 2025

Run by `python api/scripts/eval_v2.py`. The scenario uses real water data (gauge X.44, rain, satellite, terrain,
building outlines) and synthetic people and messages, so these numbers describe behaviour on realistic messages,
not field accuracy. Reference readings for depth are the rule reader's band for the same words.

| Measure | Result | Target |
|---|---|---|
| Messages read by the model in batch (claude:claude-haiku-5-5) | 10% (150/1492) | — |
| Facts shown with the person's exact words | 100% (enforced: a fact whose quote isn't in the message is dropped) | ≥ 95% |
| Depth from words in the same band as the reference reading | 100% (150/150) | ≥ 85% |
| People count read correctly (first-hand reports) | 100% (112/112) | — |
| Neighbour side read correctly (left, right, across) | 100% (42/42) | — |
| "Still safe" replies wrongly marked urgent | — | low |
| Households counted vs real families heard about | 309–311 vs 296 (the range keeps possible duplicates apart) | truth inside the range |
| Households wrongly merged (two families as one) | 0% (0/311) | ≤ 3% |
| Neighbour words matched to the exact building | 97% (64/66) | ≥ 85% |
| Planted wrong reports flagged doubtful | 80% (12/15) | ≥ 80% |
| Honest reports wrongly flagged doubtful | 5% (64/1288) | low |
| Depth at a household from the model + OTHER reports (this one left out), mean error | 0.30 m over 1278 reports (median 0.26 m); model alone 0.51 m | better than the model alone |
| Zone water surface vs the true zone surface (mean error, 6 moments) | 1.39 m over 76 zone-moments | — |

Level error by moment (mean absolute, metres):

- 23 Nov 18:00: 1.50 m across 11 zones
- 24 Nov 06:00: 1.01 m across 13 zones
- 24 Nov 18:00: 1.18 m across 13 zones
- 25 Nov 09:00: 1.38 m across 13 zones
- 25 Nov 21:00: 1.54 m across 13 zones
- 26 Nov 12:00: 1.76 m across 13 zones
