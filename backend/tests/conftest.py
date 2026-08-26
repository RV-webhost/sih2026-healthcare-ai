import uuid
from functools import wraps

import pytest

from app import create_app
from app.extensions import db
from app.models import Ward, Bed


# ---------------------------------------------------------------------------
# Test configuration
# ---------------------------------------------------------------------------

class TestConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-jwt-secret-key"
    TESTING = True


# ---------------------------------------------------------------------------
# Test user for M6 orchestrator tests only
#
# IMPORTANT:
# We do NOT replace app.auth.deps globally.
# M5's real authentication must remain available to auth tests.
# ---------------------------------------------------------------------------

MOCK_USER = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "patient_id": "00000000-0000-0000-0000-000000000002",
    "role": "PATIENT",
}


def _bypass_m6_auth(view_fn):
    """
    Wrapper used only for M6 tests.

    Calls the original undecorated Flask view with the test user.
    """
    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        return view_fn(MOCK_USER, *args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Application fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """
    Shared Flask application for the test session.

    Real M5 authentication remains intact here.
    """
    return create_app(TestConfig)


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(app, request):
    """
    Flask test client with a clean SQLite database.

    For M6 orchestrator tests only, temporarily bypass the M5 authentication
    decorator at the registered Flask view level.

    Other module tests continue using the real authentication implementation.
    """
    with app.app_context():
        db.create_all()

        # The registered Flask endpoint name from:
        # @orchestrator_bp.route('/assistant')
        endpoint_name = "orchestrator.assistant_endpoint"

        original_view = app.view_functions.get(endpoint_name)

        # Only bypass authentication for test_orchestrator.py.
        is_m6_test = request.module.__name__.endswith("test_orchestrator")

        if is_m6_test and original_view is not None:
            # M5's decorator should preserve the original function through
            # functools.wraps. Walk through __wrapped__ when available.
            target_view = original_view

            while hasattr(target_view, "__wrapped__"):
                target_view = target_view.__wrapped__

            app.view_functions[endpoint_name] = _bypass_m6_auth(target_view)

        try:
            yield app.test_client()
        finally:
            # Restore the original authenticated endpoint.
            if is_m6_test and original_view is not None:
                app.view_functions[endpoint_name] = original_view

            db.session.remove()
            db.drop_all()


# ---------------------------------------------------------------------------
# Common test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_doctor_id():
    return uuid.uuid4()


@pytest.fixture
def mock_patient_id():
    return uuid.uuid4()


@pytest.fixture
def seed_wards_and_beds(app):
    """
    Seed minimal ward/bed data for bed-related tests.
    """
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

        db.session.add_all([
            icu_ward,
            gen_ward,
        ])

        icu_bed = Bed(
            id=icu_bed_id,
            ward_id=icu_ward_id,
            bed_number="ICU-101",
            bed_type="ICU",
            status="AVAILABLE",
        )

        gen_bed = Bed(
            id=gen_bed_id,
            ward_id=gen_ward_id,
            bed_number="GEN-201",
            bed_type="General",
            status="AVAILABLE",
        )

        db.session.add_all([
            icu_bed,
            gen_bed,
        ])

        db.session.commit()

        return {
            "icu_ward_id": str(icu_ward_id),
            "gen_ward_id": str(gen_ward_id),
            "icu_bed_id": str(icu_bed_id),
            "gen_bed_id": str(gen_bed_id),
        }