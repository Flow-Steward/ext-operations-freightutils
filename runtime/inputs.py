"""Check a step's inputs against the registry and turn them into one request.

Every input is checked before anything is sent: no unknown input, every required one
present, each of its type, inside its documented bounds and, for a list of choices, one
of them. FreightUtils ignores an unknown query parameter rather than refusing it, so a
mistyped input would otherwise be dropped silently.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import quote, urlencode

from .errors import invalid

#: A text input without a documented length is still bounded.
MAX_TEXT_LENGTH = 10_000
#: A JSON body (lines, items, a consignment) is bounded before it is sent.
MAX_BODY_BYTES = 512 * 1024
HOST_INPUTS = frozenset({"connection_ref"})
#: Path segments a server would read as a move to another address.
DOT_SEGMENTS = frozenset({"", ".", ".."})


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    query: str
    body: bytes | None


def _number(name: str, value: Any, *, integer: bool) -> int | Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise invalid(f"{name} must be a {'whole number' if integer else 'number'}")
    number = Decimal(str(value)) if isinstance(value, float) else value
    if isinstance(number, Decimal) and not number.is_finite():
        raise invalid(f"{name} must be a finite number")
    if integer and isinstance(number, Decimal):
        if number != number.to_integral_value():
            raise invalid(f"{name} must be a whole number")
        number = int(number)
    return number


def _checked(name: str, kind: str, value: Any, rules: Mapping[str, Any]) -> Any:
    match kind:
        case "text":
            if not isinstance(value, str):
                raise invalid(f"{name} must be text")
            value = value.strip()
            limit = rules.get("maxLength", MAX_TEXT_LENGTH)
            if len(value) > limit:
                raise invalid(f"{name} is longer than {limit} characters")
            if len(value) < rules.get("minLength", 0):
                raise invalid(f"{name} is shorter than {rules['minLength']} characters")
            if "pattern" in rules and not re.search(rules["pattern"], value):
                raise invalid(f"{name} does not have the documented form")
        case "number" | "integer":
            value = _number(name, value, integer=kind == "integer")
            _bounds(name, value, rules)
        case "boolean":
            if not isinstance(value, bool):
                raise invalid(f"{name} must be true or false")
        case "object":
            if not isinstance(value, Mapping):
                raise invalid(f"{name} must be a JSON object")
        case "array":
            if not isinstance(value, list):
                raise invalid(f"{name} must be a JSON list")
        case _:
            raise invalid(f"{name} has an unsupported type")
    if "enum" in rules and str(value) not in {str(choice) for choice in rules["enum"]}:
        raise invalid(f"{name} must be one of: {', '.join(map(str, rules['enum']))}")
    return value


def _bounds(name: str, value: int | Decimal, rules: Mapping[str, Any]) -> None:
    for keyword, broken in (
        ("minimum", lambda limit: value < limit),
        ("maximum", lambda limit: value > limit),
        ("exclusiveMinimum", lambda limit: value <= limit),
        ("exclusiveMaximum", lambda limit: value >= limit),
    ):
        if keyword in rules and broken(Decimal(str(rules[keyword]))):
            raise invalid(f"{name} is outside its documented range ({keyword} {rules[keyword]})")


def _query_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(type(value).__name__)


def _finite(value: Any) -> bool:
    """A body holds no NaN or infinity anywhere."""
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Decimal):
        return value.is_finite()
    if isinstance(value, Mapping):
        return all(_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    return True


def build_request(step: Mapping[str, Any], operation_input: Mapping[str, Any]) -> Request:
    declared: Mapping[str, Mapping[str, Any]] = step["inputs"]
    unknown = sorted(set(operation_input) - set(declared) - HOST_INPUTS)
    if unknown:
        raise invalid(f"Unknown inputs: {', '.join(unknown)}")
    missing = [n for n, rules in declared.items() if rules["required"] and n not in operation_input]
    if missing:
        raise invalid(f"Required inputs are missing: {', '.join(missing)}")
    query: list[tuple[str, str]] = [(k, v) for k, v in step["fixed"].items()]
    path: str = step["path"]
    body: dict[str, Any] = {}
    for name, rules in declared.items():
        if name not in operation_input:
            continue
        value = _checked(name, rules["type"], operation_input[name], rules)
        wire_name = rules["send_as"]
        match rules["in"]:
            case "path":
                segment = quote(_query_value(value), safe="")
                if segment in DOT_SEGMENTS:
                    raise invalid(f"{name} cannot be {segment!r}")
                path = path.replace("{" + wire_name + "}", segment)
            case "query":
                query.append((wire_name, _query_value(value)))
            case "body":
                body[wire_name] = value
    encoded = None
    if step["has_body"]:
        if not body:
            raise invalid("Give the inputs of the request body, as the step's form describes")
        if not _finite(body):
            raise invalid("The request body holds a number that is not finite")
        encoded = json.dumps(body, default=_json_default, ensure_ascii=False).encode("utf-8")
        if len(encoded) > MAX_BODY_BYTES:
            raise invalid(f"The request body is larger than {MAX_BODY_BYTES // 1024} KiB")
    return Request(step["method"], path, urlencode(query), encoded)
