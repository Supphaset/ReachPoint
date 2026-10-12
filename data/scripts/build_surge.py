"""Export reproducible synthetic intake and separate evaluation truth; no network or credentials.

Run from the repository root: python -m data.scripts.build_surge --output /tmp/reachpoint-surge
The processor must read intake.json only. truth.json is evaluation-only.
"""
import argparse
import json
from pathlib import Path

from data.surge import VERSION, generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    catalogue = json.loads((root / "contract/fixtures/areas.hy-2025-11.json").read_text())
    reports, truth = generate(catalogue, args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, rows in (("intake", reports), ("truth", truth)):
        target = args.output / f"{name}.json"
        target.write_text(json.dumps({"synthetic": True, "version": VERSION, "rows": rows}, ensure_ascii=False, indent=2) + "\n")
    print(f"Generated {len(reports)} synthetic reports; intake and evaluation truth are separate.")


if __name__ == "__main__":
    main()
