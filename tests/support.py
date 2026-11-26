"""A fake FreightUtils that answers with the recorded live answers, and payload helpers.

``fixtures/live`` holds real answers of www.freightutils.com (2026-11-26, without a key):
the body as received and the headers this extension reads.
"""

from __future__ import annotations

import io
import json
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from runtime.operations import handle_runtime

BUNDLE = Path(__file__).resolve().parents[1]
LIVE = BUNDLE / "tests" / "fixtures" / "live"
API_KEY = "fu_fixture_key_0123456789abcdef"  # pragma: allowlist secret


def connection(key: str | None = None) -> dict[str, Any]:
    secrets = {"api_key": key} if key is not None else {}
    return {
        "connection_id": "conn-1",
        "connection_type_id": "freightutils",
        "config": {"label": "Freight desk"},
        "secrets": secrets,
    }


def payload(step: str, step_input: dict[str, Any] | None = None, *, key: str | None = None):
    return {
        "mode": "action",
        "contract_version": "extension_host_v2",
        "runtime_context": {
            "test_mode": False,
            "group_id": None,
            "for_each_id": None,
            "step_id": "step-1",
            "step_execution_id": "exec-1",
        },
        "action": {
            "action_id": step,
            "input": {"connection_ref": "conn-1", **(step_input or {})},
            "target": {"connection": connection(key)},
        },
    }


def live(name: str) -> tuple[int, dict[str, str], bytes]:
    """A recorded answer: status, headers and body."""
    lines = (LIVE / f"{name}.headers").read_text(encoding="utf-8").splitlines()
    status = int(lines[0].split()[1])
    headers = dict(line.split(": ", 1) for line in lines[1:] if ": " in line)
    return status, headers, (LIVE / f"{name}.json").read_bytes()


class Sent:
    """What the extension sent."""

    def __init__(self, request: Any, timeout: float) -> None:
        parts = urlsplit(request.full_url)
        self.url = request.full_url
        self.host = parts.hostname
        self.path = parts.path
        self.query = parse_qsl(parts.query, keep_blank_values=True)
        self.method = request.get_method()
        self.headers = {k.lower(): v for k, v in request.header_items()}
        self.body = json.loads(request.data) if request.data else None
        self.timeout = timeout


class _Answer(io.BytesIO):
    def __init__(self, status: int, headers: dict[str, str], body: bytes) -> None:
        super().__init__(body)
        self.status = status
        self.headers = Message()
        for key, value in headers.items():
            self.headers[key] = value


class FakeFreightUtils:
    """Answers each request with the next queued answer and records what was sent."""

    def __init__(self, *answers: tuple[int, dict[str, str], bytes]) -> None:
        self.answers = list(answers)
        self.sent: list[Sent] = []

    def __call__(self, request: Any, timeout: float) -> _Answer:
        self.sent.append(Sent(request, timeout))
        status, headers, body = self.answers.pop(0)
        if status >= 400:
            message = Message()
            for key, value in headers.items():
                message[key] = value
            raise urllib.error.HTTPError(
                request.full_url, status, "refused", message, io.BytesIO(body)
            )
        return _Answer(status, headers, body)


def answer(status: int, body: Any, **headers: str) -> tuple[int, dict[str, str], bytes]:
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    return status, {"content-type": "application/json", **headers}, raw


def run(step: str, step_input: dict[str, Any] | None = None, *answers, key: str | None = None):
    fake = FakeFreightUtils(*answers)
    response = handle_runtime(payload(step, step_input, key=key), opener=fake)
    return response, fake
