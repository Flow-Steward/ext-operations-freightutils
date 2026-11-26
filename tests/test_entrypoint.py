"""main.py and health.py as the host runs them: a subprocess, JSON in and out."""

from __future__ import annotations

import json
import subprocess
import sys

from support import BUNDLE, payload


def invoke(request: bytes) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, "main.py"],
        cwd=BUNDLE,
        input=request,
        capture_output=True,
        timeout=60,
        check=False,
    )
    return proc.returncode, json.loads(proc.stdout)


def test_an_unknown_operation_is_refused():
    code, response = invoke(json.dumps(payload("drop_everything")).encode())
    assert code == 2 and response["error_code"] == "unsupported_operation"


def test_a_request_that_is_not_json_is_refused():
    code, response = invoke(b"{not json")
    assert code == 2 and response["error_code"] == "invalid_payload"


def test_a_number_too_long_to_use_is_refused():
    request = json.dumps(payload("calculate_cbm", {"l": 1, "w": 1, "h": 1}))
    request = request.replace('"l": 1', '"l": 1' + "0" * 60)
    code, response = invoke(request.encode())
    assert code == 2 and "longer than" in response["error"]


def test_an_input_error_is_answered_without_network():
    code, response = invoke(json.dumps(payload("calculate_cbm", {"l": 1})).encode())
    assert code == 2 and response["error_code"] == "invalid_payload"


def test_health_reports_the_steps_without_network():
    proc = subprocess.run(
        [sys.executable, "health.py"], cwd=BUNDLE, capture_output=True, text=True, check=True
    )
    health = json.loads(proc.stdout)
    assert health["status"] == "healthy" and health["steps"] == 46
    assert health["api_operations"] == 40
