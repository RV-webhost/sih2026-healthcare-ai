import uuid
from functools import wraps

import pytest

from app import create_app
from app.extensions import db
from app.models import Ward, Bed, BedAllocation, Appointment


class TestConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-jwt-secret-key"
    TESTING = True


# ---------------------------------------------------------------------------
# M6 test authentication bypass
# ---------------------------------------------------------------------------

MOCK_USER = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "patient_id": "00000000-0000-0000-0000-000000000002",
    "role": "PATIENT",
}


def _bypass_m6_auth(view_fn):
    """Wrapper used only for M6 tests."""
    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        return view_fn(MOCK_USER, *args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Shared application fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    return create_app(TestConfig)


# ---------------------------------------------------------------------------
# Shared client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(app, request):
    with app.app_context():
        db.create_all()

        endpoint_name = "orchestrator.assistant_endpoint"
        original_view = app.view_functions.get(endpoint_name)
        is_m6_test = request.module.__name__.endswith("test_orchestrator")

        if is_m6_test and original_view is not None:
            target_view = original_view
            while hasattr(target_view, "__wrapped__"):
                target_view = target_view.__wrapped__
            app.view_functions[endpoint_name] = _bypass_m6_auth(target_view)

        try:
            yield app.test_client()
        finally:
            if is_m6_test and original_view is not None:
                app.view_functions[endpoint_name] = original_view
            db.session.remove()
            db.drop_all()


# ---------------------------------------------------------------------------
# Common fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_doctor_id():
    return uuid.uuid4()


@pytest.fixture
def mock_patient_id():
    return uuid.uuid4()


@pytest.fixture
def seed_wards_and_beds(app):
    with app.app_context():
        icu_ward_id = uuid.uuid4()
        gen_ward_id = uuid.uuid4()
        icu_bed_id = uuid.uuid4()
        gen_bed_id = uuid.uuid4()

        icu_ward = Ward(
            id=icu_ward_id,
            name="Intensive Care Unit",
            ward_type="ICU",
        )
        gen_ward = Ward(
            id=gen_ward_id,
            name="General Ward A",
            ward_type="General",
        )
        db.session.add_all([icu_ward, gen_ward])

        b1 = Bed(
            id=icu_bed_id,
            ward_id=icu_ward_id,
            bed_number="ICU-101",
            bed_type="ICU",
            status="AVAILABLE",
        )
        b2 = Bed(
            id=gen_bed_id,
            ward_id=gen_ward_id,
            bed_number="GEN-201",
            bed_type="General",
            status="AVAILABLE",
        )
        db.session.add_all([b1, b2])
        db.session.commit()

        return {
            "icu_ward_id": str(icu_ward_id),
            "gen_ward_id": str(gen_ward_id),
            "icu_bed_id": str(icu_bed_id),
            "gen_bed_id": str(gen_bed_id),
        }
