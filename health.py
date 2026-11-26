"""Health command (no network): the steps and the pinned API description load."""

from __future__ import annotations

import json


def check_health() -> dict[str, object]:
    from runtime.catalog import OPERATION_IDS, REGISTRY
    from runtime.identity import EXTENSION_ID

    return {
        "extension_id": EXTENSION_ID,
        "ok": True,
        "status": "healthy",
        "steps": len(OPERATION_IDS),
        "api_operations": REGISTRY["source"]["operations"],
        "api_description_sha256": REGISTRY["source"]["sha256"],
    }


if __name__ == "__main__":
    print(json.dumps(check_health(), separators=(",", ":"), sort_keys=True))
