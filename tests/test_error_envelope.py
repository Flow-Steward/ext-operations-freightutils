"""Every error is the host's public error envelope.

The host counts a failure toward quarantine unless the envelope carries error_code, error
and an errors list whose first entry repeats them.
"""

from __future__ import annotations

import pytest

import main
from runtime import errors


def host_accepts(response: dict) -> bool:
    entries = response.get("errors")
    return (
        response.get("ok") is False
        and bool(str(response.get("error_code") or "").strip())
        and bool(str(response.get("error") or "").strip())
        and isinstance(entries, list)
        and bool(entries)
        and entries[0] == {"code": response["error_code"], "message": response["error"]}
        and response.get("definitely_no_external_effect") is True
    )


@pytest.mark.parametrize("code", sorted(errors.CODES))
def test_every_error_code_is_the_hosts_public_envelope(code):
    assert host_accepts(errors.error_response(code, ""))
    assert host_accepts(errors.error_response(code, "Something to say"))


def test_an_unknown_code_becomes_internal_error():
    assert errors.error_response("made_up", "x")["error_code"] == "internal_error"


def test_the_entrypoint_refusal_is_the_same_envelope():
    assert host_accepts(
        main.error_response(errors.INVALID_PAYLOAD, "The request is not valid JSON")
    )
