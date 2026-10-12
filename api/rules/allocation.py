"""Split solver (C4). Owner: user. Pure: `solve_split(snapshot) -> suggestion`, no I/O, writes nothing.

The friend's API builds the snapshot from Firestore, calls this, and stores the suggestion; the coordinator's split
panel shows it and acts with direct asks ("Ask these teams"). Teams still take work themselves (pull model, 21A).

Model (design doc "Split solver", D33–D36; hand-run in api/notebooks/split-solver.ipynb):
- A resource can serve a need if it has the capability and access to the area; capacity is per help type.
- Boats and trucks count seat units, not heads (D33): adult 1, child under 12 half, baby on a lap 0, stretcher 3.
- A family goes whole by default. A split is suggested only when it fits more people, and no part that goes or waits
  has a child, a baby or a stretcher case without an adult (D34). Every split needs the coordinator's approval.
- Accepted allocations stay fixed; an unavailable resource's accepted jobs go back to the list.
- Lexicographic objective, solved level by level, each level fixed before the next:
    1a  people covered whose need has a qualified urgent medical requirement
    1b  other tier-1 people covered (coordinator urgent flag with a reason)
    2   tier-2 units covered, weighted w_evac (evacuation, medical) and w_supply (supplies); weights >= 0.1 (D35)
    -   fewest split families
    3   least waiting left uncovered, in person-minutes (D35)
- Tiers come from tiers.tier(), the same function that orders the team lists (C3), so they can't disagree (T15).
- Unassigned needs are a valid output, each with a reason: no_capable_team or capacity_exhausted.

The snapshot is the draft shape of contract/fixtures/allocationInput.cp3.json until contract v1.0.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from typing import Any, Iterable, Mapping

from ortools.sat.python import cp_model

from .tiers import Tier, TierInput, colour, tier

KINDS = ("adults", "children", "infants", "stretcher")
TYPE_WEIGHT = {"evacuation_transport": "w_evac", "medical": "w_evac", "supplies": "w_supply"}
MIN_WEIGHT = 0.1
TIME_LIMIT_S = 5.0  # per level; the demo snapshot solves in milliseconds
SOLVER_NAME = "OR-Tools CP-SAT"


class InvalidSnapshot(ValueError):
    """The snapshot can't be solved as given (bad weights, unknown IDs, accepted work over capacity)."""


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def suggestion_id(snapshot: Mapping[str, Any], options: Mapping[str, Any]) -> str:
    """Same input, same ID: lets the API spot a repeated request and a stale suggestion."""
    raw = json.dumps({"snapshot": snapshot, "options": options}, sort_keys=True, ensure_ascii=False, default=str)
    return "SUG-" + hashlib.sha1(raw.encode()).hexdigest()[:10]


def _needs(snapshot: Mapping[str, Any], half_seats: Mapping[str, int]) -> list[dict]:
    now = _parse(snapshot["snapshotAt"])
    out = []
    for doc in snapshot["needs"]:
        t = TierInput.from_listing(doc)
        party = doc.get("party")
        if party is not None:
            if set(party) != set(KINDS):
                raise InvalidSnapshot(f"{doc['listingId']}: party needs {KINDS}")
            if sum(party.values()) != doc["units"]:
                raise InvalidSnapshot(f"{doc['listingId']}: party adds up to {sum(party.values())}, units say {doc['units']}")
        out.append({
            "listingId": doc["listingId"], "caseId": doc.get("caseId"), "area": doc["areaId"],
            "type": doc["assistanceType"], "units": doc["units"], "unit": doc.get("unit", "people"), "party": party,
            "tier": tier(t), "colour": colour(t).value,
            "waiting_min": max(0, int((now - t.waiting_since).total_seconds() // 60)),
            "urgentReason": (doc.get("urgentFlag") or {}).get("reason"),
        })
    return out


def solve_split(snapshot: Mapping[str, Any], *, drop: Iterable[str] = (), extra: Iterable[Mapping[str, Any]] = (),
                weights: Mapping[str, float] | None = None, allow_splits: bool = True,
                time_limit_s: float = TIME_LIMIT_S) -> dict:
    """Suggest which resource covers which family (or safe part of one). Reads the snapshot; writes nothing."""
    drop, extra = set(drop), list(extra)
    w = {**snapshot["weights"], **(weights or {})}
    if min(w.values()) < MIN_WEIGHT:
        raise InvalidSnapshot(f"weights must be at least {MIN_WEIGHT}: {w}")
    seat = snapshot["seatUnits"]
    half_seats = {k: int(round(2 * seat[k])) for k in KINDS}
    resources = [r for r in snapshot["resources"] if r.get("available", True) and r["resourceId"] not in drop] + extra
    rids = [r["resourceId"] for r in resources]
    if len(set(rids)) != len(rids):
        raise InvalidSnapshot("duplicate resource IDs")
    needs = _needs(snapshot, half_seats)
    by_need = {n["listingId"]: n for n in needs}
    accepted = [a for a in snapshot.get("accepted", []) if a["resourceId"] in set(rids)]
    returned = [a for a in snapshot.get("accepted", []) if a["resourceId"] not in set(rids)]

    m = cp_model.CpModel()
    capable = {n["listingId"]: [r for r in resources if n["type"] in r["capabilities"] and n["area"] in r["areas"]]
               for n in needs}
    take: dict[tuple[str, str], dict[str, Any]] = {}
    used: dict[tuple[str, str], Any] = {}
    covered: dict[str, Any] = {}
    splits = []

    for n in needs:
        nid, rs = n["listingId"], capable[n["listingId"]]
        if n["party"]:
            P = n["party"]
            dependants = P["children"] + P["infants"] + P["stretcher"]
            for r in rs:
                k = (nid, r["resourceId"])
                take[k] = {kind: m.NewIntVar(0, P[kind], f"{kind}_{nid}_{r['resourceId']}") for kind in KINDS}
                used[k] = m.NewBoolVar(f"used_{nid}_{r['resourceId']}")
                part = sum(take[k].values())
                m.Add(part >= 1).OnlyEnforceIf(used[k])
                m.Add(part == 0).OnlyEnforceIf(used[k].Not())
                if P["adults"]:
                    # D34: a part that goes with children, a baby or a stretcher case has an adult in it ...
                    m.Add(take[k]["children"] + take[k]["infants"] + take[k]["stretcher"] <= dependants * take[k]["adults"])
            left = {kind: P[kind] - sum(take[nid, r["resourceId"]][kind] for r in rs) for kind in KINDS}
            for kind in KINDS:
                m.Add(left[kind] >= 0)
            if P["adults"]:
                # ... and so does the part that waits
                m.Add(left["children"] + left["infants"] + left["stretcher"] <= dependants * left["adults"])
            covered[nid] = n["units"] - sum(left.values())
            if rs:
                whole, none, split = (m.NewBoolVar(f"{x}_{nid}") for x in ("whole", "none", "split"))
                m.Add(covered[nid] == n["units"]).OnlyEnforceIf(whole)
                m.Add(sum(used[nid, r["resourceId"]] for r in rs) <= 1).OnlyEnforceIf(whole)
                m.Add(covered[nid] == 0).OnlyEnforceIf(none)
                m.AddBoolOr([whole, none, split])
                if not allow_splits or not P["adults"]:
                    m.Add(split == 0)  # a group with no adult (e.g. children found alone) always moves whole
                splits.append(split)
        else:  # medical visits and supply runs: whole or not at all
            for r in rs:
                used[nid, r["resourceId"]] = m.NewBoolVar(f"x_{nid}_{r['resourceId']}")
            covered[nid] = n["units"] * sum(used[nid, r["resourceId"]] for r in rs) if rs else 0
            if rs:
                m.Add(sum(used[nid, r["resourceId"]] for r in rs) <= 1)

    for a in accepted:
        n = by_need.get(a["listingId"])
        k = (a["listingId"], a["resourceId"])
        if n is None or k not in used:
            raise InvalidSnapshot(f"accepted allocation {a.get('allocationId')} doesn't match a capable need/resource")
        if n["party"]:
            for kind in KINDS:  # accepted whole family (a partial claim arrives as its own listing groups)
                m.Add(take[k][kind] == n["party"][kind])
        else:
            m.Add(used[k] == 1)

    for r in resources:
        rid = r["resourceId"]
        for typ, cap in r["capacity"].items():
            if typ == "evacuation_transport":
                load = sum(sum(half_seats[kind] * v for kind, v in take[k].items()) for k in take if k[1] == rid)
                m.Add(load <= int(round(2 * cap)))
            else:
                m.Add(sum(n["units"] * used[n["listingId"], rid] for n in needs
                          if (n["listingId"], rid) in used and n["type"] == typ) <= cap)

    def people(t: Tier):
        return sum(covered[n["listingId"]] for n in needs if n["tier"] == t)

    levels = [
        ("tier1aPeopleCovered", people(Tier.T1A), "max"),
        ("tier1bPeopleCovered", people(Tier.T1B), "max"),
        ("tier2WeightedUnitsX100", sum(int(round(100 * w[TYPE_WEIGHT[n["type"]]])) * covered[n["listingId"]]
                                       for n in needs if n["tier"] == Tier.T2), "max"),
        ("splitFamilies", sum(splits), "min"),
        ("personMinutesWaiting", sum(n["waiting_min"] * (n["units"] - covered[n["listingId"]]) for n in needs), "min"),
    ]
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1  # deterministic: same answer every run
    solver.parameters.max_time_in_seconds = time_limit_s
    values, optimal = {}, True
    for name, expr, sense in levels:
        (m.Maximize if sense == "max" else m.Minimize)(expr)
        status = solver.Solve(m)
        if status == cp_model.INFEASIBLE:
            raise InvalidSnapshot("no valid split: accepted work exceeds a resource's capacity")
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise InvalidSnapshot(f"solver stopped without an answer at level {name}")
        optimal = optimal and status == cp_model.OPTIMAL
        values[name] = int(round(solver.ObjectiveValue()))
        m.Add(expr >= values[name]) if sense == "max" else m.Add(expr <= values[name])

    by_rid = {r["resourceId"]: r for r in resources}
    acc = {(a["listingId"], a["resourceId"]) for a in accepted}
    assignments, unassigned = [], []
    for n in needs:
        nid, got = n["listingId"], 0
        base = {"listingId": nid, "caseId": n["caseId"], "assistanceType": n["type"], "areaId": n["area"],
                "tier": n["tier"].value, "colour": n["colour"], "unit": n["unit"]}
        for r in capable[nid]:
            k = (nid, r["resourceId"])
            if not solver.Value(used[k]):
                continue
            part = {kind: solver.Value(v) for kind, v in take[k].items()} if k in take else None
            units = sum(part.values()) if part else n["units"]
            got += units
            assignments.append({**base, "resourceId": r["resourceId"], "teamId": r["teamId"], "units": units, "part": part,
                                "seatUnits": sum(part[x] * half_seats[x] for x in KINDS) / 2 if part else None,
                                "accepted": k in acc})
        if got < n["units"]:
            left = ({kind: n["party"][kind] - sum(a["part"][kind] for a in assignments if a["listingId"] == nid)
                     for kind in KINDS} if n["party"] else None)
            unassigned.append({**base, "units": n["units"] - got, "part": left,
                               "reason": "capacity_exhausted" if capable[nid] else "no_capable_team",
                               "capableResources": [r["resourceId"] for r in capable[nid]],
                               "returnedFrom": next((a["resourceId"] for a in returned if a["listingId"] == nid), None)})
    rows = Counter(a["listingId"] for a in assignments)
    split_ids = {i for i, c in rows.items() if c > 1} | {u["listingId"] for u in unassigned if u["listingId"] in rows}
    for row in assignments + unassigned:
        row["split"] = row["listingId"] in split_ids
        row["needsCoordinatorApproval"] = row["split"]  # D34

    usage = []
    for r in resources:
        load = {}
        for typ in r["capacity"]:
            if typ == "evacuation_transport":
                load[typ] = sum(a["seatUnits"] or 0 for a in assignments if a["resourceId"] == r["resourceId"] and a["assistanceType"] == typ)
            else:
                load[typ] = sum(a["units"] for a in assignments if a["resourceId"] == r["resourceId"] and a["assistanceType"] == typ)
        usage.append({"resourceId": r["resourceId"], "teamId": r["teamId"], "capacity": r["capacity"], "used": load,
                      "simulated": bool(r.get("simulated"))})

    options = {"drop": sorted(drop), "extra": extra, "weights": w, "allowSplits": allow_splits}
    return {
        "suggestionId": suggestion_id(snapshot, options),
        "inputVersions": snapshot["inputVersions"],
        "snapshotAt": snapshot["snapshotAt"],
        "simulation": bool(drop or extra or weights),
        "solver": {"name": SOLVER_NAME, "optimal": optimal, "levels": values},
        "weights": w,
        "assignments": assignments,
        "unassigned": unassigned,
        "resources": usage,
        "explanations": explain(needs, assignments, unassigned, by_rid),
    }


TIER_REASON = {
    "1a": "Tier 1a: qualified review requires urgent medical help",
    "1b": "Tier 1b: coordinator flagged urgent",
    "2": "Tier 2",
}
REASON_TEXT = {
    "capacity_exhausted": "capable teams are full today",
    "no_capable_team": "no available team can do this here",
}


def explain(needs, assignments, unassigned, by_rid) -> list[dict]:
    """Per-need facts for the Gemini explanation (C8). Only computed facts; Gemini may not add numbers or routes."""
    out = []
    for n in needs:
        nid = n["listingId"]
        facts = [TIER_REASON[n["tier"].value] + (f" ({n['urgentReason']})" if n["tier"] == Tier.T1B and n["urgentReason"] else "")]
        for a in (x for x in assignments if x["listingId"] == nid):
            r = by_rid[a["resourceId"]]
            facts.append(f"{a['units']} {a['unit']} to {a['resourceId']} ({a['teamId']}, {r.get('kind', 'resource')})"
                         + (" · already accepted" if a["accepted"] else "")
                         + (" · split: coordinator approves" if a["split"] else ""))
        for u in (x for x in unassigned if x["listingId"] == nid):
            facts.append(f"{u['units']} {u['unit']} not covered: {REASON_TEXT[u['reason']]}"
                         + (f" (back from {u['returnedFrom']}, unavailable)" if u["returnedFrom"] else ""))
        if n["waiting_min"]:
            facts.append(f"waiting {n['waiting_min']} min")
        out.append({"listingId": nid, "facts": facts})
    return out


def compare_scenarios(snapshot: Mapping[str, Any], *, extra: Iterable[Mapping[str, Any]] = (), drop: Iterable[str] = (),
                      weights: Mapping[str, float] | None = None) -> dict:
    """What-if for the split panel. The extra resources are labelled as a simulation, never real teams."""
    extra = [{**r, "simulated": True} for r in extra]
    base = solve_split(snapshot)
    what_if = solve_split(snapshot, extra=extra, drop=drop, weights=weights)

    def covered(s):
        c = Counter()
        for a in s["assignments"]:
            c[a["listingId"]] += a["units"]
        return c

    b, wi = covered(base), covered(what_if)
    ids = sorted(set(b) | set(wi))
    return {
        "label": "Simulation: not a real team or a real change until the coordinator acts",
        "base": base,
        "whatIf": what_if,
        "diff": {
            "peopleCoveredDelta": sum(wi[i] for i in ids if base_unit(snapshot, i) == "people")
                                  - sum(b[i] for i in ids if base_unit(snapshot, i) == "people"),
            "moreCovered": [i for i in ids if wi[i] > b[i]],
            "lessCovered": [i for i in ids if wi[i] < b[i]],
        },
    }


def base_unit(snapshot: Mapping[str, Any], listing_id: str) -> str:
    return next(n.get("unit", "people") for n in snapshot["needs"] if n["listingId"] == listing_id)
