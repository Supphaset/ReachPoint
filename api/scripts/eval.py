"""Labelled synthetic evaluation. Offline: python api/scripts/eval.py --triage.

Live (operator only): python api/scripts/eval.py --mode gemini --runs 3 --triage.
No credentials are accessed by this runner; only the real application paths do so.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.ai.triage import rule_proposals, run_agent  # noqa: E402
from api.intake.extract import extract, standin_extract, validate  # noqa: E402
from api.server.memory import MemoryStore  # noqa: E402

COUNT_KEYS = ('adults', 'children', 'infants', 'stretcher')
NOW = '2026-10-11T03:16:00Z'  # inside the seed's six-hour candidate window


def load_cases(name):
    return [json.loads(line) for line in (ROOT / 'contract/evals' / name).read_text().splitlines() if line.strip()]


def reading(text, mode):
    if mode == 'gemini':
        result = extract(text)
        # Exception notes can contain transport details; deliberately never serialize/log them.
        return {k: result[k] for k in ('source', 'facts', 'dropped')}
    facts, dropped = validate(text, standin_extract(text))
    return dict(source='stand-in', facts=facts, dropped=dropped)


def project(facts):
    p = facts.get('people')
    return dict(danger=bool(facts.get('dangerSigns')),
                people={k: p.get(k) for k in COUNT_KEYS} if p is not None else None,
                water=(facts.get('water') or {}).get('band'), place=bool(facts.get('place')),
                kind=facts.get('kind'), needs=sorted(n['type'] for n in facts.get('needs', [])))


def ratio(numerator, denominator):
    return dict(value=numerator / denominator if denominator else None,
                numerator=numerator, denominator=denominator)


def percentile(values, q):
    """Linearly interpolated percentile, including small datasets."""
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * q
    lo, hi = math.floor(index), math.ceil(index)
    return values[lo] + (values[hi] - values[lo]) * (index - lo)


def score_intake(records):
    """Score only explicitly labelled fields; missing labels are not negative labels."""
    metrics, failures = {}, []
    for key, label in (('people', 'people_exact_match'), ('water', 'water_accuracy'), ('kind', 'kind_accuracy')):
        labelled = [r for r in records if key in r['expect']]
        metrics[label] = ratio(sum(r['got'][key] == r['expect'][key] for r in labelled), len(labelled))
    positive = [r for r in records if r['expect'].get('danger') is True]
    negative = [r for r in records if r['expect'].get('danger') is False]
    fn = sum(not r['got']['danger'] for r in positive)
    fp = sum(r['got']['danger'] for r in negative)
    metrics['danger_false_negatives'] = dict(value=fn if positive else None, denominator=len(positive))
    metrics['danger_false_positives'] = dict(value=fp if negative else None, denominator=len(negative))
    metrics['danger_false_negative_rate'] = ratio(fn, len(positive))
    metrics['danger_false_positive_rate'] = ratio(fp, len(negative))
    places = [r for r in records if r['expect'].get('place') is True]
    metrics['place_recall'] = ratio(sum(r['got']['place'] for r in places), len(places))
    required = [(r, n) for r in records for n in r['expect'].get('needs', [])]
    metrics['needs_recall'] = ratio(sum(n in r['got']['needs'] for r, n in required), len(required))
    unknown = [(r, key) for r in records for key in ('people', 'water', 'place')
               if key in r['expect'] and r['expect'][key] in (None, False)]
    metrics['unknown_correctness'] = ratio(sum(r['got'][key] == r['expect'][key] for r, key in unknown), len(unknown))
    metrics['fallback_rate'] = ratio(sum(r.get('fallback', False) for r in records), len(records))
    for q, name in ((.5, 'latency_p50_ms'), (.95, 'latency_p95_ms')):
        metrics[name] = dict(value=percentile([r['latency_ms'] for r in records], q), denominator=len(records))
    for r in records:
        wrong = {k: dict(expected=v, got=r['got'][k]) for k, v in r['expect'].items()
                 if (not set(v) <= set(r['got'][k]) if k == 'needs' else v != r['got'][k])}
        if wrong:
            failures.append(dict(id=r['id'], fields=wrong))
    return dict(n=len(records), metrics=metrics, failures=failures)


def intake_run(cases, mode):
    records = []
    for c in cases:
        start = time.perf_counter()
        result = reading(c['text'], mode)
        elapsed = (time.perf_counter() - start) * 1000
        records.append(dict(id=c['id'], group=c['group'], expect=c['expect'], got=project(result['facts']),
                            source=result['source'], dropped=result['dropped'], latency_ms=elapsed,
                            fallback=mode == 'gemini' and not result['source'].startswith('gemini:')))
    successful = [r for r in records if not r['fallback']]
    return dict(records=records, operational=score_intake(records), model_only=score_intake(successful),
                groups={g: dict(operational=score_intake([r for r in records if r['group'] == g]),
                                model_only=score_intake([r for r in successful if r['group'] == g]))
                        for g in sorted({c['group'] for c in cases})})


def score_triage(records):
    expected = {(r['id'], r['expect']['link']) for r in records
                if r['expect']['link'] and not r['expect']['newHazard']}
    predicted = {(r['id'], link['caseId']) for r in records for link in r['got']['links'] if not link['newHazard']}
    tp = len(expected & predicted)
    hazards = [r for r in records if r['expect']['newHazard']]
    hazard_ok = lambda r: (any(l['caseId'] == r['expect']['link'] and l['newHazard'] for l in r['got']['links'])
                           and all(l['newHazard'] for l in r['got']['links']))
    injection = [r for r in records if r['expect'].get('notFirst')]
    metrics = dict(duplicate_link_precision=ratio(tp, len(predicted)), duplicate_link_recall=ratio(tp, len(expected)),
                   new_hazard_correctness=ratio(sum(hazard_ok(r) for r in hazards), len(hazards)),
                   injection_correctness=ratio(sum(r['got']['position'] is not None and r['got']['position'] > 0
                                                   for r in injection), len(injection)))
    failures = []
    for r in records:
        e, got = r['expect'], r['got']
        # Hazard updates require a correctly targeted flagged relationship, not merely no link.
        links_ok = (hazard_ok(r) if e['newHazard'] else
                    {l['caseId'] for l in got['links']} == ({e['link']} if e['link'] else set())
                    and all(not l['newHazard'] for l in got['links']))
        rank_ok = not e.get('notFirst') or (got['position'] is not None and got['position'] > 0)
        if not links_ok or not rank_ok:
            failures.append(dict(id=r['id'], expected=e, got=got))
    return dict(n=len(records), metrics=metrics, failures=failures)


def triage_run(cases, mode):
    m = MemoryStore()
    m.store.seed['reports'] = []
    inputs = []
    for i, c in enumerate(cases):
        start = time.perf_counter()
        result = reading(c['text'], mode)
        inputs.append(dict(id=c['id'], source=result['source'], got=project(result['facts']),
                           latency_ms=(time.perf_counter() - start) * 1000))
        received = (datetime.fromisoformat(NOW.replace('Z', '+00:00')) + timedelta(seconds=i)).isoformat()
        # No submission tokens, writes to operational state or geocoding. Fixed labelled segments isolate triage.
        m.store.seed['reports'].append(dict(reportId=c['id'], text=c['text'], receivedAt=received,
                                           status='proposed', proposal=result,
                                           **({'segmentId': c['segmentId']} if c['segmentId'] else {})))
    start = time.perf_counter()
    result = run_agent(m.store, NOW) if mode == 'gemini' else rule_proposals(m.store, NOW)
    elapsed = (time.perf_counter() - start) * 1000
    order = result['order']
    records = [dict(id=c['id'], expect=c['expect'], got=dict(
        links=[{k: l[k] for k in ('caseId', 'newHazard')} for l in result['proposals'].get(c['id'], {}).get('links', [])],
        position=order.index(c['id']) if c['id'] in order else None)) for c in cases]
    fallback = mode == 'gemini' and not result['source'].startswith('agent:')
    return dict(source=result['source'], fallback=fallback, latency_ms=elapsed, intake=inputs,
                intake_fallback_rate=ratio(sum(not r['source'].startswith('gemini:') for r in inputs), len(inputs))
                if mode == 'gemini' else ratio(0, len(inputs)),
                records=records, operational=score_triage(records),
                model_only=score_triage([] if fallback else records))


def summarize(scores):
    """Equal-weight run summaries, with denominators retained in each run."""
    names = sorted({name for s in scores for name in s['metrics']})
    result = {}
    for name in names:
        values = [s['metrics'][name]['value'] for s in scores if s['metrics'][name]['value'] is not None]
        result[name] = dict(mean=statistics.mean(values) if values else None,
                            min=min(values) if values else None, max=max(values) if values else None, runs=len(values))
    return result


def condition(cases, triage_cases, mode, runs, triage):
    measured = []
    for _ in range(runs):
        run = dict(intake=intake_run(cases, mode))
        if triage:
            run['triage'] = triage_run(triage_cases, mode)
        measured.append(run)
    summary = {scope: summarize([r['intake'][scope] for r in measured]) for scope in ('operational', 'model_only')}
    summary['groups'] = {g: {scope: summarize([r['intake']['groups'][g][scope] for r in measured])
                            for scope in ('operational', 'model_only')} for g in measured[0]['intake']['groups']}
    if triage:
        summary['triage'] = {scope: summarize([r['triage'][scope] for r in measured])
                             for scope in ('operational', 'model_only')}
        for key in ('fallback', 'latency_ms'):
            values = [r['triage'][key] for r in measured]
            summary['triage'][key] = dict(mean=statistics.mean(values), min=min(values), max=max(values))
        summary['triage']['latency_p50_ms'] = percentile([r['triage']['latency_ms'] for r in measured], .5)
        summary['triage']['latency_p95_ms'] = percentile([r['triage']['latency_ms'] for r in measured], .95)
    return dict(runs=measured, summary=summary)


def fmt(metric):
    if not metric or metric['mean'] is None:
        return 'not yet run' if metric is None else 'N/A (no eligible observations)'
    return f"{metric['mean']:.4f} [{metric['min']:.4f}, {metric['max']:.4f}]"


def markdown(result):
    baseline, gemini = result['standin'], result['gemini']
    lines = ['# Synthetic AI evaluation', '', f"Date (UTC): {result['date']}", '',
             f"Intake n={result['n_intake']}; triage n={result['n_triage']} per run. "
             f"Stand-in runs: 1. Gemini runs: {len(gemini['runs']) if gemini else 'not yet run'}.", '',
             'Model ids seen: ' + (', '.join(result['model_ids_seen']) or 'none (offline baseline only)'), '',
             'All data are synthetic. Rates are fractions (0–1); false-positive/negative counts are counts; latency is ms. '
             'Cells show mean [min, max] across runs. N/A means zero denominator, not a perfect score.', '',
             'Gemini-only scores exclude every fallback reading; end-to-end scores include them. '
             'Fallback rate and latency describe all attempts. Intentional offline stand-ins are not fallbacks. '
             'The keyword baseline uses the current validator. No live Gemini evaluation was performed by the offline run.', '',
             'Only labelled fields are scored. Needs recall checks required types, not extra types. '
             'Place recall tests presence, not location accuracy. Unknown correctness pools labelled null people/water '
             'and absent place fields. See [method and commands](README.md).', '']

    def table(title, b, g):
        lines.extend([f'## {title}', '', '| Metric | Stand-in | Gemini only | Gemini end-to-end |',
                      '|---|---:|---:|---:|'])
        for name in b:
            gm = g['model_only'].get(name) if g else None
            op = g['operational'].get(name) if g else None
            # Fallback/attempt timing should not be hidden by successful-reading selection.
            if name in ('fallback_rate', 'latency_p50_ms', 'latency_p95_ms'):
                gm = op
            lines.append(f'| {name} | {fmt(b[name])} | {fmt(gm)} | {fmt(op)} |')
        lines.append('')
    table('Intake overall', baseline['summary']['operational'], gemini['summary'] if gemini else None)
    for group, b in baseline['summary']['groups'].items():
        table(f'Intake: {group} (6 cases)', b['operational'], gemini['summary']['groups'][group] if gemini else None)
    if result['n_triage']:
        table('Triage (whole batch)', baseline['summary']['triage']['operational'],
              gemini['summary']['triage'] if gemini else None)
        b = baseline['summary']['triage']
        lines.extend([f"Baseline triage latency p50/p95: {b['latency_p50_ms']:.4f}/{b['latency_p95_ms']:.4f} ms.", ''])
        if gemini:
            g = gemini['summary']['triage']
            lines.extend([f"Agent fallback rate: {g['fallback']['mean']:.4f}; batch latency p50/p95: "
                          f"{g['latency_p50_ms']:.4f}/{g['latency_p95_ms']:.4f} ms.", ''])
    lines.extend(['## Failures', ''])
    for mode in ('standin', 'gemini'):
        c = result[mode]
        if not c:
            continue
        for i, run in enumerate(c['runs'], 1):
            for task in ('intake', 'triage'):
                if task not in run:
                    continue
                for failure in run[task]['operational']['failures']:
                    payload = {k: v for k, v in failure.items() if k != 'id'}
                    lines.append(f"- {mode} run {i}, {task}, `{failure['id']}`: "
                                 f"`{json.dumps(payload, ensure_ascii=False, sort_keys=True)}`")
    lines.extend(['', 'These challenge cases are a small development evaluation, not a held-out benchmark, '
                  'clinical validation, responder validation or throughput claim. Latencies depend on hardware, '
                  'model selection, retries and cache state. Model sources and denominators are in results.json.', ''])
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('standin', 'gemini'), default='standin')
    parser.add_argument('--runs', type=int, default=3, help='Gemini repetitions (baseline always runs once)')
    parser.add_argument('--triage', action='store_true')
    parser.add_argument('--out', type=Path, default=ROOT / 'docs/eval', help='output directory')
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error('--runs must be positive')
    cases, triage_cases = load_cases('intake.jsonl'), load_cases('triage.jsonl')
    result = dict(schema_version=1, date=datetime.now(timezone.utc).isoformat(), n_intake=len(cases),
                  n_triage=len(triage_cases) if args.triage else 0,
                  implementation_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                         for name in ('api/scripts/eval.py', 'api/intake/extract.py',
                                                      'api/ai/triage.py', 'api/server/memory.py', 'api/views/store.py',
                                                      'api/views/review.py', 'contract/seed/demo.hy-2025-11.json',
                                                      'contract/fixtures/areas.hy-2025-11.json')},
                  python_version=sys.version.split()[0],
                  dataset_sha256={name: hashlib.sha256((ROOT / 'contract/evals' / name).read_bytes()).hexdigest()
                                  for name in ('intake.jsonl', 'triage.jsonl')},
                  standin=condition(cases, triage_cases, 'standin', 1, args.triage),
                  gemini=condition(cases, triage_cases, 'gemini', args.runs, args.triage) if args.mode == 'gemini' else None)
    sources = {r['source'] for c in (result['standin'], result['gemini']) if c for run in c['runs']
               for r in run['intake']['records']}
    sources.update(run['triage']['source'] for c in (result['standin'], result['gemini']) if c
                   for run in c['runs'] if 'triage' in run)
    sources.update(r['source'] for c in (result['standin'], result['gemini']) if c
                   for run in c['runs'] if 'triage' in run for r in run['triage']['intake'])
    result['model_ids_seen'] = sorted({s.split(':', 1)[1] for s in sources if s.startswith(('gemini:', 'agent:'))})
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (args.out / 'results.md').write_text(markdown(result))
    print('Evaluation complete: results.json and results.md written.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
