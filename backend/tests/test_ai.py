import pytest
from unittest.mock import patch
from app import create_app
from app.ai.prompts import get_system_prompt
from app.ai.schemas import validate_ai_request, build_error_response


@pytest.fixture
def client():
    """Create and configure a testing client."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# --- 1. Schema & Validation Tests ---

def test_validate_ai_request_valid():
    """Test validation with valid payload."""
    payload = {"message": "I need a doctor for chest pain"}
    is_valid, error = validate_ai_request(payload)
    assert is_valid is True
    assert error is None  # <--- Updated to match your schema returning None


def test_validate_ai_request_empty():
    """Test validation fails when message is empty."""
    payload = {"message": "   "}
    is_valid, error = validate_ai_request(payload)
    assert is_valid is False
    # V--- Updated to match your exact error string
    assert "'message' must be a non-empty string." in error  


def test_validate_ai_request_missing():
    """Test validation fails when message key is missing."""
    payload = {}
    is_valid, error = validate_ai_request(payload)
    assert is_valid is False


def test_system_prompt_generation():
    """Test system prompt formats and contains required intents."""
    prompt = get_system_prompt()
    assert "BOOK_APPOINTMENT" in prompt
    assert "CHECK_DOCTOR_AVAILABILITY" in prompt
    assert "CHECK_BED_AVAILABILITY" in prompt


# --- 2. Route & API Endpoint Tests ---

def test_understand_endpoint_validation_error(client):
    """Test POST /api/v1/ai/understand returns 400 on empty payload."""
    response = client.post(
        '/api/v1/ai/understand',
        json={"message": ""}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error_code"] == "VALIDATION_ERROR"


def test_understand_endpoint_success_contract(client):
    """Test POST /api/v1/ai/understand returns valid schema contract with mocked LLM."""
    mock_ai_output = {
        "success": True,
        "intent": "BOOK_APPOINTMENT",
        "entities": {
            "specialization": "CARDIOLOGY",
            "doctor_id": None,
            "doctor_name": None,
            "date": "2026-08-24",
            "time": None,
            "time_preference": "MORNING",
            "ward": None,
            "bed_type": None
        },
        "confidence": 0.95,
        "message": "Booking cardiology appointment for 2026-08-24"
    }

    # Mock the LLM service call to test API contract deterministically
    with patch('app.ai.routes.process_ai_request', return_value=mock_ai_output):
        response = client.post(
            '/api/v1/ai/understand',
            json={"message": "Book cardiology tomorrow morning"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["intent"] == "BOOK_APPOINTMENT"
        assert data["entities"]["specialization"] == "CARDIOLOGY"
        assert "confidence" in data
