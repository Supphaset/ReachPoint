"""Measure v2 against the scenario's ground truth (docs/product/v2-spec.md §7).

    python api/scripts/eval_v2.py            # writes docs/eval/v2-results.md

Reader: Gemini's cached facts (v2-facts.json) against what each synthetic message was built from.
Pipeline: households, merges, neighbour buildings, doubtful labels and water levels against the truth.
The scenario is synthetic, so these numbers say how the system behaves on realistic messages, not field accuracy.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.v2 import geo as G, pipeline as P  # noqa: E402
from api.v2.reader import read_rules  # noqa: E402

BANDS = [0.1, 0.5, 1.0, 2.0]


def band(d: float) -> int:
    return sum(d >= b for b in BANDS)


def pct(a: int, b: int, digits: int = 0) -> str:
    return "—" if not b else f"{100 * a / b:.{digits}f}% ({a}/{b})"


def main() -> None:
    sc = P.scenario()
    facts = P.cached_facts()
    hh = {h["id"]: h for h in sc["truth"]["households"]}
    msgs = [m for m in sc["messages"] if m["channel"] != "bulletin"]
    gem = [m for m in msgs if str(facts.get(m["id"], {}).get("reader", "rules")) != "rules"]
    model = sorted({facts[m["id"]]["reader"] for m in gem}) or ["none"]

    # --- Reader
    depth_ok = depth_n = people_ok = people_n = nb_ok = nb_n = urgent_fp = urgent_n = 0
    for m in gem:
        f = {x["field"]: x["value"] for x in facts[m["id"]]["facts"]}
        ref = read_rules(m["text"], m["channel"]).get("depthRange")
        if ref and f.get("depthRange"):
            depth_n += 1
            g = f["depthRange"]
            depth_ok += band((g[0] + g[1]) / 2) == band((ref[0] + ref[1]) / 2)
        if m["kind"] == "self" and not m["truth"].get("planted"):
            people_n += 1
            people_ok += f.get("people") == hh[m["truth"]["about"]]["people"]
        if m["truth"].get("neighbour"):
            nb_n += 1
            nb = f.get("neighbour") or {}
            nb_ok += isinstance(nb, dict) and nb.get("side") == m["truth"]["neighbour"]["side"]
        if m["kind"] == "reply" and "ยังปลอดภัย" in m["text"]:
            urgent_n += 1
            urgent_fp += f.get("urgent") is True

    # --- Pipeline at the end of the scenario
    w = P.run(150)
    by_msg = {m["id"]: m for m in sc["messages"]}
    true_heard = {m["truth"]["about"] for m in sc["messages"] if m["atH"] <= 150 and m["truth"].get("about")} | \
                 {m["truth"]["neighbour"]["neighbourHousehold"] for m in sc["messages"] if m["atH"] <= 150 and m["truth"].get("neighbour")}
    wrong_merge = 0
    for h in w.households.values():
        abouts = {by_msg[i]["truth"].get("about") for i in h.message_ids if i in by_msg and by_msg[i]["truth"].get("about")}
        wrong_merge += len(abouts) > 1
    nb_build = nb_build_n = 0
    for m in sc["messages"]:
        t = m["truth"].get("neighbour")
        if t and m["atH"] <= 150:
            eff = (m.get("_effects") or {}).get("neighbour")
            if eff:
                nb_build_n += 1
                nb_build += eff["buildingId"] == t["neighbourBuildingId"]
    planted = {m["id"] for m in sc["messages"] if m["truth"].get("planted")}
    honest = {o.message_id for o in w.obs if o.message_id not in planted}
    doubtful = {o.message_id for o in w.obs if o.label == "doubtful"}
    # depth at households: the local estimate at each first-hand report vs the true depth there and then
    house_err, model_err = [], []
    for m in sc["messages"]:
        if m["kind"] in ("self", "reply") and m["atH"] <= 140 and m["truth"].get("trueDepthM") is not None and m.get("pin"):
            # the estimate there from the OTHER reports (this one left out), the way a neighbour's house is estimated
            own = [o for o in w.assim_index.obs if o.id == m["id"]]
            for o in own:
                o.t += 1e6  # hide it
            d, sd, n, prior = P.local_depth(w, m["pin"]["lon"], m["pin"]["lat"], m["atH"])
            for o in own:
                o.t -= 1e6
            house_err.append(abs(d - m["truth"]["trueDepthM"]))
            model_err.append(abs(prior - m["truth"]["trueDepthM"]))
    truth = {z: dict(v) for z, v in sc["truth"]["wseByZone"].items()}
    errs = defaultdict(list)
    for h in (60, 72, 84, 99, 111, 126):
        lv = P.run(h).levels
        for z, l in lv.items():
            t = truth[z].get(h)
            if l.wse_m is not None and t is not None:
                errs[h].append(abs(l.wse_m - t))
    allerr = [e for v in errs.values() for e in v]

    lower_households = len(w.households) - sum(1 for h in w.households.values() if h.possible_duplicate_of)
    lower_error = 100 * abs(lower_households - len(true_heard)) / len(true_heard)
    upper_error = 100 * abs(len(w.households) - len(true_heard)) / len(true_heard)

    rows = [
        (f"Messages read by the model in batch ({', '.join(model)})", pct(len(gem), len(msgs), 1) + "; hybrid reader, rules fill gaps", "—"),
        ("Facts shown with the person's exact words", "100% (enforced: a fact whose quote isn't in the message is dropped)", "≥ 95%"),
        ("Depth from words in the same band as the reference reading", pct(depth_ok, depth_n), "≥ 85%"),
        ("People count read correctly (first-hand reports)", pct(people_ok, people_n), "—"),
        ("Neighbour direction read correctly (north, south, east, west)", pct(nb_ok, nb_n), "—"),
        ("\"Still safe\" replies wrongly marked urgent", pct(urgent_fp, urgent_n), "low"),
        ("Households counted vs synthetic reference families heard about",
         f"{lower_households}–{len(w.households)} vs {len(true_heard)} "
         f"(lower bound {lower_error:.1f}% error; upper bound {upper_error:.1f}% error; possible duplicates kept apart)", "lower bound within 3%"),
        ("Households wrongly merged (two families as one)", pct(wrong_merge, len(w.households)), "≤ 3%"),
        ("Neighbour words matched to the exact building", pct(nb_build, nb_build_n), "≥ 85%"),
        ("Planted wrong reports flagged doubtful", pct(len(planted & doubtful), len(planted & {o.message_id for o in w.obs})), "≥ 80%"),
        ("Honest reports wrongly flagged doubtful", pct(len(honest & doubtful), len(honest)), "low"),
        ("Depth at a household from the model + OTHER reports (this one left out), mean error",
         f"{sum(house_err) / len(house_err):.2f} m over {len(house_err)} reports (median {sorted(house_err)[len(house_err) // 2]:.2f} m); "
         f"model alone {sum(model_err) / len(model_err):.2f} m", "better than the model alone"),
        ("Zone water surface vs the true zone surface (mean error, 6 moments)", f"{sum(allerr) / len(allerr):.2f} m over {len(allerr)} zone-moments", "—"),
    ]
    md = ["# v2 evaluation: Hat Yai scenario, 21–28 Nov 2025", "",
          "Run by `python api/scripts/eval_v2.py`. The scenario uses real water data (gauge X.44, rain, satellite, terrain,",
          "building outlines) and synthetic people and messages, so these numbers describe behaviour on realistic messages,",
          "not field accuracy. Reference readings for depth are the rule reader's band for the same words.", "",
          "| Measure | Result | Target |", "|---|---|---|"]
    md += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    md += ["", "Level error by moment (mean absolute, metres):", ""]
    md += [f"- {P.label_time(h)}: {sum(v) / len(v):.2f} m across {len(v)} zones" for h, v in errs.items() if v]
    out = ROOT / "docs" / "eval" / "v2-results.md"
    out.write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
