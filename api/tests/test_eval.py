"""Offline evaluation contract and scorer checks; live paths are replaced with fakes."""
import json
from collections import Counter

import pytest

from api.scripts import eval as evaluation


def test_datasets_are_labelled_and_synthetic():
    intake = evaluation.load_cases('intake.jsonl')
    triage = evaluation.load_cases('triage.jsonl')
    assert len(intake) == 36 and len(triage) == 14
    assert Counter(c['group'] for c in intake) == dict.fromkeys(
        ('negation', 'danger', 'counts', 'water_place', 'unknown', 'kind'), 6)
    assert sum(c['lang'] == 'th' for c in intake) >= 18
    assert any(c['lang'] == 'mixed' for c in intake)
    ids = [c['id'] for c in intake + triage]
    assert len(ids) == len(set(ids))
    for c in intake:
        assert set(c) == {'id', 'group', 'lang', 'text', 'expect'}
        assert c['text'] and c['expect']
        assert set(c['expect']) <= {'danger', 'people', 'water', 'place', 'kind', 'needs'}
        p = c['expect'].get('people')
        if p is not None:
            assert set(p) == set(evaluation.COUNT_KEYS)
            assert all(type(v) is int and v >= 0 for v in p.values())
        assert c['expect'].get('water') in (None, 'knee', 'waist', 'chest', 'over_head', 'second_floor')
        assert set(c['expect'].get('needs', [])) <= {'medical', 'supplies', 'evacuation_transport'}
    store = evaluation.MemoryStore().store
    case_ids = {c['caseId'] for c in store.cases}
    for c in triage:
        assert c['expect']['link'] is None or c['expect']['link'] in case_ids
        assert c['segmentId'] is None or c['segmentId'] in store.landmarks


def test_intake_scorer_hand_calculated():
    p = dict(adults=2, children=0, infants=0, stretcher=0)
    rows = [
        dict(id='a', expect=dict(danger=True, people=p, water='knee', place=True,
                                kind='check_on', needs=['medical', 'supplies']),
             got=dict(danger=False, people=None, water='knee', place=True, kind='my_household', needs=['medical']),
             latency_ms=10, fallback=False),
        dict(id='b', expect=dict(danger=False, people=None, water=None, place=False,
                                kind='my_household', needs=['supplies']),
             got=dict(danger=True, people=None, water='waist', place=False, kind='my_household', needs=['supplies']),
             latency_ms=30, fallback=True),
    ]
    score = evaluation.score_intake(rows)
    m = score['metrics']
    assert m['danger_false_negatives'] == {'value': 1, 'denominator': 1}
    assert m['danger_false_positives'] == {'value': 1, 'denominator': 1}
    for name in ('people_exact_match', 'water_accuracy', 'kind_accuracy', 'fallback_rate'):
        assert m[name]['value'] == .5
    assert m['place_recall']['value'] == 1
    assert m['needs_recall'] == dict(value=2/3, numerator=2, denominator=3)
    assert m['unknown_correctness'] == dict(value=2/3, numerator=2, denominator=3)
    assert m['latency_p50_ms']['value'] == 20
    assert m['latency_p95_ms']['value'] == 29
    assert {f['id'] for f in score['failures']} == {'a', 'b'}
    assert evaluation.score_intake([])['metrics']['water_accuracy']['value'] is None


def test_triage_scorer_requires_correct_target_and_hazard():
    rows = [
        dict(id='dup', expect=dict(link='C-03', newHazard=False),
             got=dict(links=[dict(caseId='C-03', newHazard=False)], position=1)),
        dict(id='wrong', expect=dict(link='C-02', newHazard=False),
             got=dict(links=[dict(caseId='C-03', newHazard=False)], position=2)),
        dict(id='hazard', expect=dict(link='C-08', newHazard=True), got=dict(links=[], position=0)),
        dict(id='inject', expect=dict(link=None, newHazard=False, notFirst=True), got=dict(links=[], position=3)),
    ]
    score = evaluation.score_triage(rows)
    assert score['metrics']['duplicate_link_precision']['value'] == .5
    assert score['metrics']['duplicate_link_recall']['value'] == .5
    assert score['metrics']['new_hazard_correctness']['value'] == 0
    assert score['metrics']['injection_correctness']['value'] == 1
    assert {f['id'] for f in score['failures']} == {'wrong', 'hazard'}


def test_standin_end_to_end_without_key_or_network(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Offline evaluation must not access a key or network')
    monkeypatch.setattr('api.intake.extract.api_key', forbidden)
    monkeypatch.setattr('api.ai.triage.api_key', forbidden)
    monkeypatch.setattr(evaluation, 'extract', forbidden)
    monkeypatch.setattr(evaluation, 'run_agent', forbidden)
    import socket
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    assert evaluation.main(['--mode', 'standin', '--triage', '--out', str(tmp_path)]) == 0
    result = json.loads((tmp_path / 'results.json').read_text())
    assert result['gemini'] is None and result['model_ids_seen'] == []
    assert result['n_intake'] == 36 and result['n_triage'] == 14
    assert result['standin']['runs'][0]['triage']['source'] == 'rules'
    assert result['standin']['summary']['operational']['fallback_rate']['mean'] == 0
    assert 'Gemini runs: not yet run' in (tmp_path / 'results.md').read_text()


def test_gemini_fallback_is_excluded_and_variation_is_reported(tmp_path, monkeypatch):
    def fake_extract(text):
        facts, dropped = evaluation.validate(text, evaluation.standin_extract(text))
        return dict(source='stand-in', facts=facts, dropped=dropped, note='must never appear in results')
    monkeypatch.setattr(evaluation, 'extract', fake_extract)
    monkeypatch.setattr(evaluation, 'run_agent', evaluation.rule_proposals)
    evaluation.main(['--mode', 'gemini', '--runs', '3', '--triage', '--out', str(tmp_path)])
    result = json.loads((tmp_path / 'results.json').read_text())
    g = result['gemini']
    assert len(g['runs']) == 3
    assert g['summary']['operational']['fallback_rate']['mean'] == 1
    assert g['summary']['model_only']['water_accuracy']['mean'] is None
    assert all(r['intake']['model_only']['n'] == 0 for r in g['runs'])
    assert g['summary']['triage']['fallback']['mean'] == 1
    assert g['summary']['triage']['model_only']['duplicate_link_recall']['mean'] is None
    assert 'must never appear' not in (tmp_path / 'results.json').read_text()
    summary = evaluation.summarize([{'metrics': {'x': {'value': .2}}}, {'metrics': {'x': {'value': .8}}}])
    assert summary['x'] == dict(mean=.5, min=.2, max=.8, runs=2)


@pytest.mark.parametrize('runs', ['0', '-1'])
def test_runs_must_be_positive(runs):
    with pytest.raises(SystemExit):
        evaluation.main(['--runs', runs])
