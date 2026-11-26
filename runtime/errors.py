"""Error codes and the host's response envelopes.

Every failure is the host's public error envelope: ``ok`` false, ``error_code``, ``error``
and ``errors`` whose first entry repeats them. Without that list the host counts an
ordinary refusal (not found, rate limited) as a crash of the extension. No message
carries the API key.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

INVALID_PAYLOAD = "invalid_payload"
INVALID_HOST_ENVELOPE = "invalid_host_envelope"
INVALID_CONNECTION = "invalid_connection"
UNSUPPORTED_OPERATION = "unsupported_operation"
AUTHENTICATION_FAILED = "authentication_failed"
NOT_FOUND = "not_found"
UPSTREAM_VALIDATION_FAILED = "upstream_validation_failed"
STALE_DATA = "stale_data"
RATE_LIMITED = "rate_limited"
UPSTREAM_UNAVAILABLE = "upstream_unavailable"
INVALID_RESPONSE = "invalid_response"
RESPONSE_TOO_LARGE = "response_too_large"
TIMEOUT = "timeout"
CONNECTION_FAILED = "connection_failed"
REDIRECT_REJECTED = "redirect_rejected"
INTERNAL_ERROR = "internal_error"

CODES: frozenset[str] = frozenset(
    {
        INVALID_PAYLOAD,
        INVALID_HOST_ENVELOPE,
        INVALID_CONNECTION,
        UNSUPPORTED_OPERATION,
        AUTHENTICATION_FAILED,
        NOT_FOUND,
        UPSTREAM_VALIDATION_FAILED,
        STALE_DATA,
        RATE_LIMITED,
        UPSTREAM_UNAVAILABLE,
        INVALID_RESPONSE,
        RESPONSE_TOO_LARGE,
        TIMEOUT,
        CONNECTION_FAILED,
        REDIRECT_REJECTED,
        INTERNAL_ERROR,
    }
)
MAX_MESSAGE = 1200


def safe_text(value: object, limit: int = MAX_MESSAGE) -> str:
    """Printable, single-line, bounded text."""
    text = value if isinstance(value, str) else ("" if value is None else str(value))
    text = " ".join("".join(ch if ch.isprintable() else " " for ch in text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


class ExtensionError(Exception):
    """A failure already reduced to a code, a message and the host's retry facts."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        http_status: int | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        self.code = code if code in CODES else INTERNAL_ERROR
        self.message = safe_text(message)
        super().__init__(self.message)
        self.retryable = retryable
        self.http_status = http_status
        self.retry_after_seconds = retry_after_seconds

    def facts(self) -> dict[str, Any]:
        facts: dict[str, Any] = {"retryable": self.retryable}
        if self.http_status is not None:
            facts["failure_class"] = "transient" if self.retryable else "provider"
            facts["http_status"] = self.http_status
            facts["provider_error_code"] = self.code
        if self.retry_after_seconds is not None:
            facts["retry_after_seconds"] = self.retry_after_seconds
        return facts


def invalid(message: str) -> ExtensionError:
    return ExtensionError(INVALID_PAYLOAD, message)


def error_response(code: str, message: str, facts: Mapping[str, Any] | None = None) -> dict:
    """The failing envelope. Every step only reads, so nothing changed anywhere."""
    safe_code = code if code in CODES else INTERNAL_ERROR
    text = safe_text(message) or safe_code.replace("_", " ")
    response: dict[str, Any] = {
        "ok": False,
        "result": {"warnings": []},
        "warnings": [],
        "error_code": safe_code,
        "error": text,
        "errors": [{"code": safe_code, "message": text}],
        "definitely_no_external_effect": True,
        "external_effect_status": "failed",
    }
    if facts:
        response.update(facts)
    return response


def ok(result: Mapping[str, Any]) -> dict[str, Any]:
    return {"ok": True, "result": dict(result), "error_code": None, "error": None, "errors": []}
