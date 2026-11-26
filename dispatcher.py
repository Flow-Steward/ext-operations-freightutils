"""Closed dispatcher: only the steps of ``runtime/registry.json`` are routed."""

from __future__ import annotations

from typing import Any

from flowsteward_extension_sdk import runtime_context_from_payload

from runtime import errors
from runtime.catalog import OPERATION_IDS
from runtime.errors import error_response
from runtime.operations import handle_runtime


def dispatch_runtime(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        runtime_context_from_payload(payload)
    except ValueError as exc:
        return error_response(errors.INVALID_HOST_ENVELOPE, str(exc))
    action = payload.get("action")
    step_id = ""
    if payload.get("mode") == "action" and isinstance(action, dict):
        value = action.get("action_id") or action.get("operation_id")
        step_id = value.strip() if isinstance(value, str) else ""
    if step_id not in OPERATION_IDS:
        return error_response(
            errors.UNSUPPORTED_OPERATION, "That operation is not part of this extension"
        )
    return handle_runtime(payload)
