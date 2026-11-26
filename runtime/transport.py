"""One HTTPS request to FreightUtils.

Only ``https://www.freightutils.com`` is called; redirects are refused, an answer is read
up to ``MAX_RESPONSE_BYTES`` and a request waits at most ``REQUEST_TIMEOUT_SECONDS``.
Nothing is retried: each request counts against the caller's allowance.
"""

from __future__ import annotations

import ssl
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from email.message import Message
from typing import Any

from . import errors
from .connection import Connection
from .errors import ExtensionError
from .identity import BASE_URL, USER_AGENT
from .inputs import Request

REQUEST_TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict[str, str]
    body: bytes

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "").split(";")[0].strip().lower()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise ExtensionError(
            errors.REDIRECT_REJECTED,
            f"FreightUtils answered with a redirect (HTTP {code}); it was not followed",
        )


Opener = Callable[[urllib.request.Request, float], Any]


def _default_opener() -> Opener:
    opener = urllib.request.build_opener(
        _NoRedirect, urllib.request.HTTPSHandler(context=ssl.create_default_context())
    )
    return lambda request, timeout: opener.open(request, timeout=timeout)


def _headers(message: Message | None) -> dict[str, str]:
    if message is None:
        return {}
    return {key.lower(): value for key, value in message.items()}


def _read(stream: Any) -> bytes:
    body = stream.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ExtensionError(
            errors.RESPONSE_TOO_LARGE,
            f"FreightUtils' answer is larger than {MAX_RESPONSE_BYTES // (1024 * 1024)} MiB; "
            "ask for fewer rows",
        )
    return body


def send(connection: Connection, request: Request, opener: Opener | None = None) -> Response:
    url = f"{BASE_URL}{request.path}" + (f"?{request.query}" if request.query else "")
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if request.body is not None:
        headers["Content-Type"] = "application/json"
    if connection.api_key:
        headers["X-API-Key"] = connection.api_key
    outgoing = urllib.request.Request(
        url, data=request.body, headers=headers, method=request.method
    )
    open_request = opener or _default_opener()
    try:
        with open_request(outgoing, REQUEST_TIMEOUT_SECONDS) as answer:
            return Response(answer.status, _headers(answer.headers), _read(answer))
    except urllib.error.HTTPError as answer:
        with answer:
            return Response(answer.code, _headers(answer.headers), _read(answer))
    except ExtensionError:
        raise
    except TimeoutError as exc:
        raise ExtensionError(
            errors.TIMEOUT,
            f"FreightUtils did not answer within {REQUEST_TIMEOUT_SECONDS} seconds",
            retryable=True,
        ) from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise ExtensionError(
                errors.TIMEOUT,
                f"FreightUtils did not answer within {REQUEST_TIMEOUT_SECONDS} seconds",
                retryable=True,
            ) from exc
        raise ExtensionError(
            errors.CONNECTION_FAILED, "FreightUtils could not be reached", retryable=True
        ) from exc
