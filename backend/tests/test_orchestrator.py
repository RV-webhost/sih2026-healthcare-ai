"""
M6 orchestrator tests for POST /api/v1/assistant.

These cases lock the routing and AssistantResponseSchema JSON contract.
M1 (AI) and M5 (auth) are mocked so we never call the LLM or require a JWT.
"""

from __future__ import annotations

from functools import wraps
from unittest.mock import patch
import sys
import types

import pytest

from app.orchestrator.schemas import AssistantResponseSchema

# ---------------------------------------------------------------------------
# M5 auth bypass — must be installed before the Flask app (and routes) load
# ---------------------------------------------------------------------------

MOCK_USER = {"user_id": "1001", "patient_id": "P1001", "role": "PATIENT"}

ASSISTANT_URL = "/api/v1/assistant"
SCHEMA_FIELDS = set(AssistantResponseSchema.model_fields.keys())


def mock_get_current_user(view_fn):
    """Stand-in for @get_current_user from app.auth.decorators."""

    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        return view_fn(MOCK_USER, *args, **kwargs)

    return wrapper


def _install_auth_decorator_mock() -> None:
    """Force orchestrator routes to use the bypass decorator at import time."""
    module = types.ModuleType("app.auth.decorators")
    module.get_current_user = mock_get_current_user
    sys.modules["app.auth.decorators"] = module


_install_auth_decorator_mock()

# Import the app only after the decorator mock is in sys.modules.
from app import create_app  # noqa: E402


def assert_matches_assistant_schema(payload: dict) -> None:
    """Fail if the body is not a valid AssistantResponseSchema document."""
    assert isinstance(payload, dict), "Response body must be a JSON object"
    assert set(payload.keys()).issubset(SCHEMA_FIELDS), (
        f"Unexpected keys {set(payload.keys()) - SCHEMA_FIELDS}; "
        f"allowed fields are {SCHEMA_FIELDS}"
    )
    for required in ("success", "intent", "message"):
        assert required in payload, f"Missing required contract field: {required}"
        assert payload[required] is not None

    assert isinstance(payload["success"], bool)
    assert isinstance(payload["intent"], str)
    assert isinstance(payload["message"], str)

    if "data" in payload:
        assert payload["data"] is None or isinstance(payload["data"], dict)
    if "next_action" in payload:
        assert payload["next_action"] is None or isinstance(payload["next_action"], str)
    if "error_code" in payload:
        assert payload["error_code"] is None or isinstance(payload["error_code"], str)

    # Pydantic round-trip: extra/missing/wrong types will raise
    AssistantResponseSchema.model_validate(payload)


@pytest.fixture
def client():
    """Flask test client with testing config (no live DB/JWT required)."""
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        JWT_SECRET_KEY="test-secret",
    )
    with app.test_client() as test_client:
        yield test_client


def _post_assistant(client, message: str = "hello"):
    return client.post(ASSISTANT_URL, json={"message": message})


def test_unknown_intent(client):
    """UNKNOWN from M1 must fail closed and ask the user to clarify."""
    m1_payload = {"intent": "UNKNOWN", "entities": {}}

    with patch(
        "app.orchestrator.service.extract_intent_and_entities",
        return_value=m1_payload,
    ):
        response = _post_assistant(client, "xyzzy not a healthcare request")

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
        "entities": {"date": "2026-08-21"},
    }

    with patch(
        "app.orchestrator.service.extract_intent_and_entities",
        return_value=m1_payload,
    ):
        response = _post_assistant(client, "I need an appointment on 21 August")

    assert response.status_code == 200
    body = response.get_json()
    assert_matches_assistant_schema(body)
    assert body["success"] is True
    assert body["next_action"] == "ASK_SPECIALIZATION"
    assert body["intent"] == "BOOK_APPOINTMENT"


def test_check_bed_routing(client):
    """CHECK_BED_AVAILABILITY must be delegated to M2 and keep the same intent."""
    m1_payload = {
        "intent": "CHECK_BED_AVAILABILITY",
        "entities": {"ward_type": "ICU"},
    }
    dummy_beds = {"ward_type": "ICU", "available_beds": 3, "status": "AVAILABLE"}

    with patch(
        "app.orchestrator.service.extract_intent_and_entities",
        return_value=m1_payload,
    ), patch(
        "app.orchestrator.service.check_bed_availability",
        return_value=dummy_beds,
    ) as mock_beds:
        response = _post_assistant(client, "Are ICU beds available?")

    assert response.status_code == 200
    body = response.get_json()
    assert_matches_assistant_schema(body)
    assert body["success"] is True
    assert body["intent"] == "CHECK_BED_AVAILABILITY"
    mock_beds.assert_called_once()
    assert mock_beds.call_args.args[0] == {"ward_type": "ICU"}
    if "data" in body and body["data"] is not None:
        assert body["data"] == dummy_beds
