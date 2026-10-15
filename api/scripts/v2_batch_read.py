"""Gemini reads every scenario message once (the Reader agent in batch), and the facts are cached for the board.

    python api/scripts/v2_batch_read.py [--workers 8]

Writes data/hy-2025-11/v2-facts.json: per message, the facts Gemini returned that passed the quote rule, and the
model. Messages Gemini could not read keep the rule reader (and say so). Bulletins are read by the rules.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.v2 import ai  # noqa: E402
from api.v2.pipeline import PKG, scenario  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    msgs = [m for m in scenario()["messages"] if m["channel"] != "bulletin"]
    out_path = PKG / "v2-facts.json"
    done = json.loads(out_path.read_text())["facts"] if out_path.exists() else {}
    todo = [m for m in msgs if not str(done.get(m["id"], {}).get("reader", "")).startswith("gemini")]
    print(len(msgs), "messages;", len(todo), "to read", flush=True)

    def one(m):
        r = ai.read(m["text"], m["channel"], timeout=20, models=2)
        return m["id"], {"reader": r.reader, "facts": [asdict(f) for f in r.facts]}

    t0 = time.time()
    with ThreadPoolExecutor(args.workers) as pool:
        for i, (mid, res) in enumerate(pool.map(one, todo), 1):
            done[mid] = res
            if i % 50 == 0:
                out_path.write_text(json.dumps({"package": "hy-2025-11", "facts": done}, ensure_ascii=False))
                print(i, "read", round(time.time() - t0), "s", flush=True)
    out_path.write_text(json.dumps({"package": "hy-2025-11", "facts": done}, ensure_ascii=False))
    g = sum(1 for v in done.values() if v["reader"].startswith("gemini"))
    print("done:", g, "by Gemini,", len(done) - g, "by rules")


if __name__ == "__main__":
    main()
