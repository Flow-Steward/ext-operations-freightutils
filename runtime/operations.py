"""Run one step: check the inputs, send one request, shape the answer."""

from __future__ import annotations

import sys
import traceback
from collections.abc import Mapping
from typing import Any

from . import answer, errors
from .catalog import STEPS
from .connection import connection_from_payload
from .errors import ExtensionError, error_response, invalid, ok
from .identity import EXTENSION_ID
from .inputs import build_request
from .transport import Opener, send

SUCCESS_RANGE = range(200, 300)
_ACTION_KEYS = frozenset(
    {"action_id", "operation_id", "page_id", "component_id", "context", "input", "target"}
)
ANONYMOUS_NOTE = (
    "No API key: FreightUtils answers 25 requests a day per address. A free key gives 100 a day"
)


def handle_runtime(payload: Mapping[str, Any], opener: Opener | None = None) -> dict[str, Any]:
    try:
        step_id, operation_input = _envelope(payload)
        step = STEPS.get(step_id)
        if step is None:
            raise ExtensionError(
                errors.UNSUPPORTED_OPERATION, "That operation is not part of this extension"
            )
        ref = operation_input.get("connection_ref")
        connection = connection_from_payload(payload, ref if isinstance(ref, str) else "")
        request = build_request(step, operation_input)
        response = send(connection, request, opener)
        if response.status not in SUCCESS_RANGE:
            raise answer.failure(response, connection)
        shaped = answer.result(response)
        if step_id == "test_connection" and connection.anonymous:
            shaped["warnings"] = [ANONYMOUS_NOTE, *shaped["warnings"]]
        return ok(shaped)
    except ExtensionError as exc:
        return error_response(exc.code, exc.message, exc.facts())
    except Exception as exc:
        where = _where(exc)
        # The type and place only, never the text, which could hold data or the key.
        print(f"{EXTENSION_ID} internal error: {where}", file=sys.stderr)
        return error_response(errors.INTERNAL_ERROR, f"The step could not be completed ({where})")


def _envelope(payload: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    if payload.get("mode") != "action":
        raise invalid("Request mode must be action")
    action = payload.get("action")
    if not isinstance(action, Mapping) or set(action) - _ACTION_KEYS:
        raise invalid("The action envelope is invalid")
    step_id = action.get("action_id") or action.get("operation_id")
    if not isinstance(step_id, str) or not step_id.strip():
        raise invalid("An operation id is required")
    raw = action.get("input")
    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping):
        raise invalid("The operation input must be an object")
    # The host sends a field left empty in the form as null or "".
    cleaned = {str(k): v for k, v in raw.items() if v is not None and v != ""}
    return step_id.strip(), cleaned


def _where(exc: BaseException) -> str:
    frames = traceback.extract_tb(exc.__traceback__)
    inside = [f for f in frames if "/runtime/" in f.filename.replace("\\", "/")] or frames
    if not inside:
        return type(exc).__name__
    frame = inside[-1]
    name = frame.filename.replace("\\", "/").rsplit("/", 1)[-1]
    return f"{type(exc).__name__} at {name}:{frame.lineno} in {frame.name}"
