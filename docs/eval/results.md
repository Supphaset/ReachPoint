# Synthetic AI evaluation

Date (UTC): 2026-10-13T07:00:43.093879+00:00

Intake n=36; triage n=12 per run. Stand-in runs: 1. Gemini runs: not yet run.

Model ids seen: none (offline baseline only)

All data are synthetic. Rates are fractions (0–1); false-positive/negative counts are counts; latency is ms. Cells show mean [min, max] across runs. N/A means zero denominator, not a perfect score.

Gemini-only scores exclude every fallback reading; end-to-end scores include them. Fallback rate and latency describe all attempts. Intentional offline stand-ins are not fallbacks. The keyword baseline uses the current validator. No live Gemini evaluation was performed by the offline run.

Only labelled fields are scored. Needs recall checks required types, not extra types. Place recall tests presence, not location accuracy. Unknown correctness pools labelled null people/water and absent place fields. See [method and commands](README.md).

## Intake overall

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | 0.3333 [0.3333, 0.3333] | not yet run | not yet run |
| danger_false_negatives | 2.0000 [2.0000, 2.0000] | not yet run | not yet run |
| danger_false_positive_rate | 0.5000 [0.5000, 0.5000] | not yet run | not yet run |
| danger_false_positives | 6.0000 [6.0000, 6.0000] | not yet run | not yet run |
| fallback_rate | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| kind_accuracy | 0.3333 [0.3333, 0.3333] | not yet run | not yet run |
| latency_p50_ms | 0.3873 [0.3873, 0.3873] | not yet run | not yet run |
| latency_p95_ms | 1.4527 [1.4527, 1.4527] | not yet run | not yet run |
| needs_recall | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |
| people_exact_match | 0.5000 [0.5000, 0.5000] | not yet run | not yet run |
| place_recall | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| unknown_correctness | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |
| water_accuracy | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |

## Intake: counts (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_negatives | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_positive_rate | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_positives | N/A (no eligible observations) | not yet run | not yet run |
| fallback_rate | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| kind_accuracy | N/A (no eligible observations) | not yet run | not yet run |
| latency_p50_ms | 0.3570 [0.3570, 0.3570] | not yet run | not yet run |
| latency_p95_ms | 0.4487 [0.4487, 0.4487] | not yet run | not yet run |
| needs_recall | N/A (no eligible observations) | not yet run | not yet run |
| people_exact_match | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| place_recall | N/A (no eligible observations) | not yet run | not yet run |
| unknown_correctness | N/A (no eligible observations) | not yet run | not yet run |
| water_accuracy | N/A (no eligible observations) | not yet run | not yet run |

## Intake: danger (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | 0.3333 [0.3333, 0.3333] | not yet run | not yet run |
| danger_false_negatives | 2.0000 [2.0000, 2.0000] | not yet run | not yet run |
| danger_false_positive_rate | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_positives | N/A (no eligible observations) | not yet run | not yet run |
| fallback_rate | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| kind_accuracy | N/A (no eligible observations) | not yet run | not yet run |
| latency_p50_ms | 0.2945 [0.2945, 0.2945] | not yet run | not yet run |
| latency_p95_ms | 0.4078 [0.4078, 0.4078] | not yet run | not yet run |
| needs_recall | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |
| people_exact_match | N/A (no eligible observations) | not yet run | not yet run |
| place_recall | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| unknown_correctness | N/A (no eligible observations) | not yet run | not yet run |
| water_accuracy | N/A (no eligible observations) | not yet run | not yet run |

## Intake: kind (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_negatives | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_positive_rate | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_positives | N/A (no eligible observations) | not yet run | not yet run |
| fallback_rate | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| kind_accuracy | 0.3333 [0.3333, 0.3333] | not yet run | not yet run |
| latency_p50_ms | 0.7599 [0.7599, 0.7599] | not yet run | not yet run |
| latency_p95_ms | 1.2516 [1.2516, 1.2516] | not yet run | not yet run |
| needs_recall | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |
| people_exact_match | N/A (no eligible observations) | not yet run | not yet run |
| place_recall | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| unknown_correctness | N/A (no eligible observations) | not yet run | not yet run |
| water_accuracy | N/A (no eligible observations) | not yet run | not yet run |

## Intake: negation (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_negatives | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_positive_rate | 0.6667 [0.6667, 0.6667] | not yet run | not yet run |
| danger_false_positives | 4.0000 [4.0000, 4.0000] | not yet run | not yet run |
| fallback_rate | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| kind_accuracy | N/A (no eligible observations) | not yet run | not yet run |
| latency_p50_ms | 0.7126 [0.7126, 0.7126] | not yet run | not yet run |
| latency_p95_ms | 1.5952 [1.5952, 1.5952] | not yet run | not yet run |
| needs_recall | N/A (no eligible observations) | not yet run | not yet run |
| people_exact_match | N/A (no eligible observations) | not yet run | not yet run |
| place_recall | N/A (no eligible observations) | not yet run | not yet run |
| unknown_correctness | N/A (no eligible observations) | not yet run | not yet run |
| water_accuracy | N/A (no eligible observations) | not yet run | not yet run |

## Intake: unknown (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_negatives | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_positive_rate | 0.3333 [0.3333, 0.3333] | not yet run | not yet run |
| danger_false_positives | 2.0000 [2.0000, 2.0000] | not yet run | not yet run |
| fallback_rate | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| kind_accuracy | N/A (no eligible observations) | not yet run | not yet run |
| latency_p50_ms | 0.4775 [0.4775, 0.4775] | not yet run | not yet run |
| latency_p95_ms | 1.5876 [1.5876, 1.5876] | not yet run | not yet run |
| needs_recall | N/A (no eligible observations) | not yet run | not yet run |
| people_exact_match | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |
| place_recall | N/A (no eligible observations) | not yet run | not yet run |
| unknown_correctness | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |
| water_accuracy | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |

## Intake: water_place (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_negatives | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_positive_rate | N/A (no eligible observations) | not yet run | not yet run |
| danger_false_positives | N/A (no eligible observations) | not yet run | not yet run |
| fallback_rate | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| kind_accuracy | N/A (no eligible observations) | not yet run | not yet run |
| latency_p50_ms | 0.3021 [0.3021, 0.3021] | not yet run | not yet run |
| latency_p95_ms | 0.3438 [0.3438, 0.3438] | not yet run | not yet run |
| needs_recall | N/A (no eligible observations) | not yet run | not yet run |
| people_exact_match | N/A (no eligible observations) | not yet run | not yet run |
| place_recall | 0.0000 [0.0000, 0.0000] | not yet run | not yet run |
| unknown_correctness | N/A (no eligible observations) | not yet run | not yet run |
| water_accuracy | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |

## Triage (whole batch)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| duplicate_link_precision | 0.6667 [0.6667, 0.6667] | not yet run | not yet run |
| duplicate_link_recall | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |
| injection_correctness | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |
| new_hazard_correctness | 1.0000 [1.0000, 1.0000] | not yet run | not yet run |

Baseline triage latency p50/p95: 11.2639/11.2639 ms.

## Failures

- standin run 1, intake, `negation-01`: `{"fields": {"danger": {"expected": false, "got": true}}}`
- standin run 1, intake, `negation-02`: `{"fields": {"danger": {"expected": false, "got": true}}}`
- standin run 1, intake, `negation-04`: `{"fields": {"danger": {"expected": false, "got": true}}}`
- standin run 1, intake, `negation-05`: `{"fields": {"danger": {"expected": false, "got": true}}}`
- standin run 1, intake, `danger-04`: `{"fields": {"danger": {"expected": true, "got": false}}}`
- standin run 1, intake, `danger-06`: `{"fields": {"danger": {"expected": true, "got": false}, "place": {"expected": true, "got": false}}}`
- standin run 1, intake, `counts-01`: `{"fields": {"people": {"expected": {"adults": 2, "children": 0, "infants": 1, "stretcher": 0}, "got": null}}}`
- standin run 1, intake, `counts-02`: `{"fields": {"people": {"expected": {"adults": 3, "children": 2, "infants": 0, "stretcher": 0}, "got": null}}}`
- standin run 1, intake, `counts-03`: `{"fields": {"people": {"expected": {"adults": 4, "children": 0, "infants": 0, "stretcher": 0}, "got": null}}}`
- standin run 1, intake, `counts-04`: `{"fields": {"people": {"expected": {"adults": 2, "children": 1, "infants": 1, "stretcher": 0}, "got": null}}}`
- standin run 1, intake, `counts-05`: `{"fields": {"people": {"expected": {"adults": 1, "children": 0, "infants": 0, "stretcher": 1}, "got": null}}}`
- standin run 1, intake, `counts-06`: `{"fields": {"people": {"expected": {"adults": 2, "children": 1, "infants": 0, "stretcher": 0}, "got": null}}}`
- standin run 1, intake, `water_place-01`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `water_place-02`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `water_place-03`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `water_place-04`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `water_place-05`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `water_place-06`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `unknown-05`: `{"fields": {"danger": {"expected": false, "got": true}}}`
- standin run 1, intake, `unknown-06`: `{"fields": {"danger": {"expected": false, "got": true}}}`
- standin run 1, intake, `kind-01`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-02`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-03`: `{"fields": {"kind": {"expected": "check_on", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-04`: `{"fields": {"kind": {"expected": "check_on", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-05`: `{"fields": {"kind": {"expected": "neighbour_report", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-06`: `{"fields": {"kind": {"expected": "neighbour_report", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- standin run 1, triage, `different-household-03`: `{"expected": {"link": null, "newHazard": false}, "got": {"links": [{"caseId": "C-03", "newHazard": false}], "position": 6}}`
- standin run 1, triage, `different-household-02`: `{"expected": {"link": null, "newHazard": false}, "got": {"links": [{"caseId": "C-02", "newHazard": false}], "position": 7}}`

These challenge cases are a small development evaluation, not a held-out benchmark, clinical validation, responder validation or throughput claim. Latencies depend on hardware, model selection, retries and cache state. Model sources and denominators are in results.json.
