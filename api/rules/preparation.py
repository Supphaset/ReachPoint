"""Compact preparation excerpts without adding or rewriting reported facts."""

from __future__ import annotations

import re


def compact_preparation_notes(text: str | None) -> str | None:
    lines = []
    keys = []
    for raw in (text or "").splitlines():
        line = re.sub(r"^Caller reports:\s*", "", raw.strip(), flags=re.IGNORECASE).strip()
        key = re.sub(r"\s+", "", line).casefold()
        if key and key not in keys:
            lines.append(line)
            keys.append(key)
    # Keep the full-context excerpt when a shorter line repeats part of it.
    return "\n".join(line for i, line in enumerate(lines)
                     if not any(keys[i] in other for j, other in enumerate(keys) if i != j)) or None
