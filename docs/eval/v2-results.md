# v2 evaluation: Hat Yai scenario, 21–28 Nov 2025

Run by `python api/scripts/eval_v2.py`. The scenario uses real water data (gauge X.44, rain, satellite, terrain,
building outlines) and synthetic people and messages, so these numbers describe behaviour on realistic messages,
not field accuracy. Reference readings for depth are the rule reader's band for the same words.

| Measure | Result | Target |
|---|---|---|
| Messages read by Gemini (batch) | 0% (0/993) | — |
| Facts shown with the person's exact words | 100% (enforced: a fact whose quote isn't in the message is dropped) | ≥ 95% |
| Depth from words in the same band as the reference reading | — | ≥ 85% |
| People count read correctly (first-hand reports) | — | — |
| Neighbour side read correctly (left, right, across) | — | — |
| "Still safe" replies wrongly marked urgent | — | low |
| Households counted vs real families heard about | 276–280 vs 272 (the range keeps possible duplicates apart) | truth inside the range |
| Households wrongly merged (two families as one) | 0% (1/280) | ≤ 3% |
| Neighbour words matched to the exact building | 91% (61/67) | ≥ 85% |
| Planted wrong reports flagged doubtful | 100% (6/6) | ≥ 80% |
| Honest reports wrongly flagged doubtful | 1% (8/825) | low |
| Most likely level vs the true level (mean error, 6 moments × zones) | 0.17 m over 66 zone-moments | ≤ 0.2 m |

Level error by moment (mean absolute, metres):

- 23 Nov 18:00: 0.10 m across 11 zones
- 24 Nov 06:00: 0.13 m across 11 zones
- 24 Nov 18:00: 0.25 m across 11 zones
- 25 Nov 09:00: 0.09 m across 11 zones
- 25 Nov 21:00: 0.15 m across 11 zones
- 26 Nov 12:00: 0.29 m across 11 zones
