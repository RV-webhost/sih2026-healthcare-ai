import pytest
from flask import Flask
from unittest.mock import patch, MagicMock

from app.tokens.routes import tokens_bp
from app.tokens.models import TokenStatus

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(tokens_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@patch('app.tokens.routes.service.create_token')
@patch('app.tokens.routes.service.calculate_queue_metrics')
def test_generate_token_success(mock_calc, mock_create, client):
    # Mocking a valid, confirmed appointment generating a token
    mock_token = MagicMock()
    mock_token.id = "T5001"
    mock_token.token_number = 27
    mock_token.patient_id = "P1023"
    mock_token.appointment_id = "APT10045"
    mock_token.doctor_id = "D204"
    mock_token.status = TokenStatus.WAITING
    mock_token.token_date.isoformat.return_value = "2026-08-21"
    mock_token.created_at.isoformat.return_value = "2026-08-21T10:00:00"

    mock_create.return_value = mock_token
    mock_calc.return_value = (4, 40) # 4 people ahead, 40 mins wait

    response = client.post('/api/v1/tokens', json={
        "patient_id": "P1023",
        "appointment_id": "APT10045"
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["token_number"] == 27
    assert data["data"]["estimated_wait_minutes"] == 40

def test_generate_token_missing_data(client):
    response = client.post('/api/v1/tokens', json={"patient_id": "P1023"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False

@patch('app.tokens.routes.service.transition_token_status')
@patch('app.tokens.routes.service.calculate_queue_metrics')
def test_call_patient(mock_calc, mock_transition, client):
    # Validating status transitions (WAITING -> CALLED)
    mock_token = MagicMock()
    mock_token.id = "T5001"
    mock_token.token_number = 27
    mock_token.patient_id = "P1023"      # Added missing field
    mock_token.appointment_id = "APT1"   # Added missing field
    mock_token.doctor_id = "D204"        # Added missing field
    mock_token.status = TokenStatus.CALLED
    mock_token.token_date.isoformat.return_value = "2026-08-21"
    mock_token.created_at.isoformat.return_value = "2026-08-21T10:00:00"
    
    mock_transition.return_value = mock_token
    mock_calc.return_value = (0, 0)
    
    response = client.patch('/api/v1/tokens/T5001/call')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "CALLED"

def test_get_queue_missing_params(client):
    response = client.get('/api/v1/tokens/queue')
    assert response.status_code == 400

def test_get_current_token_missing_params(client):
    response = client.get('/api/v1/tokens/current')
    assert response.status_code == 400