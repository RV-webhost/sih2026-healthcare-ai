import unittest
from datetime import date, time
from app import create_app
from app.extensions import db
from app.doctors.service import (
    create_doctor,
    create_doctor_schedule,
    create_doctor_leave,
    get_doctors,
)


class TestDoctorAvailability(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        # Seed sample active doctor
        self.doctor = create_doctor({
            "doctor_id": "doc-test-1",
            "name": "Dr. Sarah Connor",
            "department": "Pediatrics",
            "is_available": True
        })

        # Seed schedule for Monday (09:00 - 11:00, 30 min slots -> 4 slots)
        self.schedule = create_doctor_schedule({
            "doctor_id": self.doctor.doctor_id,
            "day_of_week": "Monday",
            "start_time": time(9, 0),
            "end_time": time(11, 0),
            "slot_duration": 30
        })

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_doctors_service(self):
        docs = get_doctors(department="pediat")
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].name, "Dr. Sarah Connor")

    def test_get_doctors_api(self):
        res = self.client.get("/api/v1/doctors?department=Pediatrics")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["name"], "Dr. Sarah Connor")

    def test_get_doctor_by_id_success(self):
        res = self.client.get(f"/api/v1/doctors/{self.doctor.doctor_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["name"], "Dr. Sarah Connor")

    def test_get_doctor_by_id_not_found(self):
        res = self.client.get("/api/v1/doctors/00000000-0000-0000-0000-000000000000")
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error_code"], "DOCTOR_NOT_FOUND")

    def test_get_doctor_schedule(self):
        res = self.client.get(f"/api/v1/doctors/{self.doctor.doctor_id}/schedule")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["day_of_week"], "Monday")
        self.assertEqual(data["data"][0]["start_time"], "09:00")
        self.assertEqual(data["data"][0]["end_time"], "11:00")

    def test_get_doctor_availability_success(self):
        # 2026-08-24 is a Monday
        res = self.client.get(f"/api/v1/doctors/{self.doctor.doctor_id}/availability?date=2026-08-24")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["data"]["available"])
        self.assertEqual(len(data["data"]["slots"]), 4)
        self.assertEqual(data["data"]["slots"][0]["time"], "09:00")
        self.assertTrue(data["data"]["slots"][0]["available"])
        self.assertEqual(data["data"]["slots"][3]["time"], "10:30")
        self.assertTrue(data["data"]["slots"][3]["available"])

    def test_get_doctor_availability_on_leave(self):
        tue_date = date(2026, 8, 25)
        create_doctor_leave({
            "doctor_id": self.doctor.doctor_id,
            "leave_date": tue_date,
            "reason": "Personal Leave"
        })
        res = self.client.get(f"/api/v1/doctors/{self.doctor.doctor_id}/availability?date=2026-08-25")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data["data"]["available"])
        self.assertEqual(data["error_code"], "DOCTOR_ON_LEAVE")

    def test_patient_cardiologist_search_and_availability(self):
        # 1. Create a dummy doctor with department="Cardiology" and is_available=True
        cardio_doc = create_doctor({
            "doctor_id": "doc-test-cardio",
            "name": "Dr. Elizabeth Heart",
            "department": "Cardiology",
            "is_available": True
        })

        # 2. Create working schedule on Monday from 10:00 to 12:00 with 30-min slots
        create_doctor_schedule({
            "doctor_id": cardio_doc.doctor_id,
            "day_of_week": "Monday",
            "start_time": time(10, 0),
            "end_time": time(12, 0),
            "slot_duration": 30
        })

        # 3. Call GET /api/v1/doctors?department=Cardiology
        search_res = self.client.get("/api/v1/doctors?department=Cardiology")
        self.assertEqual(search_res.status_code, 200)

        search_json = search_res.get_json()
        self.assertTrue(search_json["success"])

        cardio_doctors = [d for d in search_json["data"] if d["name"] == "Dr. Elizabeth Heart"]
        self.assertEqual(len(cardio_doctors), 1)

        # 4. Extract doctor_id from search response
        doctor_id = cardio_doctors[0]["doctor_id"]
        self.assertIsNotNone(doctor_id)

        # 5. Call GET /api/v1/doctors/{doctor_id}/availability?date=YYYY-MM-DD on a Monday
        monday_date = "2026-08-24"
        avail_res = self.client.get(f"/api/v1/doctors/{doctor_id}/availability?date={monday_date}")
        self.assertEqual(avail_res.status_code, 200)

        avail_json = avail_res.get_json()
        self.assertTrue(avail_json["success"])
        self.assertIsNotNone(avail_json["data"])
        self.assertEqual(avail_json["data"]["doctor_id"], doctor_id)
        self.assertTrue(avail_json["data"]["available"])

        slots = avail_json["data"]["slots"]
        self.assertEqual(len(slots), 4)
        self.assertEqual(slots[0]["time"], "10:00")
        self.assertTrue(slots[0]["available"])
        self.assertEqual(slots[3]["time"], "11:30")
        self.assertTrue(slots[3]["available"])

    def test_get_doctor_availability_missing_date(self):
        res = self.client.get(f"/api/v1/doctors/{self.doctor.doctor_id}/availability")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error_code"], "INVALID_DATE")

    def test_get_doctor_availability_invalid_date(self):
        res = self.client.get(f"/api/v1/doctors/{self.doctor.doctor_id}/availability?date=invalid-date")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error_code"], "INVALID_DATE")


if __name__ == "__main__":
    unittest.main()
