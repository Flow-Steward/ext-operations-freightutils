#!/usr/bin/env python3
"""Compare the live FreightUtils API description with the pinned snapshot.

    python3 scripts/check_upstream.py            report what changed (exit 1 when anything did)
    python3 scripts/check_upstream.py --update   also replace reference/openapi.json

Reading the description does not count against a FreightUtils allowance. After
``--update`` run ``python3 scripts/build_contracts.py``: it refuses a snapshot whose
operations ``scripts/steps.py`` does not name yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "reference" / "openapi.json"
URL = "https://www.freightutils.com/openapi.json"
TIMEOUT_SECONDS = 30
MAX_BYTES = 8 * 1024 * 1024


def _operations(spec: dict[str, Any]) -> dict[str, str]:
    """operationId -> the operation as canonical JSON, to see which ones changed."""
    found = {}
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if isinstance(op, dict) and "operationId" in op:
                found[op["operationId"]] = json.dumps(
                    {"path": path, "method": method, **op}, sort_keys=True
                )
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--update", action="store_true", help="replace the pinned snapshot")
    args = parser.parse_args()
    request = urllib.request.Request(URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as answer:  # nosec B310
        live_bytes = answer.read(MAX_BYTES + 1)
    if len(live_bytes) > MAX_BYTES:
        raise SystemExit("the live description is larger than expected; nothing was changed")
    pinned_bytes = SNAPSHOT.read_bytes()
    if hashlib.sha256(live_bytes).digest() == hashlib.sha256(pinned_bytes).digest():
        print("the pinned snapshot is current")
        return 0
    live, pinned = _operations(json.loads(live_bytes)), _operations(json.loads(pinned_bytes))
    for label, names in (
        ("added", sorted(set(live) - set(pinned))),
        ("removed", sorted(set(pinned) - set(live))),
        ("changed", sorted(n for n in set(live) & set(pinned) if live[n] != pinned[n])),
    ):
        print(f"{label}: {', '.join(names) or '-'}")
    if args.update:
        SNAPSHOT.write_bytes(live_bytes)
        print("reference/openapi.json replaced; run scripts/build_contracts.py")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
