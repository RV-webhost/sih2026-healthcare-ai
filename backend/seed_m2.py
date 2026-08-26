import uuid
from app import create_app
from app.extensions import db
from app.models.m2_models import Ward, Bed

app = create_app()

def seed_m2_data():
    with app.app_context():
        # Check if wards already exist
        if Ward.query.count() > 0:
            print("ℹ️ Wards and beds already exist in the database.")
            return

        print("🌱 Seeding Member 2 Wards and Beds into Neon Database...")
        
        # 1. Create Wards
        icu_ward = Ward(id=uuid.uuid4(), name="Intensive Care Unit", ward_type="ICU")
        general_ward = Ward(id=uuid.uuid4(), name="General Ward A", ward_type="General")
        emergency_ward = Ward(id=uuid.uuid4(), name="Emergency Ward", ward_type="Emergency")
        
        db.session.add_all([icu_ward, general_ward, emergency_ward])
        db.session.flush()

        # 2. Create Beds
        beds = [
            # ICU Beds
            Bed(id=uuid.uuid4(), ward_id=icu_ward.id, bed_number="ICU-101", bed_type="ICU", status="AVAILABLE"),
            Bed(id=uuid.uuid4(), ward_id=icu_ward.id, bed_number="ICU-102", bed_type="ICU", status="AVAILABLE"),
            Bed(id=uuid.uuid4(), ward_id=icu_ward.id, bed_number="ICU-103", bed_type="ICU", status="AVAILABLE"),
            # General Beds
            Bed(id=uuid.uuid4(), ward_id=general_ward.id, bed_number="GEN-201", bed_type="Standard", status="AVAILABLE"),
            Bed(id=uuid.uuid4(), ward_id=general_ward.id, bed_number="GEN-202", bed_type="Standard", status="AVAILABLE"),
            Bed(id=uuid.uuid4(), ward_id=general_ward.id, bed_number="GEN-203", bed_type="Standard", status="AVAILABLE"),
            # Emergency Beds
            Bed(id=uuid.uuid4(), ward_id=emergency_ward.id, bed_number="EMG-001", bed_type="Critical Care", status="AVAILABLE"),
            Bed(id=uuid.uuid4(), ward_id=emergency_ward.id, bed_number="EMG-002", bed_type="Critical Care", status="AVAILABLE"),
        ]

        db.session.add_all(beds)
        db.session.commit()
        print(f"✅ Successfully seeded {len([icu_ward, general_ward, emergency_ward])} wards and {len(beds)} beds into Neon DB.")

if __name__ == "__main__":
    seed_m2_data()
