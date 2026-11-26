"""The closed list of steps, read from ``registry.json``.

``registry.json`` is written by ``scripts/build_contracts.py`` from the pinned OpenAPI
description; ``tests/test_contracts.py`` keeps it in step with the snapshot.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_FILE = Path(__file__).with_name("registry.json")
REGISTRY: dict[str, Any] = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
STEPS: dict[str, dict[str, Any]] = REGISTRY["steps"]
OPERATION_IDS: frozenset[str] = frozenset(STEPS)
