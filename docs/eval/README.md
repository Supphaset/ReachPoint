# Reproducing the synthetic evaluation

Run from the repository root, using the existing environment (no packages to install):

```sh
.venv/bin/python api/scripts/eval.py --mode standin --triage
.venv/bin/python -m pytest -q -p no:cacheprovider api/tests
```

The offline command never calls `extract()`, `run_agent()` or their key readers. It imports their modules, calls `validate(text, standin_extract(text))`, and calls `rule_proposals()` for triage. It does not read the private environment file, make network requests or write operational records. Use `--out /tmp/reachpoint-eval-results` to keep artifacts outside the checkout.

An operator with the configured key can subsequently run:

```sh
.venv/bin/python api/scripts/eval.py --mode gemini --runs 3 --triage
```

This recomputes the offline baseline once and the real extraction and ADK paths three times, replacing both result files. The application reads its own key. The runner never handles credentials and omits exception notes, raw transport errors, rank reasons and operational tokens from artifacts. Gemini has **not yet been run** in the committed baseline.

Read [results.md](results.md) for tables and failures, and [results.json](results.json) for per-reading sources, latency, projected fields, denominators and repeated-run summaries. Dataset and implementation fingerprints allow later comparisons to identify changed inputs or validators. Exact timings are not reproducible across machines.

## Labels and scoring

The intake set has six groups of six: negation, genuine danger, counts, water/place, unknown/injection and report kind. Thai-only messages form at least half; other cases are English or mixed. These are invented reports at generic landmarks already used in the Hat Yai fixtures, with no real households, names, phone numbers or addresses. Labels represent human interpretation, independently of what the current parser can extract. They have not been independently annotated by a responder.

Only fields present in `expect` are scored. An absent label means **not evaluated**, not an expected null. This makes task-specific denominators explicit and avoids guessed facts becoming ground truth. Count examples specify otherwise absent categories; adults/children/infants count people by age, while stretcher is an overlapping carrying requirement (the single bedridden adult remains an adult). Historical, negated and conditional dangers are negative labels. `needs` lists required assistance types; empty lists do not penalize extra types. Requests to check on someone do not automatically label evacuation or medical need.

- Danger false negatives/positives: counts, with denominators of labelled positive/negative reports; accompanying rates use those denominators. This evaluates **any current danger**, not the precision of individual danger descriptions.
- People: exact equality across all four count fields, including expected null.
- Water: exact band or expected null.
- Place: recall for labelled place presence, not geocoding correctness. Expected absence contributes to unknown correctness.
- Kind: exact category equality.
- Needs: micro recall across required types; extra needs are not scored as false positives.
- Unknown: pooled correctness across labelled null people/water and absent place fields, including the injection examples.
- Latency: wall time around the full extraction call, including retries and fallback; p50/p95 use linear interpolation. Baseline excludes model imports/key reads because it uses the offline path directly.

For each run there are overall and per-group scores. Repeated-run summaries give equal-weight mean/min/max of defined metrics, without treating zero denominators as perfect scores. Every reading whose source does not start with `gemini:` is a fallback in Gemini mode and is excluded from model-only scores. End-to-end scores include all readings. Fallback rate and attempt latency always include all attempts. Intentional stand-in baseline calls have zero fallback rate.

## Triage isolation and limitations

All 12 triage reports are run together on a fresh `MemoryStore` snapshot per run. Seed cases are retained; proposed reports are replaced with just the evaluation batch. Fixed timestamps start at `2026-10-11T03:16:00Z`, within six hours of seed confirmations. Labelled `segmentId` inputs isolate household/link reasoning from location resolution. Intake facts still come from the selected extractor, so missed danger signs can affect triage; every triage input source and projected reading is recorded. This does not measure a full geocoding or submission workflow.

Duplicates explicitly refer to existing synthetic case IDs and household sizes in different words/languages; this is an easier identity test than unreferenced real-world duplicate matching. Different-household cases explicitly distinguish themselves despite the same landmark. Two hazard updates require a link to the **right case** with `newHazard=true` and no ordinary duplicate link. Merely abstaining is not a success on this measure. Unrelated and injection reports expect no link; injection also must not appear first in the batch.

Duplicate precision/recall operates on unique `(report ID, case ID)` pairs for **ordinary** links. Wrong targets count as false positives and missed expected pairs. Hazard relations are scored separately. Agent fallback (`source` not starting with `agent:`) is excluded from agent-only metrics; extraction fallback within an otherwise real agent run is exposed separately, and can still influence agent outcomes. Triage latency measures a whole batch, with p50/p95 across batches. The keyword/rules baseline is not ADK execution. The tool call list is not treated as proof of model-directed ADK events.

This small development challenge set is not held out from prompt development and does not establish clinical safety, field effectiveness, workload reduction or production throughput. No coordinator timing drill was performed. Re-run after validator changes; do not compare code revisions as though only the model changed.

## Validation of this baseline

On 13 Oct 2026, the offline runner completed with triage enabled; all seven evaluation tests passed. The requested full API command produced **211 passed, 1 failed**: the existing notebook execution test could not bind a local Jupyter kernel socket (`PermissionError: Operation not permitted`) in this sandbox. This is a runtime validation limitation, not a passing full-suite claim. No unrelated test or application implementation was changed to bypass it. The extractor and triage files were left untouched; re-run this evaluation when the concurrent validator changes are integrated.
