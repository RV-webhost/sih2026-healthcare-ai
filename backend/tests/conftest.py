import uuid
import pytest
from app import create_app
from app.extensions import db
from app.models import Ward, Bed, BedAllocation, Appointment


class TestConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-jwt-secret-key"
    TESTING = True


# Define mock Patient and Doctor models for foreign key resolution in SQLite
class MockPatient(db.Model):
    __tablename__ = "patients"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    # Changed 'name' to 'full_name' to stop crashing the real model
    full_name = db.Column(db.String(100), default="Test Patient")





@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    return app


@pytest.fixture(scope="function")
def client(app):
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


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
            ward_type="ICU"
        )
        gen_ward = Ward(
            id=gen_ward_id,
            name="General Ward A",
            ward_type="General"
        )
        db.session.add_all([icu_ward, gen_ward])

        b1 = Bed(
            id=icu_bed_id,
            ward_id=icu_ward_id,
            bed_number="ICU-101",
            bed_type="ICU",
            status="AVAILABLE"
        )
        b2 = Bed(
            id=gen_bed_id,
            ward_id=gen_ward_id,
            bed_number="GEN-201",
            bed_type="General",
            status="AVAILABLE"
        )
        db.session.add_all([b1, b2])
        db.session.commit()

        return {
            "icu_ward_id": str(icu_ward_id),
            "gen_ward_id": str(gen_ward_id),
            "icu_bed_id": str(icu_bed_id),
            "gen_bed_id": str(gen_bed_id),
        }
