"""The records a view is built from. Owner: user (shape), friend (Firestore storage).

`Store` is one snapshot: the demo seed (or the same documents read from Firestore), plus the area package
(geography, estimates) and the vulnerable-residents register. Firestore layout the friend's API reads into it:

    cases/{caseId}                 one household or place; `needs` holds its listings (one per assistance type)
    reports/{reportId}             not yet reviewed (counted in badges, never in demand)
    waterReports/{id}              a caller's or team's water band at a segment (D26, D32)
    segmentMarks/{segmentId}       Checked / Partly checked / Couldn't reach (D17b)
    teams/{teamId}                 status, capabilities, landmark, resource (seats)
    register/{entryId}             coordinator-only (D19); views read counts only
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Store:
    seed: dict[str, Any]
    catalogue: dict[str, Any]  # contract/fixtures/areas.<package>.json
    exposure: dict[str, Any]  # data/<package>/exposure.json, raw counts per segment
    register: dict[str, Any] = field(default_factory=lambda: {"entries": []})

    @property
    def cases(self) -> list[dict]:
        return self.seed["cases"]

    def needs(self, type_: str | None = None):
        """(case, need) pairs, optionally of one assistance type."""
        return [(c, n) for c in self.cases for n in c["needs"] if type_ in (None, n["type"])]

    def team(self, team_id: str) -> dict | None:
        return next((t for t in self.seed["teams"] if t["teamId"] == team_id), None)

    @property
    def landmarks(self) -> dict[str, dict]:
        return {l["id"]: l for l in self.catalogue["landmarks"]}


def load(package: str = "hy-2025-11", root: Path = ROOT, seed: dict | None = None) -> Store:
    """The demo store from the repo files. The API passes `seed` built from Firestore instead."""
    fx = root / "contract" / "fixtures"
    return Store(
        seed=seed if seed is not None else json.loads((root / "contract" / "seed" / f"demo.{package}.json").read_text()),
        catalogue=json.loads((fx / f"areas.{package}.json").read_text()),
        exposure=json.loads((root / "data" / package / "exposure.json").read_text()),
        register=json.loads((fx / f"register.{package}.json").read_text()),
    )
