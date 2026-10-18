"""Vehicle-constrained model routes. Guidance for ground checks, never a safe-route claim."""
from __future__ import annotations

import json
import heapq
import math
from functools import lru_cache

from api.v2 import geo as G, pipeline as P, shelters as H, sim as S
from api.v2.names import english_name

SPEED = {"boat": 5, "truck": 12, "foot": 3}


def vehicle_name(value):
    return {"high truck": "truck", "on foot": "foot"}.get(value, value) if value else "boat"


@lru_cache(maxsize=12)
def model(now_h, vehicle):
    nodes, edges = H._streets()
    return [S.depth(*G.to_ll(*p), now_h) or 0.0 for p in nodes]


@lru_cache(maxsize=1)
def main_nodes():
    nodes, _ = H._streets()
    lookup = {(round(x), round(y)): i for i, (x, y) in enumerate(nodes)}
    out = set()
    p = G.PKG / "v2-streets.geojson"
    if p.exists():
        for f in json.loads(p.read_text())["features"]:
            if f["properties"].get("kind") not in {"primary", "secondary", "tertiary", "trunk"}:
                continue
            g = f["geometry"]
            for line in (g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]):
                for lo, la in line:
                    x, y = G.to_m(lo, la)
                    i = lookup.get((round(x), round(y)))
                    if i is not None:
                        out.add(i)
    return out


def street_name(lon, lat):
    geo = G.load()
    building = geo.snap(lon, lat)
    facing = geo.facing(building) if building else None
    return english_name(facing.street or facing.street_th) if facing and (facing.street or facing.street_th) else "street"


def two_opt(order, distance, start, end):
    """Improve an open run with fixed endpoints; accept only strictly shorter tours."""
    order = list(order)
    def cost(xs):
        seq = [start, *xs, end]
        return sum(distance(a, b) for a, b in zip(seq, seq[1:]))
    best = cost(order)
    changed = True
    while changed:
        changed = False
        for i in range(len(order)):
            for j in range(i + 1, len(order)):
                trial = order[:i] + order[i:j + 1][::-1] + order[j + 1:]
                c = cost(trial)
                if c + 0.001 < best:
                    order, best, changed = trial, c, True
    return order


class Network:
    def __init__(self, w, vehicle):
        self.w, self.vehicle = w, vehicle
        self.nodes, self.edges = H._streets()
        self.depths = model(w.now_h, vehicle)
        self.corrected = {}
        self.edge_info = {}
        self.trees = {}
        self.components = {}

    def depth(self, lon, lat):
        key = (round(lon, 8), round(lat, 8))
        if not hasattr(self, "sample_cache"):
            self.sample_cache = {}
        if key not in self.sample_cache:
            self.sample_cache[key] = P.local_depth(self.w, lon, lat, self.w.now_h)[0]
        return self.sample_cache[key]

    def wet(self, i):
        if i not in self.corrected:
            self.corrected[i] = self.depth(*G.to_ll(*self.nodes[i])) if getattr(self.w, "assim_index", None) is not None else self.depths[i]
        return self.corrected[i]

    def allowed(self, d):
        return self.vehicle == "boat" or d <= (H.WALK_M if self.vehicle == "foot" else 1.0)

    def segment(self, a, b):
        key = tuple(sorted((a, b)))
        if key not in self.edge_info:
            p, q = self.nodes[a], self.nodes[b]
            n = max(1, math.ceil(math.dist(p, q) / H.STEP_M))
            lookup = (lambda lo, la: S.depth(lo, la, self.w.now_h) or 0.0) if self.vehicle == "boat" else self.depth
            ds = [lookup(*G.to_ll(p[0] + (q[0]-p[0])*k/n, p[1] + (q[1]-p[1])*k/n)) for k in range(n + 1)]
            self.edge_info[key] = (max(ds), sum(d < .4 for d in ds) / len(ds))
        return self.edge_info[key]

    def search(self, a, b):
        key = (a, b)
        if key in self.trees:
            return self.trees[key]
        component = self.components.get(a)
        if component is not None and b not in component:
            return math.inf, None
        best, prev = {a: 0.0}, {}
        todo = [(math.dist(self.nodes[a], self.nodes[b]), 0.0, a)]
        while todo:
            _, c, i = heapq.heappop(todo)
            if c > best[i]:
                continue
            if i == b:
                out = [b]
                while out[-1] != a:
                    out.append(prev[out[-1]])
                result = (c, [G.to_ll(*self.nodes[j]) for j in reversed(out)])
                self.trees[key] = result
                self.trees[(b, a)] = (c, result[1][::-1])
                return result
            for j, meters in self.edges.get(i, []):
                if self.vehicle != "boat" and not self.allowed(self.wet(j)):
                    continue
                deepest, dry = self.segment(i, j)
                if not self.allowed(deepest):
                    continue
                nc = c + meters * (1 + 15 * dry if self.vehicle == "boat" else 1)
                if nc < best.get(j, math.inf):
                    best[j], prev[j] = nc, i
                    heapq.heappush(todo, (nc + math.dist(self.nodes[j], self.nodes[b]), nc, j))
        component = set(best)
        for i in component:
            self.components[i] = component
        self.trees[key] = (math.inf, None)
        return self.trees[key]

    def path(self, a, b):
        return self.search(a, b)[1]


def _samples(net, line):
    out, meters, carry = [], 0.0, 0.0
    for a, b in zip(line, line[1:]):
        p, q = G.to_m(*a), G.to_m(*b)
        length = math.dist(p, q)
        n = max(1, math.ceil(length / H.STEP_M))
        for k in range(n):
            lo, la = G.to_ll(p[0] + (q[0]-p[0])*k/n, p[1] + (q[1]-p[1])*k/n)
            d = net.depth(lo, la)
            out.append([round(lo, 6), round(la, 6), round(d, 2)])
            if d < .4:
                carry += length/n
        meters += length
    lo, la = line[-1]
    out.append([round(lo, 6), round(la, 6), round(net.depth(lo, la), 2)])
    return out, meters, carry


def route(w, rows, plan=None, vehicle=None, seats=None, center=None):
    plan = plan or {}
    vehicle = vehicle_name(vehicle or plan.get("vehicle"))
    if vehicle not in SPEED:
        vehicle = "boat"
    seats = seats or plan.get("seats") or 4
    if not hasattr(w, "_route_networks"):
        w._route_networks = {}
    key = (w.now_h, vehicle, id(getattr(w, "assim_index", None)))
    if key not in w._route_networks:
        w._route_networks[key] = Network(w, vehicle)
    net = w._route_networks[key]
    warnings, unreachable = [], []
    waiting = [r for r in rows if r["status"] not in {"safe", "evacuated", "atShelter", "nobodyThere"}]
    located = [r for r in waiting if r.get("lon") is not None and r.get("lat") is not None]
    center = center or ((located[0]["lon"], located[0]["lat"]) if located else (100.47, 7.01))
    target = G.to_m(*center)
    dry = [i for i in net.edges if net.depths[i] < .1]
    # A launch is the first wet street vertex adjacent to the exterior dry network.
    exterior = set()
    approach = {}
    if dry:
        west = min(dry, key=lambda i: net.nodes[i][0]); east = max(dry, key=lambda i: net.nodes[i][0])
        south = min(dry, key=lambda i: net.nodes[i][1]); north = max(dry, key=lambda i: net.nodes[i][1])
        todo = [west, east, south, north]
        approach.update({i: None for i in todo})
        while todo:
            i = todo.pop()
            if i in exterior:
                continue
            exterior.add(i)
            for j, _ in net.edges[i]:
                if j not in exterior and j not in approach and net.depths[j] < .4:
                    approach[j] = i
                    todo.append(j)
    launches = [i for i in net.edges if net.depths[i] >= .4 and any(j in exterior for j, _ in net.edges[i])]
    choices = launches if vehicle == "boat" else [i for i in dry if i in exterior and i in main_nodes()]
    if not choices:
        choices = dry or list(net.edges)
        warnings.append("No verified launch or dry approach on the street graph; check on the ground")
    choices.sort(key=lambda i: math.dist(target, net.nodes[i]))
    # Model candidates are cheap to enumerate; verify the selected approach against room reports.
    def valid_start(i):
        if vehicle != "boat":
            if net.wet(i) >= .1:
                return False
            k = i
            while k is not None and net.allowed(net.wet(k)):
                k = approach.get(k)
            return k is None
        if net.wet(i) < .4:
            return False
        for j, _ in net.edges[i]:
            if j not in exterior:
                continue
            k = j
            while k is not None and net.wet(k) < .4:
                k = approach.get(k)
            if k is None:
                return True
        return False
    start_i = next((i for i in choices if valid_start(i)), None)
    verified_start = start_i is not None
    if start_i is None:
        start_i = choices[0] if choices else None
        warnings.append("No verified launch or dry approach on the street graph; check on the ground")
    start_ll = G.to_ll(*net.nodes[start_i]) if start_i is not None else center
    start = {"lon": start_ll[0], "lat": start_ll[1], "label": ("Launch here" if verified_start else "Launch unverified") if vehicle == "boat" else "Start"}
    points = {"start": (start_ll, start_i)}
    valid = []
    for r in waiting:
        reason = None
        if r not in located:
            reason = "House coordinates unavailable"
        else:
            ll = (r["lon"], r["lat"])
            d = net.depth(*ll)
            i = H._nearest(*G.to_m(*ll))
            if not net.allowed(d) or (i is not None and not net.allowed(net.wet(i))):
                reason = f"{max(d, net.wet(i) if i is not None else d):.1f} m on {street_name(*ll)} at {r['id']}: a {vehicle} can't pass — this house needs a boat"
            elif (r.get("people") or 1) > seats:
                reason = f"{r['id']}: household exceeds {seats} seats; arrange more capacity"
            else:
                points[r["id"]] = (ll, i)
                valid.append(r)
        if reason:
            unreachable.append({"id": r["id"], "reason": reason, "reasonTh": f"{r['id']}: เข้าถึงไม่ได้ด้วยพาหนะนี้ โปรดตรวจสอบระดับน้ำและจำนวนที่นั่ง"})
            warnings.append(reason)
    posted = plan.get("order")
    by_id = {r["id"]: r for r in valid}
    if posted is not None:
        ordered = [by_id[i] for i in dict.fromkeys(posted) if i in by_id]
    else:
        ordered = sorted(valid, key=lambda r: (-r.get("priority", 0), -r.get("urgent", False), -r.get("cannotWalk", 0), r["id"]))
    groups, group, load = [], [], 0
    for r in ordered:
        people = r.get("people") or 1
        if r.get("people") is None:
            warnings.append(f"{r['id']}: household size unknown; confirm capacity before departure")
        if group and load + people > seats:
            groups.append(group); group, load = [], 0
        group.append(r["id"]); load += people
    if group:
        groups.append(group)

    def distance(a, b):
        pa, ia = points[a]
        if b == "shelter":
            candidate, ib = choose_drop(a)
            pb = (candidate["lon"], candidate["lat"]) if candidate else start_ll
            ib = ib if candidate else start_i
        else:
            pb, ib = points[b]
        if ia is not None and ib is not None:
            _, path = net.search(ia, ib)
            if path is None:
                return math.dist(G.to_m(*pa), G.to_m(*pb)) * 20
            return sum(math.dist(G.to_m(*a), G.to_m(*b)) for a, b in zip([pa, *path], [*path, pb]))
        return math.dist(G.to_m(*pa), G.to_m(*pb)) * 20

    blocked = []

    def leg(a, b):
        pa, ia = points[a]; pb, ib = points[b]
        path = net.path(ia, ib) if ia is not None and ib is not None else None
        notes = []
        if path is None:
            path = [pa, pb]
            notes.append("direct line, check on the ground")
        else:
            path = [pa, *path, pb]
        path = [p for i, p in enumerate(path) if i == 0 or p != path[i-1]]
        if len(path) == 1:
            path = [path[0], path[0]]
        samples, meters, carry = _samples(net, path)
        deepest = max(s[2] for s in samples)
        if not net.allowed(deepest):
            blocked.append(max(samples, key=lambda s: s[2]))
            return None
        if vehicle == "boat" and carry >= 1:
            dry_sample = next(s for s in samples if s[2] < .4)
            notes.append(f"dry {round(carry)} m on {street_name(*dry_sample[:2])}: carry the boat {round(carry)} m")
        # Keep the original geometry in the samples; cap display geometry without losing endpoints.
        path = [path[round(k * (len(path)-1)/119)] for k in range(120)] if len(path) > 120 else path
        return {"from": a, "to": b, "path": [[round(lo, 6), round(la, 6)] for lo, la in path],
                "km": round(meters/1000, 3), "minutes": round(meters/1000/SPEED[vehicle]*60, 1),
                "deepestM": deepest, "samples": samples, "warnings": notes,
                "warningAt": dry_sample[:2] if vehicle == "boat" and carry >= 1 else max(samples, key=lambda s: s[2])[:2]}

    drops = {}

    def choose_drop(hid):
        if hid in drops:
            return drops[hid]
        last = points[hid][0]
        shelter = None
        shelter_i = None
        for s in sorted(H.load(), key=lambda s: math.dist(G.to_m(s["lon"], s["lat"]), G.to_m(*last))):
            p = G.to_m(s["lon"], s["lat"])
            near = [i for i in dry if math.dist(net.nodes[i], p) <= H.SNAP_M]
            near.sort(key=lambda i: math.dist(net.nodes[i], p))
            for i in near:
                if net.wet(i) >= .1:
                    continue
                src = points[hid][1]
                if src is not None and net.path(src, i) is not None:
                    shelter, shelter_i = s, i
                    break
            if shelter:
                break
        if shelter:
            ll = G.to_ll(*net.nodes[shelter_i])
            drop = {k: shelter.get(k) for k in ("id", "name", "nameEn")}
            drop.update(lon=ll[0], lat=ll[1])
        else:
            drop = None
        drops[hid] = drop, shelter_i
        return drops[hid]

    runs = []
    for ids in groups:
        if posted is None:
            remaining, ordered_ids, current = ids[:], [], "start"
            while remaining:
                nxt = min(remaining, key=lambda i: distance(current, i))
                ordered_ids.append(nxt); remaining.remove(nxt); current = nxt
            ids = two_opt(ordered_ids, distance, "start", "start" if vehicle == "boat" else "shelter")
        drop, shelter_i = choose_drop(ids[-1])
        if drop is None:
            warnings.append("No reachable dry shelter drop-off; arrange a handover on the ground")
        points["shelter"] = ((drop["lon"], drop["lat"]), shelter_i) if drop else (start_ll, start_i)
        legs, reached, current = [], [], "start"
        for hid in ids:
            item = leg(current, hid)
            if item is None:
                lo, la, deepest = blocked[-1]
                reason = f"{deepest:.1f} m on {street_name(lo, la)} at {hid}: a {vehicle} can't pass — this house needs a boat"
                unreachable.append({"id": hid, "reason": reason, "reasonTh": f"{hid}: น้ำบนทางเข้าลึกเกินขีดจำกัด ต้องใช้เรือ"}); warnings.append(reason)
                continue
            legs.append(item); reached.append(hid); current = hid
        if not reached:
            continue
        # A boat hands people over at the launch point, where a truck takes them on to the shelter; trucks and
        # walkers take them to the shelter themselves.
        back = [(current, "start")] if vehicle == "boat" or not drop else [(current, "shelter"), ("shelter", "start")]
        for a, b in back:
            item = leg(a, b)
            if item:
                legs.append(item)
            else:
                warnings.append("Drop-off or return exceeds vehicle depth limit; check on the ground")
        totals = {"km": round(sum(l["km"] for l in legs), 3), "minutes": round(sum(l["minutes"] for l in legs), 1)}
        runs.append({"run": len(runs)+1, "stops": reached, "start": start, "shelter": drop, "legs": legs, "totals": totals,
                     "handover": vehicle == "boat"})
        warnings.extend(n for l in legs for n in l["warnings"])
    return {"vehicle": vehicle, "seats": seats, "start": start, "runs": runs, "unreachable": unreachable,
            "totals": {k: round(sum(r["totals"][k] for r in runs), 2) for k in ("km", "minutes")},
            "perRun": {"runs": len(runs), "km": round(max((r["totals"]["km"] for r in runs), default=0), 1),
                       "minutes": round(max((r["totals"]["minutes"] for r in runs), default=0))},
            "deepestM": max((l["deepestM"] for r in runs for l in r["legs"]), default=0),
            "warnings": list(dict.fromkeys(warnings)), "now": {"atH": w.now_h, "at": P.label_time(w.now_h)}}
