"""Steps against recorded live answers and documented refusals of FreightUtils."""

from __future__ import annotations

import json

import pytest
from support import API_KEY, answer, live, run

LIVE_STEPS = [
    ("look_up_un_number", {"un": "1203"}, "adr_lookup", "/api/adr", [("un", "1203")]),
    (
        "calculate_loading_metres",
        {"pallet": "euro", "qty": 10},
        "ldm",
        "/api/ldm",
        [("pallet", "euro"), ("qty", "10")],
    ),
    (
        "calculate_emissions",
        {"mass": 1000, "distance_km": 500, "mode": "road"},
        "emissions",
        "/api/emissions",
        [("mass", "1000"), ("distance_km", "500"), ("mode", "road")],
    ),
    ("look_up_incoterms", {"code": "FOB"}, "incoterms", "/api/incoterms", [("code", "FOB")]),
    ("look_up_hs_code", {"code": "847130"}, "hs", "/api/hs", [("code", "847130")]),
    (
        "validate_container_number",
        {"container_number": "CSQU3054383"},
        "validate",
        "/api/validate",
        [("type", "container"), ("value", "CSQU3054383")],
    ),
]


@pytest.mark.parametrize(("step", "step_input", "recorded", "path", "query"), LIVE_STEPS)
def test_a_live_answer_comes_back_whole_with_its_source(step, step_input, recorded, path, query):
    response, fake = run(step, step_input, live(recorded))
    assert response["ok"] is True, response
    result = response["result"]
    body = json.loads(live(recorded)[2])
    assert result["status"] == 200
    assert result["data"] == body
    assert result["source"] == body.get("_source")
    (sent,) = fake.sent
    assert (sent.method, sent.host, sent.path) == ("GET", "www.freightutils.com", path)
    assert sorted(sent.query) == sorted(query)
    assert "x-api-key" not in sent.headers
    assert sent.headers["user-agent"].startswith("FlowSteward-FreightUtils-Extension/0.1.0")


def test_the_allowance_and_data_freshness_are_returned():
    response, _ = run("look_up_hs_code", {"code": "847130"}, live("hs"))
    result = response["result"]
    assert result["rate_limit"] == {
        "limit": 25,
        "remaining": 21,
        "window_seconds": 86400,
        "resets_at": "2026-11-27T00:00:00Z",
    }
    assert result["upstream"]["stale"] is False
    assert result["warnings"] == []


def test_a_stale_dataset_is_a_warning():
    response, _ = run(
        "calculate_emissions", {"mass": 1000, "distance_km": 500, "mode": "road"}, live("emissions")
    )
    (warning,) = response["result"]["warnings"]
    assert "missed its update check (emissions)" in warning


def test_a_low_allowance_is_a_warning():
    response, _ = run(
        "look_up_hs_code",
        {"code": "0901"},
        answer(200, {"hscode": "0901"}, **{"x-ratelimit-remaining": "2"}),
    )
    assert response["result"]["warnings"] == ["2 FreightUtils requests left in the allowance"]


def test_the_api_key_goes_in_the_header_and_nowhere_else():
    response, fake = run(
        "look_up_hs_code",
        {"code": "0901"},
        answer(401, {"error": f"Unknown key {API_KEY}"}),
        key=API_KEY,
    )
    assert fake.sent[0].headers["x-api-key"] == API_KEY
    assert response["error_code"] == "authentication_failed"
    assert API_KEY not in json.dumps(response)
    assert "check the API key" in response["error"]


def test_an_unknown_body_field_is_refused_by_freightutils_with_its_reason():
    status, headers, body = live("unknown_body")
    response, fake = run(
        "check_limited_quantities",
        {"mode": "lq", "items": [{"un_number": "1203", "quantity": 1}]},
        (status, headers, body),
    )
    assert fake.sent[0].body == {"mode": "lq", "items": [{"un_number": "1203", "quantity": 1}]}
    assert response["error_code"] == "upstream_validation_failed"
    assert 'Unknown field "colour"' in response["error"]
    assert response["http_status"] == 400 and response["retryable"] is False


@pytest.mark.parametrize(
    ("step_input", "message"),
    [
        ({"code": "0901", "colour": "red"}, "Unknown inputs: colour"),
        ({}, "Required inputs are missing: code"),
        ({"code": 901}, "code must be text"),
    ],
)
def test_inputs_are_checked_before_anything_is_sent(step_input, message):
    response, fake = run("look_up_hs_code", step_input)
    assert fake.sent == []
    assert response["error_code"] == "invalid_payload"
    assert message in response["error"]


@pytest.mark.parametrize(
    ("step", "step_input", "message"),
    [
        ("calculate_emissions", {"mass": 1, "distance_km": 1, "mode": "space"}, "one of"),
        ("calculate_cbm", {"l": True, "w": 1, "h": 1}, "must be a number"),
        ("calculate_cbm", {"l": 1, "w": 1, "h": 1, "pcs": 2.5}, "whole number"),
        ("look_up_airlines", {"limit": 101}, "documented range"),
        ("check_adr_exemption_for_substance", {"un": "1203", "qty": 0}, "exclusiveMinimum"),
        ("look_up_dangerous_goods", {"client": "two words"}, "documented form"),
        ("get_check_receipt", {"check_id": "../keys"}, "documented form"),
        ("get_adr_code", {"family": "sp", "code": ".."}, "cannot be"),
        ("check_adr_exemption_for_load", {}, "request body"),
    ],
)
def test_types_choices_bounds_and_paths_are_checked(step, step_input, message):
    response, fake = run(step, step_input)
    assert fake.sent == [], response
    assert message in response["error"]


def test_a_path_value_is_one_encoded_segment():
    response, fake = run(
        "get_adr_code", {"family": "sp", "code": "640/X"}, answer(200, {"code": "640"})
    )
    assert response["ok"] is True
    assert fake.sent[0].url == "https://www.freightutils.com/api/adr/codes/sp/640%2FX"


def test_a_spent_allowance_says_when_it_resets_and_is_not_repeated():
    refusal = answer(
        429,
        {
            "error": "rate_limited",
            "message": "Daily limit reached",
            "tier": "anon",
            "limit": 25,
            "window": "1d",
            "reset_at": "2026-11-27T00:00:00Z",
            "retry_after_seconds": 3600,
        },
        **{"retry-after": "3600"},
    )
    response, fake = run("look_up_hs_code", {"code": "0901"}, refusal)
    assert len(fake.sent) == 1
    assert response["error_code"] == "rate_limited"
    assert response["error"] == (
        "The FreightUtils request allowance is spent (25 requests per 1d); it resets at "
        "2026-11-27T00:00:00Z. Add a free API key to the connection for 100 requests a day. "
        "The step was not repeated."
    )
    assert response["retryable"] is False and response["retry_after_seconds"] == 3600


@pytest.mark.parametrize(
    ("status", "body", "code", "retryable"),
    [
        (404, {"error": "No HS code 9999"}, "not_found", False),
        (422, {"error": "EDITION_UNSUPPORTED"}, "upstream_validation_failed", False),
        (424, {"title": "stale_upstream"}, "stale_data", False),
        (503, {"error": "UK Trade Tariff unavailable"}, "upstream_unavailable", True),
        (418, {"error": "teapot"}, "invalid_response", False),
    ],
)
def test_refusals_become_one_error_each(status, body, code, retryable):
    response, _ = run("look_up_hs_code", {"code": "9999"}, answer(status, body))
    assert response["ok"] is False
    assert response["error_code"] == code
    assert response["retryable"] is retryable
    assert response["errors"] == [{"code": code, "message": response["error"]}]


def test_a_2xx_freightutils_does_not_document_is_not_a_success():
    response, _ = run("look_up_hs_code", {"code": "0901"}, answer(201, {"hscode": "0901"}))
    assert response["error_code"] == "invalid_response"


def test_a_text_answer_comes_back_as_text():
    check_id = "chk_" + "A" * 22
    receipt = (200, {"content-type": "text/plain; charset=utf-8"}, b"Receipt\nresult: ok")
    response, fake = run("get_check_receipt", {"check_id": check_id, "format": "text"}, receipt)
    assert fake.sent[0].path == f"/api/receipts/{check_id}"
    assert response["result"]["text"] == "Receipt\nresult: ok"
    assert response["result"]["data"] is None and response["result"]["source"] is None


def test_an_unexpected_content_type_is_refused():
    page = (200, {"content-type": "text/html"}, b"<html></html>")
    response, _ = run("look_up_hs_code", {"code": "0901"}, page)
    assert response["error_code"] == "invalid_response"


def test_a_redirect_is_not_followed():
    from runtime import transport

    with pytest.raises(transport.ExtensionError) as refused:
        transport._NoRedirect().redirect_request(None, None, 301, "Moved", {}, "https://x/")
    assert refused.value.code == "redirect_rejected"


def test_test_connection_reads_the_code_list_index_and_notes_the_anonymous_allowance():
    response, fake = run("test_connection", {}, answer(200, {"lists": []}))
    assert fake.sent[0].path == "/api/codes"
    assert response["result"]["warnings"][0].startswith("No API key: FreightUtils answers 25")


def test_a_malformed_key_is_refused_before_sending():
    response, fake = run("look_up_hs_code", {"code": "0901"}, key="has space")
    assert fake.sent == []
    assert response["error_code"] == "invalid_connection"
