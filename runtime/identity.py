"""Who this extension is and which service it calls."""

from __future__ import annotations

EXTENSION_ID = "flowsteward.freightutils"
VERSION = "0.1.0"
REPOSITORY = "https://github.com/Flow-Steward/ext-operations-freightutils"
USER_AGENT = f"FlowSteward-FreightUtils-Extension/{VERSION} (+{REPOSITORY})"
#: The servers entry of the pinned OpenAPI description. The bare domain redirects
#: pages to www, and redirects are not followed.
BASE_URL = "https://www.freightutils.com"
HOST = "www.freightutils.com"
