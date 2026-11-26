#!/usr/bin/env python3
"""FreightUtils subprocess entrypoint: one JSON request on stdin, one JSON answer out."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from typing import Any

from dispatcher import dispatch_runtime
from runtime import errors
from runtime.errors import error_response

MAX_INPUT_BYTES = 2 * 1024 * 1024
#: The host's step output limit, with room for the envelope.
MAX_OUTPUT_BYTES = 4 * 1024 * 1024 + 256 * 1024
#: Numbers with more digits than this are refused before they are used.
MAX_NUMBER_DIGITS = 40


class _Refused(ValueError):
    pass


def _decimal(text: str) -> Decimal:
    if len(text) > MAX_NUMBER_DIGITS:
        raise _Refused(f"The request has a number longer than {MAX_NUMBER_DIGITS} characters")
    return Decimal(text)


def _integer(text: str) -> int:
    if len(text) > MAX_NUMBER_DIGITS:
        raise _Refused(f"The request has a number longer than {MAX_NUMBER_DIGITS} characters")
    return int(text)


def _constant(text: str) -> Any:
    raise _Refused(f"The request has {text}, which is not a JSON number")


def _load(raw: bytes) -> dict[str, Any]:
    text = raw.decode("utf-8")
    payload = (
        json.loads(text, parse_float=_decimal, parse_int=_integer, parse_constant=_constant)
        if text.strip()
        else {}
    )
    return payload if isinstance(payload, dict) else {}


def _default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(type(value).__name__)


def _serialized(response: dict[str, Any]) -> bytes:
    return json.dumps(
        response, default=_default, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def main() -> int:
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        response = error_response(errors.INVALID_PAYLOAD, "The request exceeds its safe limit")
    else:
        try:
            response = dispatch_runtime(_load(raw))
        except _Refused as exc:
            response = error_response(errors.INVALID_PAYLOAD, str(exc))
        except (UnicodeDecodeError, ValueError, RecursionError):
            response = error_response(errors.INVALID_PAYLOAD, "The request is not valid JSON")
    serialized = _serialized(response)
    if len(serialized) > MAX_OUTPUT_BYTES:
        response = error_response(
            errors.RESPONSE_TOO_LARGE,
            "The answer is too large for a step output; ask for fewer rows",
        )
        serialized = _serialized(response)
    sys.stdout.buffer.write(serialized + b"\n")
    return 0 if response.get("ok") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
