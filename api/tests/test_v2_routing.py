"""Deterministic small street fixtures plus a real ten-house performance check."""
from types import SimpleNamespace
from time import perf_counter

import pytest

from api.v2 import routing as R


@pytest.fixture
def streets(monkeypatch):
    # Dry exterior -> shallow launch -> deep house, with a dry shelter beside the exterior.
    nodes = [(0., 0.), (40., 0.), (80., 0.), (120., 0.)]
    edges = {0: [(1, 40)], 1: [(0, 40), (2, 40)], 2: [(1, 40), (3, 40)], 3: [(2, 40)]}
    depths = [0., .4, .5, 1.4]
    monkeypatch.setattr(R.H, '_streets', lambda: (nodes, edges))
    monkeypatch.setattr(R.H, '_nearest', lambda x, y: min(range(4), key=lambda i: abs(nodes[i][0]-x)))
    monkeypatch.setattr(R, 'main_nodes', lambda: {0})
    def depth(lo, la, h):
        x, _ = R.G.to_m(lo, la)
        return depths[min(3, max(0, round(x/40)))]
    monkeypatch.setattr(R.S, 'depth', depth)
    monkeypatch.setattr(R.P, 'local_depth', lambda w, lo, la, h: (depth(lo, la, h), 0, 0, 0))
    lo, la = R.G.to_ll(0, 0)
    monkeypatch.setattr(R.H, 'load', lambda: [{'id': 'S', 'name': 'Shelter', 'nameEn': 'Shelter', 'lon': lo, 'lat': la}])
    R.model.cache_clear()
    yield nodes, edges, depths
    R.model.cache_clear()


def row(i, priority=1):
    lo, la = R.G.to_ll(i*40, 0)
    return dict(id=f'H{i}', lon=lo, lat=la, status='open', people=1, priority=priority)


def test_foot_never_crosses_deep_water(streets):
    out = R.route(SimpleNamespace(now_h=96), [row(2), row(3)], vehicle='foot')
    assert [h['id'] for h in out['unreachable']] == ['H3']
    assert all(s[2] <= .5 for r in out['runs'] for l in r['legs'] for s in l['samples'])
    assert out['runs'] and all(len(l['path']) <= 120 for r in out['runs'] for l in r['legs'])


def test_truck_deep_house_is_unreachable(streets):
    out = R.route(SimpleNamespace(now_h=96), [row(3)], vehicle='truck')
    assert out['unreachable'][0]['id'] == 'H3'
    assert any("1.4 m" in w and 'needs a boat' in w for w in out['warnings'])
    assert not out['runs']


def test_boat_launch_and_posted_order(streets):
    out = R.route(SimpleNamespace(now_h=96), [row(2), row(3)], {'order': ['fake', 'H3', 'H2', 'H3'], 'seats': 4}, vehicle='boat')
    assert out['start']['label'] == 'Launch here'
    assert R.S.depth(out['start']['lon'], out['start']['lat'], 96) >= .4
    assert out['runs'][0]['stops'] == ['H3', 'H2']
    assert out['runs'][0]['shelter']['id'] == 'S'
    assert out['runs'][0]['legs'][-1]['to'] == 'start'
    assert any('carry the boat' in w for w in out['warnings'])


def test_two_opt_does_not_lengthen():
    pts = {'s': (0, 0), 'a': (10, 10), 'b': (0, 10), 'c': (10, 0), 'e': (20, 0)}
    import math
    d = lambda a, b: math.dist(pts[a], pts[b])
    def cost(xs):
        seq = ['s', *xs, 'e']
        return sum(d(a, b) for a, b in zip(seq, seq[1:]))
    order = ['a', 'b', 'c']
    assert cost(R.two_opt(order, d, 's', 'e')) < cost(order)


def test_disconnected_falls_back(streets):
    _, edges, depths = streets
    edges[1] = [(0, 40)]; edges[2] = [(3, 40)]; depths[3] = .5
    out = R.route(SimpleNamespace(now_h=96), [row(2)], vehicle='foot')
    assert out['runs']
    assert 'direct line, check on the ground' in out['runs'][0]['legs'][0]['warnings']


def test_real_ten_house_routing_under_five_seconds():
    from api.v2 import board, cases
    st = board.state(96)
    rows = cases._rows(st, 'D12')[:9]
    from api.v2 import geo
    coordinates = {(r['lon'], r['lat']) for r in rows}
    building = next(b for b in geo.load().buildings.values() if b.zone_id == 'D12' and (b.lon, b.lat) not in coordinates)
    rows.append({**rows[0], 'id': 'SYNTHETIC-TENTH', 'lon': building.lon, 'lat': building.lat})
    assert len(rows) == 10
    t = perf_counter()
    out = R.route(st['world'], rows, vehicle='boat', seats=8, center=cases.zone_point('D12'))
    seconds = perf_counter() - t
    print(f'10-house boat routing: {seconds:.3f}s')
    assert seconds < 5
    assert out['runs']


def test_b5_report_route_endpoint_and_overrides():
    from fastapi.testclient import TestClient
    from uuid import uuid4
    from api.main import app
    from api.v2 import geo, limits
    client = TestClient(app)
    headers = {'X-Demo-Room': 'pytest-route-' + uuid4().hex[:12]}
    b = max((b for b in geo.load().buildings.values() if b.zone_id == 'B5'), key=lambda b: R.S.depth(b.lon, b.lat, 96) or 0)
    created = client.post('/api/v2/chat/sessions?lang=en', headers=headers)
    headers['X-Demo-Room'] = created.headers['X-Demo-Room']
    sid = created.json()['id']
    report = client.post(f'/api/v2/chat/sessions/{sid}/turn', headers=headers, json={
        'text': 'Water at my waist. We are 2 people. My mother cannot walk. Please help.',
        'pin': {'lon': b.lon, 'lat': b.lat, 'method': 'map'}})
    assert report.status_code == 200
    zone = client.get('/api/v2/v/zones/B5', headers=headers).json()
    ids = [h['id'] for h in zone['households'] if h['status'] not in {'safe', 'evacuated', 'atShelter', 'nobodyThere'}]
    assert ids
    posted = client.post('/api/v2/plans', headers=headers, json={
        'text': 'Routing demo boat 6 seats zone B5 around 12:00', 'team': 'Routing demo', 'zone': 'B5', 'order': ids})
    assert posted.status_code == 200, posted.text
    boat = client.get('/api/v2/v/mission/B5/route', headers=headers)
    assert boat.status_code == 200
    boat = boat.json()
    assert boat['vehicle'] == 'boat' and boat['seats'] == 6
    assert boat['runs'] and boat['start']['label'] == 'Launch here'
    assert [hid for run in boat['runs'] for hid in run['stops']] == ids
    mission = client.get('/api/v2/v/zones/B5?team=Routing%20demo', headers=headers).json()
    assert mission['route']['totals'] == boat['totals']
    truck = client.get('/api/v2/v/mission/B5/route?vehicle=truck&seats=8', headers=headers).json()
    assert truck['vehicle'] == 'truck' and truck['seats'] == 8
    assert truck['unreachable'] and any('boat' in w for w in truck['warnings'])
    assert client.get('/api/v2/v/mission/B5/route?vehicle=plane', headers=headers).status_code == 422
    assert client.get('/api/v2/v/mission/B5/route?seats=0', headers=headers).status_code == 422
    assert client.get('/api/v2/v/mission/nope/route', headers=headers).status_code == 404
    assert not limits.http_limit('GET', '/api/v2/v/mission/B5/route', uuid4().hex, 'room', {})


def test_shallow_house_behind_deep_barrier_is_unreachable(streets):
    _, _, depths = streets
    depths[1] = 1.4; depths[3] = .1
    out = R.route(SimpleNamespace(now_h=96), [row(3)], vehicle='truck')
    assert not out['runs']
    assert out['unreachable'][0]['id'] == 'H3'
    assert any('needs a boat' in w for w in out['warnings'])


def test_cache_keeps_room_report_corrections_separate(streets, monkeypatch):
    def local(w, lo, la, h):
        x, _ = R.G.to_m(lo, la)
        return (1.4 if w.flooded and x > 60 else 0, 0, 0, 0)
    monkeypatch.setattr(R.P, 'local_depth', local)
    dry = R.route(SimpleNamespace(now_h=96, flooded=False, assim_index=object()), [row(2)], vehicle='truck')
    wet = R.route(SimpleNamespace(now_h=96, flooded=True, assim_index=object()), [row(2)], vehicle='truck')
    assert dry['runs'] and not dry['unreachable']
    assert not wet['runs'] and wet['unreachable']


def test_shelter_is_nearest_to_final_stop_after_optimization(streets, monkeypatch):
    _, _, depths = streets
    depths[3] = 0
    shelters = []
    for i in [0, 3]:
        lo, la = R.G.to_ll(i*40, 0)
        shelters.append({'id': f'S{i}', 'name': f'Shelter {i}', 'nameEn': f'Shelter {i}', 'lon': lo, 'lat': la})
    monkeypatch.setattr(R.H, 'load', lambda: shelters)
    out = R.route(SimpleNamespace(now_h=96), [row(2, priority=10), row(1)], vehicle='boat', seats=4, center=R.G.to_ll(0, 0))
    assert out['runs'][0]['stops'] == ['H1', 'H2']
    assert out['runs'][0]['shelter']['id'] == 'S3'


def test_boat_prefers_wet_streets_over_short_dry_cut(streets, monkeypatch):
    nodes = [(0, 0), (40, 0), (80, 0), (0, 40), (80, 40)]
    edges = {0: [(1, 40), (3, 40)], 1: [(0, 40), (2, 40)], 2: [(1, 40), (4, 40)], 3: [(0, 40), (4, 80)], 4: [(3, 80), (2, 40)]}
    monkeypatch.setattr(R.H, '_streets', lambda: (nodes, edges))
    def depth(lo, la, h):
        x, y = R.G.to_m(lo, la)
        return 0 if abs(x-40) < 20 and abs(y) < 20 else .5
    monkeypatch.setattr(R.S, 'depth', depth)
    R.model.cache_clear()
    path = R.Network(SimpleNamespace(now_h=96), 'boat').path(0, 2)
    assert R.G.to_ll(0, 40) in path
    assert R.G.to_ll(40, 0) not in path
