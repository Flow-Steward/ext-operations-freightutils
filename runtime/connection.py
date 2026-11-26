"""The project connection: an optional FreightUtils API key.

Without a key FreightUtils answers 25 requests a day per address; a free key gives 100 a
day and Pro 50,000 a month (freightutils.com/pricing). The key travels only in the
``X-API-Key`` header and is never placed in a result, a message or a log line.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from . import errors
from .errors import ExtensionError

CONNECTION_TYPE = "freightutils"
CONFIG_FIELDS = frozenset({"label"})
#: Keys the host may add to a connection's settings that this extension does not use.
HOST_CONFIG_FIELDS = frozenset({"oauth"})
SECRET_FIELDS = frozenset({"api_key"})
MIN_KEY_LENGTH = 8
MAX_KEY_LENGTH = 200
#: Printable ASCII without spaces: a header value that cannot be split.
_KEY_RE = re.compile(r"[\x21-\x7e]+")


@dataclass(frozen=True)
class Connection:
    connection_id: str
    _api_key: str = field(default="", repr=False)

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def anonymous(self) -> bool:
        return not self._api_key


def _refused(message: str) -> ExtensionError:
    return ExtensionError(errors.INVALID_CONNECTION, message)


def _api_key(value: Any) -> str:
    text = value.strip() if isinstance(value, str) else ""
    if not text:
        return ""
    if not MIN_KEY_LENGTH <= len(text) <= MAX_KEY_LENGTH or not _KEY_RE.fullmatch(text):
        raise _refused(
            "The API key of this connection is not usable: paste the whole key FreightUtils "
            "gave you (it starts with fu_), without spaces, or leave it empty"
        )
    return text


def connection_from_payload(payload: Mapping[str, Any], connection_ref: str) -> Connection:
    """The selected connection, checked before anything is sent."""
    action = payload.get("action")
    target = action.get("target") if isinstance(action, Mapping) else None
    connection = target.get("connection") if isinstance(target, Mapping) else None
    if not isinstance(connection, Mapping):
        raise _refused("The selected connection is unavailable")
    connection_id = str(connection.get("connection_id") or "")
    if not connection_id or connection_id != connection_ref:
        raise _refused("The selected connection does not match connection_ref")
    kind = connection.get("connection_type_id") or connection.get("connection_type")
    if kind != CONNECTION_TYPE:
        raise _refused("The selected connection is not a FreightUtils connection")
    config = connection.get("config")
    config = config if isinstance(config, Mapping) else {}
    if set(config) - CONFIG_FIELDS - HOST_CONFIG_FIELDS:
        raise _refused("The connection carries settings this extension does not use")
    secrets = connection.get("secrets")
    secrets = secrets if isinstance(secrets, Mapping) else {}
    if set(secrets) - SECRET_FIELDS:
        raise _refused("The connection carries secrets this extension does not use")
    return Connection(connection_id, _api_key(secrets.get("api_key")))
