"""Zone briefing text (T7, C8): 2–3 plain sentences for a team leader, written by Gemini from computed facts only.

The validator is the contract: the text is shown only if every number in it is one of the input facts, next to
words of the fact it counts, it makes no
route, safety, dryness or priority claim, and it is short. Otherwise the zone shows "Briefing unavailable" and the
facts, which are complete on their own. Teams never see AI text that adds a number.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from api.intake.extract import ENDPOINT, MODELS, api_key

MAX_CHARS, MAX_SENTENCES = 420, 3
THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
FORBIDDEN = [
    (r"\b(route|routes|road|roads|street is|streets are|via|detour|path|way in|access is)\b", "route claim"),
    (r"\b(safe|safely|unsafe|passable|impassable|clear(ed)? to|dry|drained)\b", "safety or dryness claim"),
    (r"\b(priority|prioriti[sz]e|most urgent|urgent first|go first|first to|should|must|recommend|need to go|send (a|the|more))\b", "priority or instruction"),
    (r"\b(dead|died|deaths|missing persons?|trapped people)\b", "claim not in the facts"),
]
INSTRUCTIONS = """You write a short briefing about one flood zone for a volunteer rescue team leader in Hat Yai.
Rules:
- 2 or 3 short sentences, plain English, under 60 words. Start with what reviewed calls say, then what is unknown.
- Use only the facts given. Copy numbers exactly as given; never add, round, total or compare numbers.
- Say clearly what is unknown (for example segments not yet checked).
- Call an estimate an estimate, and the depth model a model, not a measurement.
- Never mention routes, roads, safety, dryness or what anyone should do, and never rank or prioritise.
Return only the sentences."""


def zone_facts(zone: dict) -> dict:
    """The facts a briefing may use, from a zone of the area briefing view."""
    f = {x["key"]: x["value"] for x in zone["facts"]}
    segs = zone["segments"]
    est = zone["estimate"].get("notYetChecked") or [0, 0]
    out = {
        "zone": zone["zoneId"],
        "people reported needing evacuation (reviewed calls)": f.get("reviewedEvacuation"),
        "reviewed cases": f.get("cases"),
        "urgent needs (red)": zone["badge"]["urgent"],
        "reports not yet reviewed": zone["badge"]["unreviewed"],
        "water reported by callers": [f"{w['bandLabel']} at {w['landmarkLabel']}" + (" (report older than 6 h)" if w["stale"] else "")
                                      for w in zone.get("callerWater", [])],
        "segments not yet checked": f"{f.get('segmentsNotChecked')} of {len(segs)}",
        "segments partly checked": sum(s["check"]["state"] == "partly_checked" for s in segs),
        "segments a team couldn't reach": [s["label"] for s in segs if s["check"]["state"] == "could_not_reach"],
        "people living in segments not yet checked (estimate, not people needing help)": f"{est[0]:,}–{est[1]:,}",
        "cited flood reports from news or officials": f.get("reportedFloodingPoints"),
    }
    if zone.get("depth"):
        lo, hi = zone["depth"]["modelledM"]
        out["water depth from the city model (a model, not measured)"] = f"about {lo:g} m" if lo == hi else f"{lo:g}–{hi:g} m"
    return out


def facts_key(facts: dict) -> str:
    return hashlib.sha1(json.dumps(facts, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _numbers_in_facts(obj: Any, acc: set[float]) -> set[float]:
    if isinstance(obj, bool):
        return acc
    if isinstance(obj, (int, float)):
        acc.add(float(obj))
    elif isinstance(obj, str):
        for n in re.findall(r"\d+(?:\.\d+)?", obj.replace(",", "")):
            acc.add(float(n))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers_in_facts(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _numbers_in_facts(v, acc)
    return acc


_STOP = {"about", "from", "with", "that", "this", "than", "have", "been", "only", "more", "there", "their", "they",
         "were", "also", "some", "zone", "estimated", "estimate", "report", "reports", "reported", "callers", "calls",
         "reviewed", "review"}  # in many labels, so they can't tell one count from another


def _stems(s: str) -> set[str]:
    return {w[:4] for w in re.findall(r"[a-z]+", s.lower()) if len(w) >= 4 and w not in _STOP}


def _number_labels(facts: dict) -> dict[float, list[set[str]]]:
    """For each number in the facts, the words of the fact it belongs to (its key, and any words in its value)."""
    out: dict[float, list[set[str]]] = {}
    for key, value in facts.items():
        words = _stems(key) | _stems(json.dumps(value, ensure_ascii=False))
        for n in _numbers_in_facts(value, set()):
            out.setdefault(n, []).append(words)
    return out


def _wrong_label(t: str, start: int, end: int, labels: list[set[str]]) -> bool:
    """A number must sit next to words of a fact that has that number: "2 reviewed evacuation requests" is blocked
    when 2 is only the count of unchecked segments. Looks 3 words back and 5 forward, within the clause."""
    before = re.split(r"[;,.:]", t[:start])[-1].split()[-3:]
    after = re.split(r"[;,.:]", t[end:])[0].split()[:5]
    near = _stems(" ".join(before + after))
    return bool(near) and not any(near & words for words in labels)


def validate(text: str, facts: dict) -> list[str]:
    """Problems that block the text; empty means it can be shown."""
    problems = []
    t = (text or "").strip()
    if not t:
        return ["empty"]
    if len(t) > MAX_CHARS:
        problems.append("too long")
    if len([s for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]) > MAX_SENTENCES:
        problems.append("too many sentences")
    facts_text = json.dumps(facts, ensure_ascii=False)
    place = r"\b[ABC]-\d{1,2}(?:\s*·\s*L\d\b(?:\s+[A-Z][a-z]+(?:\s[a-z]+)?)?)?"
    for ref in re.findall(place, t):
        if re.sub(r"\s+", " ", ref) not in facts_text:  # a zone or landmark the facts don't name (e.g. L1 for L2)
            problems.append(f"place '{ref}' is not in the facts")
    for code in re.findall(r"\bL\d\b", re.sub(place, " ", t)):
        problems.append(f"landmark code '{code}' without its zone")
    allowed = _numbers_in_facts(facts, set())
    scrubbed = re.sub(r"\b[ABC]-\d{1,2}\b|\bL\d\b|\b6\s?h(ours)?\b", " ", t.translate(THAI_DIGITS))  # IDs and the 6 h label
    labels = _number_labels(facts)
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", scrubbed):
        n = m.group()
        v = float(n.replace(",", ""))
        if v not in allowed:
            problems.append(f"number {n} is not in the facts")
        elif _wrong_label(scrubbed, m.start(), m.end(), labels.get(v, [])):
            problems.append(f"number {n} is not what the facts say it counts")
    for word in ("two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "dozen", "hundred", "thousand", "million"):
        if re.search(rf"\b{word}\b", t, re.I):  # numbers must be digits so they can be checked against the facts
            problems.append(f"number word '{word}'")
    for pat, why in FORBIDDEN:
        if re.search(pat, t, re.I):
            problems.append(why)
    return problems


def write(facts: dict, timeout: float = 12.0) -> dict:
    """Ask Gemini, then validate. Returns the briefing field for the zone view."""
    import httpx
    key = api_key()
    if not key:
        return {"state": "unavailable", "text": None, "reason": "no_ai_key"}
    last = "model_unavailable"
    for model in MODELS:
        try:
            body = {"systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
                    "contents": [{"role": "user", "parts": [{"text": "Facts (JSON):\n" + json.dumps(facts, ensure_ascii=False)}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200}}
            r = httpx.post(ENDPOINT.format(model=model), headers={"x-goog-api-key": key}, json=body, timeout=timeout)
            if r.status_code != 200:
                last = f"http_{r.status_code}"
                continue
            text = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"]).strip()
        except Exception as e:  # network or bad response: try the next model
            last = type(e).__name__
            continue
        problems = validate(text, facts)
        if not problems:
            return {"state": "ready", "text": text, "source": f"gemini:{model}", "factsKey": facts_key(facts)}
        last = "validator_blocked: " + "; ".join(problems[:3])
    return {"state": "unavailable", "text": None, "reason": last}
