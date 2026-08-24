import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_auth_flow():
    # Dynamic email prevents duplicate email 400 Bad Request errors
    unique_email = f"test_{int(time.time())}@example.com"
    
    # 1. Register
    payload = {
        "name": "Rahul Test",
        "email": unique_email,
        "password": "StrongPassword123",
        "phone": "9876543210"
    }
    res_reg = client.post("/api/auth/register", json=payload)
    assert res_reg.status_code == 201
    
    # 2. Login
    login_payload = {"email": unique_email, "password": "StrongPassword123"}
    res_login = client.post("/api/auth/login", json=login_payload)
    assert res_login.status_code == 200
    token = res_login.json()["data"]["access_token"]
    
    # 3. Access Protected Profile
    res_profile = client.get("/api/patients/me", headers={"Authorization": f"Bearer {token}"})
    assert res_profile.status_code == 200

def test_get_profile_unauthorized():
    response = client.get("/api/patients/me")
    assert response.status_code == 401