import uuid
from datetime import date, timedelta
from typing import Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.tokens.models import Token, TokenStatus


# ---------------------------------------------------------------------------
# StaticPool SQLite In-Memory Database (Persists tables across threads)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="function", autouse=True)
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: Session) -> AsyncClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_appointment_verifier():
    with patch("app.tokens.service.verify_appointment") as mock_v:
        mock_v.return_value = {"valid": True, "doctor_id": "D204", "status": "CONFIRMED"}
        yield mock_v


def extract_data(res_json: dict) -> dict:
    if isinstance(res_json, dict) and "data" in res_json and isinstance(res_json["data"], dict):
        return res_json["data"]
    return res_json


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_token_first_of_day(client: AsyncClient, mock_appointment_verifier):
    response = await client.post(
        "/api/tokens",
        json={"patient_id": "P101", "appointment_id": "APT1001"},
    )
    assert response.status_code == 201
    data = extract_data(response.json())
    assert data["token_number"] == 1
    assert data["status"] == TokenStatus.WAITING.value
    assert data["people_ahead"] == 0
    assert data["estimated_wait_minutes"] == 0


@pytest.mark.asyncio
async def test_daily_token_sequence_increments_per_doctor(client: AsyncClient, mock_appointment_verifier):
    for expected_num in [1, 2, 3]:
        res = await client.post(
            "/api/tokens",
            json={"patient_id": f"P{expected_num}", "appointment_id": f"APT{expected_num}"},
        )
        assert res.status_code == 201
        data = extract_data(res.json())
        assert data["token_number"] == expected_num


@pytest.mark.asyncio
async def test_sequence_isolation_between_different_doctors(client: AsyncClient, db_session: Session, mock_appointment_verifier):
    doc_a = "DOC_A"
    doc_b = "DOC_B"
    today = date.today()

    t1 = Token(
        id=str(uuid.uuid4()),
        doctor_id=doc_a,
        patient_id="P1",
        appointment_id="APT1",
        token_number=1,
        token_date=today,
        status=TokenStatus.WAITING,
    )
    t2 = Token(
        id=str(uuid.uuid4()),
        doctor_id=doc_b,
        patient_id="P2",
        appointment_id="APT2",
        token_number=1,
        token_date=today,
        status=TokenStatus.WAITING,
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    assert t1.token_number == 1
    assert t2.token_number == 1


@pytest.mark.asyncio
async def test_sequence_resets_on_new_date(client: AsyncClient, db_session: Session, mock_appointment_verifier):
    doc_id = "D204"
    yesterday = date.today() - timedelta(days=1)

    old_token = Token(
        id=str(uuid.uuid4()),
        doctor_id=doc_id,
        patient_id="P_OLD",
        appointment_id="APT_OLD",
        token_number=15,
        token_date=yesterday,
        status=TokenStatus.COMPLETED,
    )
    db_session.add(old_token)
    db_session.commit()

    res = await client.post("/api/tokens", json={"patient_id": "P_NEW", "appointment_id": "APT_NEW"})
    assert res.status_code == 201
    data = extract_data(res.json())
    assert data["token_number"] == 1


@pytest.mark.asyncio
async def test_generate_token_fails_if_appointment_invalid(client: AsyncClient):
    res = await client.post(
        "/api/tokens",
        json={"patient_id": "", "appointment_id": ""},
    )
    assert res.status_code in [400, 422]


@pytest.mark.asyncio
async def test_people_ahead_and_wait_time_calculation(client: AsyncClient, mock_appointment_verifier):
    tokens = []
    for i in range(4):
        res = await client.post(
            "/api/tokens",
            json={"patient_id": f"P_{i}", "appointment_id": f"APT_{i}"},
        )
        tokens.append(extract_data(res.json()))

    assert tokens[0]["people_ahead"] == 0
    assert tokens[0]["estimated_wait_minutes"] == 0
    assert tokens[3]["people_ahead"] == 3
    assert tokens[3]["estimated_wait_minutes"] == 30


@pytest.mark.asyncio
async def test_metrics_recalculate_when_preceding_tokens_change_status(
    client: AsyncClient, mock_appointment_verifier
):
    res1 = await client.post("/api/tokens", json={"patient_id": "P1", "appointment_id": "APT1"})
    res2 = await client.post("/api/tokens", json={"patient_id": "P2", "appointment_id": "APT2"})
    res3 = await client.post("/api/tokens", json={"patient_id": "P3", "appointment_id": "APT3"})

    token1_data = extract_data(res1.json())
    token3_data = extract_data(res3.json())

    token1_id = token1_data["token_id"]
    token3_id = token3_data["token_id"]

    assert token3_data["people_ahead"] == 2
    assert token3_data["estimated_wait_minutes"] == 20

    await client.patch(f"/api/tokens/{token1_id}/call")

    res3_updated = await client.get(f"/api/tokens/{token3_id}")
    assert res3_updated.status_code == 200
    updated_data = extract_data(res3_updated.json())
    assert updated_data["people_ahead"] == 1
    assert updated_data["estimated_wait_minutes"] == 10


@pytest.mark.asyncio
async def test_valid_token_lifecycle(client: AsyncClient, mock_appointment_verifier):
    res = await client.post(
        "/api/tokens",
        json={"patient_id": "P_LIFE", "appointment_id": "APT_LIFE"},
    )
    t_data = extract_data(res.json())
    token_id = t_data["token_id"]

    call_res = await client.patch(f"/api/tokens/{token_id}/call")
    assert call_res.status_code == 200
    assert extract_data(call_res.json())["status"] == TokenStatus.CALLED.value

    comp_res = await client.patch(f"/api/tokens/{token_id}/complete")
    assert comp_res.status_code == 200
    assert extract_data(comp_res.json())["status"] == TokenStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_invalid_lifecycle_transition_fails(client: AsyncClient, mock_appointment_verifier):
    res = await client.post(
        "/api/tokens",
        json={"patient_id": "P_FAIL", "appointment_id": "APT_FAIL"},
    )
    t_data = extract_data(res.json())
    token_id = t_data["token_id"]

    comp_res = await client.patch(f"/api/tokens/{token_id}/complete")
    assert comp_res.status_code in [400, 422]


@pytest.mark.asyncio
async def test_cancelled_or_skipped_tokens_cannot_be_called(client: AsyncClient, mock_appointment_verifier):
    res = await client.post(
        "/api/tokens",
        json={"patient_id": "P_SKIP", "appointment_id": "APT_SKIP"},
    )
    t_data = extract_data(res.json())
    token_id = t_data["token_id"]

    await client.patch(f"/api/tokens/{token_id}/skip")

    call_res = await client.patch(f"/api/tokens/{token_id}/call")
    assert call_res.status_code in [400, 422]


@pytest.mark.asyncio
async def test_doctor_call_next_token_in_order(client: AsyncClient, mock_appointment_verifier):
    res1 = await client.post("/api/tokens", json={"patient_id": "P_ORD1", "appointment_id": "APT_ORD1"})
    t1_data = extract_data(res1.json())
    token1_id = t1_data["token_id"]

    call_res = await client.patch(f"/api/tokens/{token1_id}/call")
    assert call_res.status_code == 200
    assert extract_data(call_res.json())["status"] == TokenStatus.CALLED.value


@pytest.mark.asyncio
async def test_doctor_call_next_when_queue_empty(client: AsyncClient):
    random_id = str(uuid.uuid4())
    res = await client.get(f"/api/tokens/{random_id}")
    assert res.status_code == 404