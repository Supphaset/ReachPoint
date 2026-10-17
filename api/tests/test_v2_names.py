"""Display-name regressions: preserve Thai evidence and cover the entire demo package."""
import re

from api.v2 import geo, intake, shelters
from api.v2.names import bilingual, english_name, romanise


def test_rtgs_street_numbers_and_intake_aliases():
    assert romanise('ถนนเพชรเกษม ซอย 2') == 'Thanon Phetkasem Soi 2'
    assert romanise('ถนนละม้ายสงเคราะห์') == 'Thanon Lamai Songkhro'
    assert romanise('ซอย สุภาพ ๒') == 'Soi Suphap 2'
    assert intake.thai_streets('Phetkasem Soi 2') == 'ถนนเพชรเกษม ซอย 2'


def test_osm_english_and_explicit_shelter_names_take_precedence(monkeypatch):
    monkeypatch.setattr('api.v2.names.osm_english', lambda: {'ถนนเพชรเกษม': 'Phet Kasem Road'})
    assert english_name('ถนนเพชรเกษม') == 'Phet Kasem Road'
    assert english_name('ถนนเพชรเกษม', 'Official English') == 'Official English'


def test_every_bundled_named_street_zone_sector_block_and_shelter_has_english():
    g = geo.load()
    rows = g.streets + [f['properties'] for f in g.zones + g.sectors + g.blocks] + shelters.load()
    for row in rows:
        if row.get('name'):
            assert english_name(row['name'], row.get('nameEn'))
            assert not re.search('[\u0e00-\u0e7f]', english_name(row['name'], row.get('nameEn'))), row['name']
    assert all(s['nameEn'] for s in shelters.load())


def test_api_views_keep_both_names_without_rewriting_evidence():
    original = {'label': 'ถนนเพชรเกษม ซอย 2', 'sector': 'B', 'story': [{'text': 'ถนนเพชรเกษม', 'quote': 'แม่เดินไม่ได้'}]}
    out = bilingual(original)
    assert out['label'] == original['label']
    assert out['labelEn'] == out['nameEn'] == 'Thanon Phetkasem Soi 2'
    assert out['story'] == original['story']
    assert 'nameEn' not in original


def test_geo_and_locator_return_both_languages():
    from api.v2.routes import geo_view
    view = geo_view()
    assert all(f['properties']['nameEn'] for f in view['zones']['features'])
    assert all(f['properties']['nameEn'] for f in view['sectors']['features'])
    located = intake.locate('52/9 Phetkasem Soi 2', geo.load())
    assert located and located['labelEn'] == 'Thanon Phetkasem Soi 2'


def test_volunteer_views_and_copilot_supply_english_names():
    from api.v2 import board, cases, copilot
    state = board.state(96)
    overview = cases.overview(state)
    assert all(z['labelEn'] and z['nameEn'] for z in overview['zones'])
    assert all(s['nameEn'] for s in overview['sectors'])
    assert all(z['labelEn'] for z in cases.urgent(state, {})['zones'])
    assert cases.zone(state, 'D12')['zone']['labelEn'] == 'Thanon Lamai Songkhro'
    assert copilot.get_zone(state, 'D12')['labelEn'] == 'Thanon Lamai Songkhro'


def test_shelter_followup_uses_the_session_language(monkeypatch):
    from api.v2 import followup
    option = {'name': 'วัดคลองแห', 'nameEn': 'Wat Khlong Hae', 'walkable': True,
              'km': 1, 'minutes': 20, 'deepestM': 0.1, 'lat': 7, 'lon': 100}
    monkeypatch.setattr(followup.SH, 'options', lambda *args: [option])
    for lang, expected in [('en', 'Wat Khlong Hae'), ('th', 'วัดคลองแห')]:
        s = intake.new_session(lang)
        s.pin = {'lon': 100, 'lat': 7}
        answer = followup.answer(None, s, None, 'I can walk', 'evacWalk', lang)
        assert expected in answer['reply']
        if lang == 'en':
            assert not re.search('[\u0e00-\u0e7f]', answer['reply'])
