"""Turn FreightUtils' answer into the step result, or into one error.

A documented success is HTTP 200; any other 2xx is not taken as success. The answer is
returned whole in ``data``; its ``_source`` block and ``citation`` are lifted out as they
are, because FreightUtils' terms let an answer be stored, shown and cited only with its
source line beside the values.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from . import errors
from .connection import Connection
from .errors import ExtensionError, safe_text
from .transport import Response

SUCCESS = 200
JSON_TYPES = frozenset({"application/json", "application/problem+json"})
TEXT_TYPES = frozenset({"text/plain", "application/rss+xml", "application/xml", "text/xml"})
#: Warn when this many requests or fewer are left in the allowance.
LOW_ALLOWANCE = 3
MAX_UPSTREAM_HEADER = 16 * 1024
MAX_PROVIDER_TEXT = 600
RATE_LIMIT_HEADERS = {
    "limit": "x-ratelimit-limit",
    "remaining": "x-ratelimit-remaining",
    "window_seconds": "x-ratelimit-window",
}


def _scrub(text: str, connection: Connection) -> str:
    return text.replace(connection.api_key, "[api key]") if connection.api_key else text


def _int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _reset(value: str | None) -> str | None:
    """X-RateLimit-Reset as an ISO time: FreightUtils sends Unix seconds."""
    seconds = _int(value)
    if seconds is None:
        return safe_text(value, 40) or None
    return datetime.fromtimestamp(seconds, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def rate_limit(response: Response) -> dict[str, Any] | None:
    found: dict[str, Any] = {
        key: _int(response.headers.get(header)) for key, header in RATE_LIMIT_HEADERS.items()
    }
    found["resets_at"] = _reset(response.headers.get("x-ratelimit-reset"))
    return found if any(v is not None for v in found.values()) else None


def upstream(response: Response) -> dict[str, Any] | None:
    raw = response.headers.get("x-freightutils-upstream")
    if not raw or len(raw) > MAX_UPSTREAM_HEADER:
        return None
    try:
        value = json.loads(raw)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def _parsed(response: Response) -> tuple[Any, str | None]:
    """(JSON value, text): one of them is set for an answer with a body."""
    if not response.body:
        return None, None
    try:
        decoded = response.body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExtensionError(errors.INVALID_RESPONSE, "FreightUtils' answer is not UTF-8") from exc
    if response.content_type in JSON_TYPES:
        try:
            return json.loads(decoded), None
        except (ValueError, RecursionError) as exc:
            raise ExtensionError(
                errors.INVALID_RESPONSE, "FreightUtils' answer is not valid JSON"
            ) from exc
    if response.content_type in TEXT_TYPES:
        return None, decoded
    raise ExtensionError(
        errors.INVALID_RESPONSE,
        f"FreightUtils answered with an unexpected content type ({response.content_type})",
    )


def _warnings(fresh: dict[str, Any] | None, allowance: dict[str, Any] | None) -> list[str]:
    warnings = []
    if fresh and fresh.get("stale") is True:
        datasets = fresh.get("datasets")
        stale = sorted(
            name
            for name, state in (datasets.items() if isinstance(datasets, dict) else [])
            if isinstance(state, dict) and state.get("stale") is True
        )
        names = f" ({', '.join(stale)})" if stale else ""
        warnings.append(
            f"A dataset behind this answer missed its update check{names}; the answer comes "
            "from the last verified edition"
        )
    remaining = allowance.get("remaining") if allowance else None
    if isinstance(remaining, int) and remaining <= LOW_ALLOWANCE:
        resets = allowance.get("resets_at") if allowance else None
        when = f", until {resets}" if resets else ""
        warnings.append(f"{remaining} FreightUtils requests left in the allowance{when}")
    return warnings


def result(response: Response) -> dict[str, Any]:
    """The step result of a successful answer."""
    if response.status != SUCCESS:
        raise ExtensionError(
            errors.INVALID_RESPONSE,
            f"FreightUtils answered HTTP {response.status}, which its API does not document "
            "as an answer to this request",
            http_status=response.status,
        )
    data, text = _parsed(response)
    fresh = upstream(response)
    allowance = rate_limit(response)
    return {
        "status": response.status,
        "data": data,
        "text": text,
        "source": data.get("_source") if isinstance(data, dict) else None,
        "citation": data.get("citation") if isinstance(data, dict) else None,
        "upstream": fresh,
        "rate_limit": allowance,
        "warnings": _warnings(fresh, allowance),
    }


def _provider_text(response: Response, connection: Connection) -> str:
    """FreightUtils' own words about the refusal: ``error``, ``message`` or ``detail``."""
    try:
        data, text = _parsed(response)
    except ExtensionError:
        return ""
    if isinstance(data, dict):
        for key in ("error", "message", "detail", "title"):
            if isinstance(data.get(key), str) and data[key].strip():
                return _scrub(safe_text(data[key], MAX_PROVIDER_TEXT), connection)
    return _scrub(safe_text(text or "", MAX_PROVIDER_TEXT), connection)


def _rate_limit_message(response: Response, connection: Connection) -> tuple[str, int | None]:
    try:
        data, _ = _parsed(response)
    except ExtensionError:
        data = None
    data = data if isinstance(data, dict) else {}
    allowance = rate_limit(response) or {}
    limit = data.get("limit") or allowance.get("limit")
    window = data.get("window")
    reset = data.get("reset_at") or allowance.get("resets_at")
    retry = _int(response.headers.get("retry-after"))
    if retry is None and isinstance(data.get("retry_after_seconds"), int):
        retry = data["retry_after_seconds"]
    spent = "The FreightUtils request allowance is spent"
    if limit:
        spent += f" ({safe_text(limit, 20)} requests" + (
            f" per {safe_text(window, 10)})" if window else ")"
        )
    if reset:
        spent += f"; it resets at {safe_text(reset, 40)}"
    elif retry is not None:
        spent += f"; try again in {retry} seconds"
    if connection.anonymous:
        spent += ". Add a free API key to the connection for 100 requests a day"
    return spent + ". The step was not repeated.", retry


def failure(response: Response, connection: Connection) -> ExtensionError:
    """The one error a refusal of FreightUtils becomes."""
    status = response.status
    said = _provider_text(response, connection)
    detail = f": {said}" if said else ""
    match status:
        case 400 | 405 | 422:
            return ExtensionError(
                errors.UPSTREAM_VALIDATION_FAILED,
                f"FreightUtils refused the request{detail}",
                http_status=status,
            )
        case 401 | 403:
            hint = (
                "check the API key in the connection"
                if not connection.anonymous
                else "this request needs an API key in the connection"
            )
            return ExtensionError(
                errors.AUTHENTICATION_FAILED,
                f"FreightUtils did not accept the request ({hint}){detail}",
                http_status=status,
            )
        case 404:
            return ExtensionError(
                errors.NOT_FOUND, f"FreightUtils found nothing{detail}", http_status=status
            )
        case 424:
            return ExtensionError(
                errors.STALE_DATA,
                "A dataset of this answer missed its update check, and the step asks to "
                f"refuse stale data{detail}",
                http_status=status,
            )
        case 429:
            message, retry = _rate_limit_message(response, connection)
            return ExtensionError(
                errors.RATE_LIMITED, message, http_status=status, retry_after_seconds=retry
            )
        case _ if status >= 500:
            return ExtensionError(
                errors.UPSTREAM_UNAVAILABLE,
                f"FreightUtils is unavailable (HTTP {status}){detail}",
                retryable=True,
                http_status=status,
            )
        case _:
            return ExtensionError(
                errors.INVALID_RESPONSE,
                f"FreightUtils answered HTTP {status}, which its API does not document{detail}",
                http_status=status,
            )
