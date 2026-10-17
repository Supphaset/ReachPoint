# v2 evaluation: Hat Yai scenario, 21–28 Nov 2025

Run by `python api/scripts/eval_v2.py`. The scenario uses real water data (gauge X.44, rain, satellite, terrain,
building outlines) and synthetic people and messages, so these numbers describe behaviour on realistic messages,
not field accuracy. Reference readings for depth are the rule reader's band for the same words.

| Measure | Result | Target |
|---|---|---|
| Messages read by the model in batch (gemini:gemini-3.5-flash-lite, gemini:gemini-flash-lite-latest) | 100% (1517/1522) | — |
| Facts shown with the person's exact words | 100% (enforced: a fact whose quote isn't in the message is dropped) | ≥ 95% |
| Depth from words in the same band as the reference reading | 100% (1405/1405) | ≥ 85% |
| People count read correctly (first-hand reports) | 100% (176/176) | — |
| Neighbour direction read correctly (north, south, east, west) | 100% (72/72) | — |
| "Still safe" replies wrongly marked urgent | 0% (0/751) | low |
| Households counted vs real families heard about | 306–309 vs 299 (the range keeps possible duplicates apart) | truth inside the range |
| Households wrongly merged (two families as one) | 1% (2/309) | ≤ 3% |
| Neighbour words matched to the exact building | 100% (72/72) | ≥ 85% |
| Planted wrong reports flagged doubtful | 80% (4/5) | ≥ 80% |
| Honest reports wrongly flagged doubtful | 5% (65/1345) | low |
| Depth at a household from the model + OTHER reports (this one left out), mean error | 0.27 m over 1251 reports (median 0.23 m); model alone 0.46 m | better than the model alone |
| Zone water surface vs the true zone surface (mean error, 6 moments) | 1.10 m over 305 zone-moments | — |

Level error by moment (mean absolute, metres):

- 23 Nov 18:00: 1.13 m across 52 zones
- 24 Nov 06:00: 0.92 m across 55 zones
- 24 Nov 18:00: 0.95 m across 59 zones
- 25 Nov 09:00: 1.28 m across 46 zones
- 25 Nov 21:00: 1.21 m across 47 zones
- 26 Nov 12:00: 1.17 m across 46 zones
