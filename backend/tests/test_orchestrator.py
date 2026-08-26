"""
M6 orchestrator tests for POST /api/v1/assistant.

These cases lock the routing and AssistantResponseSchema JSON contract.

M1 (AI) and M5 (auth) are mocked so we never call the LLM or require a JWT.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.orchestrator.schemas import AssistantResponseSchema


ASSISTANT_URL = "/api/v1/assistant"
SCHEMA_FIELDS = set(AssistantResponseSchema.model_fields.keys())


def assert_matches_assistant_schema(payload: dict) -> None:
    """Fail if the body is not a valid AssistantResponseSchema document."""
    assert isinstance(payload, dict), "Response body must be a JSON object"

    assert set(payload.keys()).issubset(SCHEMA_FIELDS), (
        f"Unexpected keys {set(payload.keys()) - SCHEMA_FIELDS}; "
        f"allowed fields are {SCHEMA_FIELDS}"
    )

    for required in ("success", "intent", "message"):
        assert required in payload, (
            f"Missing required contract field: {required}"
        )
        assert payload[required] is not None

    assert isinstance(payload["success"], bool)
    assert isinstance(payload["intent"], str)
    assert isinstance(payload["message"], str)

    if "data" in payload:
        assert payload["data"] is None or isinstance(payload["data"], dict)

    if "next_action" in payload:
        assert payload["next_action"] is None or isinstance(
            payload["next_action"], str
        )

    if "error_code" in payload:
        assert payload["error_code"] is None or isinstance(
            payload["error_code"], str
        )

    # Pydantic round-trip validation
    AssistantResponseSchema.model_validate(payload)


def _post_assistant(client, message: str = "hello"):
    return client.post(
        ASSISTANT_URL,
        json={"message": message},
    )


def test_unknown_intent(client):
    """UNKNOWN from M1 must fail closed and ask the user to clarify."""
    m1_payload = {
        "intent": "UNKNOWN",
        "entities": {},
    }

    with patch(
        "app.orchestrator.service.process_ai_request",
        return_value=m1_payload,
    ):
        response = _post_assistant(
            client,
            "xyzzy not a healthcare request",
        )

    assert response.status_code == 200

    body = response.get_json()

    assert_matches_assistant_schema(body)

    assert body["success"] is False
    assert body["next_action"] == "CLARIFY"
    assert body["intent"] == "UNKNOWN"


def test_missing_specialization(client):
    """BOOK_APPOINTMENT without specialization must ask for the department."""
    m1_payload = {
        "intent": "BOOK_APPOINTMENT",
        "entities": {
            "date": "2026-08-21",
        },
    }

    with patch(
        "app.orchestrator.service.process_ai_request",
        return_value=m1_payload,
    ):
        response = _post_assistant(
            client,
            "I need an appointment on 21 August",
        )

    assert response.status_code == 200

    body = response.get_json()

    assert_matches_assistant_schema(body)

    assert body["success"] is True
    assert body["next_action"] == "ASK_SPECIALIZATION"
    assert body["intent"] == "BOOK_APPOINTMENT"


def test_check_bed_routing(client):
    """CHECK_BED_AVAILABILITY must be delegated to M2."""
    m1_payload = {
        "intent": "CHECK_BED_AVAILABILITY",
        "entities": {
            "ward": "ICU",
            "bed_type": None,
        },
    }

    # Match the actual M2 service return contract:
    # get_bed_availability() -> (data, message, error_code)
    dummy_beds = {
        "ward_filter": "ICU",
        "total_beds": 5,
        "available_beds": 3,
        "occupied_beds": 1,
        "maintenance_beds": 1,
        "reserved_beds": 0,
        "beds": [],
    }

    with patch(
        "app.orchestrator.service.process_ai_request",
        return_value=m1_payload,
    ), patch(
        "app.orchestrator.service.get_bed_availability",
        return_value=(
            dummy_beds,
            "Bed availability retrieved successfully.",
            None,
        ),
    ) as mock_beds:
        response = _post_assistant(
            client,
            "Are ICU beds available?",
        )

    assert response.status_code == 200

    body = response.get_json()

    assert_matches_assistant_schema(body)

    assert body["success"] is True
    assert body["intent"] == "CHECK_BED_AVAILABILITY"

    mock_beds.assert_called_once()

    # M2 expects ward_type, not the complete entities dictionary.
    assert mock_beds.call_args.kwargs["ward_type"] == "ICU"

    if "data" in body and body["data"] is not None:
        assert body["data"] == dummy_beds