import time
import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def client():
    # Create the Flask app instance using the shared application factory
    app = create_app()
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_auth_flow(client):
    # Dynamic email prevents duplicate email errors
    unique_email = f"test_{int(time.time())}@example.com"
    
    # 1. Register
    payload = {
        "name": "Rahul Test",
        "email": unique_email,
        "password": "StrongPassword123",
        "phone": "9876543210"
    }
    res_reg = client.post("/api/v1/auth/register", json=payload)
    assert res_reg.status_code == 201
    
    # 2. Login
    login_payload = {"email": unique_email, "password": "StrongPassword123"}
    res_login = client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    token = res_login.get_json()["data"]["access_token"]
    
    # 3. Access Protected Profile
    res_profile = client.get(
        "/api/v1/patients/me", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_profile.status_code == 200

def test_get_profile_unauthorized(client):
    response = client.get("/api/v1/patients/me")
    assert response.status_code == 401