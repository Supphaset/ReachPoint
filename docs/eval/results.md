# Synthetic AI evaluation

Date (UTC): 2026-10-13T07:23:44.040698+00:00

Intake n=36; triage n=12 per run. Stand-in runs: 1. Gemini runs: 3.

Model ids seen: gemini-3.5-flash-lite, gemini-flash-lite-latest

All data are synthetic. Rates are fractions (0–1); false-positive/negative counts are counts; latency is ms. Cells show mean [min, max] across runs. N/A means zero denominator, not a perfect score.

Gemini-only scores exclude every fallback reading; end-to-end scores include them. Fallback rate and latency describe all attempts. Intentional offline stand-ins are not fallbacks. The keyword baseline uses the current validator. No live Gemini evaluation was performed by the offline run.

Only labelled fields are scored. Needs recall checks required types, not extra types. Place recall tests presence, not location accuracy. Unknown correctness pools labelled null people/water and absent place fields. See [method and commands](README.md).

## Intake overall

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | 0.3333 [0.3333, 0.3333] | 0.0000 [0.0000, 0.0000] | 0.1111 [0.0000, 0.3333] |
| danger_false_negatives | 2.0000 [2.0000, 2.0000] | 0.0000 [0.0000, 0.0000] | 0.6667 [0.0000, 2.0000] |
| danger_false_positive_rate | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| danger_false_positives | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| fallback_rate | 0.0000 [0.0000, 0.0000] | 0.3056 [0.0278, 0.4722] | 0.3056 [0.0278, 0.4722] |
| kind_accuracy | 0.3333 [0.3333, 0.3333] | 1.0000 [1.0000, 1.0000] | 0.8333 [0.5000, 1.0000] |
| latency_p50_ms | 0.4284 [0.4284, 0.4284] | 1549.6582 [1311.9236, 1697.2074] | 1549.6582 [1311.9236, 1697.2074] |
| latency_p95_ms | 0.8501 [0.8501, 0.8501] | 1987.0619 [1824.0983, 2102.9195] | 1987.0619 [1824.0983, 2102.9195] |
| needs_recall | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |
| people_exact_match | 0.5000 [0.5000, 0.5000] | 1.0000 [1.0000, 1.0000] | 0.8056 [0.5000, 1.0000] |
| place_recall | 0.0000 [0.0000, 0.0000] | 0.9744 [0.9231, 1.0000] | 0.5897 [0.2308, 0.9231] |
| unknown_correctness | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |
| water_accuracy | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |

## Intake: counts (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_negatives | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_positive_rate | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_positives | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| fallback_rate | 0.0000 [0.0000, 0.0000] | 0.3889 [0.0000, 1.0000] | 0.3889 [0.0000, 1.0000] |
| kind_accuracy | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| latency_p50_ms | 0.4578 [0.4578, 0.4578] | 1439.1423 [1257.4569, 1753.3679] | 1439.1423 [1257.4569, 1753.3679] |
| latency_p95_ms | 0.5936 [0.5936, 0.5936] | 1725.0076 [1631.0215, 1872.2021] | 1725.0076 [1631.0215, 1872.2021] |
| needs_recall | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| people_exact_match | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.6111 [0.0000, 1.0000] |
| place_recall | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| unknown_correctness | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| water_accuracy | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |

## Intake: danger (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | 0.3333 [0.3333, 0.3333] | 0.0000 [0.0000, 0.0000] | 0.1111 [0.0000, 0.3333] |
| danger_false_negatives | 2.0000 [2.0000, 2.0000] | 0.0000 [0.0000, 0.0000] | 0.6667 [0.0000, 2.0000] |
| danger_false_positive_rate | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_positives | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| fallback_rate | 0.0000 [0.0000, 0.0000] | 0.2222 [0.0000, 0.6667] | 0.2222 [0.0000, 0.6667] |
| kind_accuracy | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| latency_p50_ms | 0.7221 [0.7221, 0.7221] | 1570.0435 [1414.6497, 1702.0100] | 1570.0435 [1414.6497, 1702.0100] |
| latency_p95_ms | 1.0117 [1.0117, 1.0117] | 1878.8100 [1676.6056, 1997.8547] | 1878.8100 [1676.6056, 1997.8547] |
| needs_recall | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |
| people_exact_match | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| place_recall | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.6667 [0.0000, 1.0000] |
| unknown_correctness | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| water_accuracy | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |

## Intake: kind (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_negatives | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_positive_rate | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_positives | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| fallback_rate | 0.0000 [0.0000, 0.0000] | 0.2778 [0.0000, 0.8333] | 0.2778 [0.0000, 0.8333] |
| kind_accuracy | 0.3333 [0.3333, 0.3333] | 1.0000 [1.0000, 1.0000] | 0.8333 [0.5000, 1.0000] |
| latency_p50_ms | 0.3394 [0.3394, 0.3394] | 1610.7454 [1406.1715, 1891.1761] | 1610.7454 [1406.1715, 1891.1761] |
| latency_p95_ms | 0.5186 [0.5186, 0.5186] | 1957.0240 [1584.0694, 2221.7799] | 1957.0240 [1584.0694, 2221.7799] |
| needs_recall | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |
| people_exact_match | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| place_recall | 0.0000 [0.0000, 0.0000] | 0.9444 [0.8333, 1.0000] | 0.6667 [0.1667, 1.0000] |
| unknown_correctness | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| water_accuracy | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |

## Intake: negation (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_negatives | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_positive_rate | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| danger_false_positives | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| fallback_rate | 0.0000 [0.0000, 0.0000] | 0.2222 [0.0000, 0.5000] | 0.2222 [0.0000, 0.5000] |
| kind_accuracy | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| latency_p50_ms | 0.4055 [0.4055, 0.4055] | 1402.7275 [1264.9787, 1618.7278] | 1402.7275 [1264.9787, 1618.7278] |
| latency_p95_ms | 1.3638 [1.3638, 1.3638] | 1824.2527 [1388.7483, 2059.0600] | 1824.2527 [1388.7483, 2059.0600] |
| needs_recall | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| people_exact_match | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| place_recall | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| unknown_correctness | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| water_accuracy | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |

## Intake: unknown (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_negatives | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_positive_rate | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| danger_false_positives | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| fallback_rate | 0.0000 [0.0000, 0.0000] | 0.2222 [0.0000, 0.6667] | 0.2222 [0.0000, 0.6667] |
| kind_accuracy | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| latency_p50_ms | 0.2620 [0.2620, 0.2620] | 1371.4395 [1142.6635, 1743.1471] | 1371.4395 [1142.6635, 1743.1471] |
| latency_p95_ms | 0.5811 [0.5811, 0.5811] | 1660.2078 [1324.9185, 1989.4149] | 1660.2078 [1324.9185, 1989.4149] |
| needs_recall | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| people_exact_match | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |
| place_recall | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| unknown_correctness | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |
| water_accuracy | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |

## Intake: water_place (6 cases)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| danger_false_negative_rate | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_negatives | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_positive_rate | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| danger_false_positives | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| fallback_rate | 0.0000 [0.0000, 0.0000] | 0.5000 [0.0000, 0.8333] | 0.5000 [0.0000, 0.8333] |
| kind_accuracy | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| latency_p50_ms | 0.4441 [0.4441, 0.4441] | 1668.4258 [1315.0535, 1917.3439] | 1668.4258 [1315.0535, 1917.3439] |
| latency_p95_ms | 0.5344 [0.5344, 0.5344] | 1888.9062 [1605.4560, 2173.2053] | 1888.9062 [1605.4560, 2173.2053] |
| needs_recall | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| people_exact_match | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| place_recall | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.5000 [0.1667, 1.0000] |
| unknown_correctness | N/A (no eligible observations) | N/A (no eligible observations) | N/A (no eligible observations) |
| water_accuracy | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |

## Triage (whole batch)

| Metric | Stand-in | Gemini only | Gemini end-to-end |
|---|---:|---:|---:|
| duplicate_link_precision | 0.6667 [0.6667, 0.6667] | N/A (no eligible observations) | 0.8222 [0.6667, 1.0000] |
| duplicate_link_recall | 1.0000 [1.0000, 1.0000] | N/A (no eligible observations) | 1.0000 [1.0000, 1.0000] |
| injection_correctness | 1.0000 [1.0000, 1.0000] | N/A (no eligible observations) | 1.0000 [1.0000, 1.0000] |
| new_hazard_correctness | 1.0000 [1.0000, 1.0000] | N/A (no eligible observations) | 0.8333 [0.5000, 1.0000] |

Baseline triage latency p50/p95: 12.1956/12.1956 ms.

Agent fallback rate: 1.0000; batch latency p50/p95: 6735.2205/8247.7934 ms.

## Failures

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
- standin run 1, intake, `kind-01`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-02`: `{"fields": {"place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-03`: `{"fields": {"kind": {"expected": "check_on", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-04`: `{"fields": {"kind": {"expected": "check_on", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-05`: `{"fields": {"kind": {"expected": "neighbour_report", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- standin run 1, intake, `kind-06`: `{"fields": {"kind": {"expected": "neighbour_report", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- standin run 1, triage, `different-household-03`: `{"expected": {"link": null, "newHazard": false}, "got": {"links": [{"caseId": "C-03", "newHazard": false}], "position": 6}}`
- standin run 1, triage, `different-household-02`: `{"expected": {"link": null, "newHazard": false}, "got": {"links": [{"caseId": "C-02", "newHazard": false}], "position": 7}}`
- gemini run 1, intake, `counts-06`: `{"fields": {"people": {"expected": {"adults": 2, "children": 1, "infants": 0, "stretcher": 0}, "got": null}}}`
- gemini run 1, intake, `kind-05`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 1, triage, `different-household-03`: `{"expected": {"link": null, "newHazard": false}, "got": {"links": [{"caseId": "C-03", "newHazard": false}], "position": 6}}`
- gemini run 1, triage, `different-household-02`: `{"expected": {"link": null, "newHazard": false}, "got": {"links": [{"caseId": "C-02", "newHazard": false}], "position": 7}}`
- gemini run 2, intake, `water_place-01`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 2, intake, `water_place-02`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 2, intake, `water_place-03`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 2, intake, `water_place-04`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 2, intake, `water_place-06`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 2, intake, `kind-01`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 2, intake, `kind-02`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 2, intake, `kind-04`: `{"fields": {"kind": {"expected": "check_on", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- gemini run 2, intake, `kind-05`: `{"fields": {"kind": {"expected": "neighbour_report", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- gemini run 2, intake, `kind-06`: `{"fields": {"kind": {"expected": "neighbour_report", "got": "my_household"}, "place": {"expected": true, "got": false}}}`
- gemini run 2, triage, `hazard-08`: `{"expected": {"link": "C-08", "newHazard": true}, "got": {"links": [], "position": 1}}`
- gemini run 3, intake, `danger-04`: `{"fields": {"danger": {"expected": true, "got": false}}}`
- gemini run 3, intake, `danger-06`: `{"fields": {"danger": {"expected": true, "got": false}, "place": {"expected": true, "got": false}}}`
- gemini run 3, intake, `counts-01`: `{"fields": {"people": {"expected": {"adults": 2, "children": 0, "infants": 1, "stretcher": 0}, "got": null}}}`
- gemini run 3, intake, `counts-02`: `{"fields": {"people": {"expected": {"adults": 3, "children": 2, "infants": 0, "stretcher": 0}, "got": null}}}`
- gemini run 3, intake, `counts-03`: `{"fields": {"people": {"expected": {"adults": 4, "children": 0, "infants": 0, "stretcher": 0}, "got": null}}}`
- gemini run 3, intake, `counts-04`: `{"fields": {"people": {"expected": {"adults": 2, "children": 1, "infants": 1, "stretcher": 0}, "got": null}}}`
- gemini run 3, intake, `counts-05`: `{"fields": {"people": {"expected": {"adults": 1, "children": 0, "infants": 0, "stretcher": 1}, "got": null}}}`
- gemini run 3, intake, `counts-06`: `{"fields": {"people": {"expected": {"adults": 2, "children": 1, "infants": 0, "stretcher": 0}, "got": null}}}`
- gemini run 3, intake, `water_place-01`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 3, intake, `water_place-02`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 3, intake, `water_place-03`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 3, intake, `water_place-04`: `{"fields": {"place": {"expected": true, "got": false}}}`
- gemini run 3, triage, `different-household-03`: `{"expected": {"link": null, "newHazard": false}, "got": {"links": [{"caseId": "C-03", "newHazard": false}], "position": 6}}`

These challenge cases are a small development evaluation, not a held-out benchmark, clinical validation, responder validation or throughput claim. Latencies depend on hardware, model selection, retries and cache state. Model sources and denominators are in results.json.
