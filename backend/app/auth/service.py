from sqlalchemy.orm import Session
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
from app.auth.models import User, Patient, UserRole
from app.auth.utils import hash_password, verify_password, create_access_token

def register_user(db: Session, payload: dict):
    # Dictionary lookup instead of Pydantic dot notation
    if db.query(User).filter(User.email == payload.get("email")).first():
        # Using Werkzeug exceptions which are standard for Flask
        raise BadRequest("Email already exists.")
    
    user = User(
        email=payload.get("email"), 
        password_hash=hash_password(payload.get("password")), 
        role=UserRole.PATIENT
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    patient = Patient(
        user_id=user.id, 
        full_name=payload.get("name"), 
        phone=payload.get("phone")
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return {
        "user_id": str(user.id), 
        "patient_id": str(patient.id), 
        "name": patient.full_name, 
        "email": user.email, 
        "role": user.role.value if hasattr(user.role, 'value') else user.role
    }

def authenticate_user(db: Session, payload: dict):
    user = db.query(User).filter(User.email == payload.get("email")).first()
    if not user or not verify_password(payload.get("password"), user.password_hash):
        raise Unauthorized("Invalid credentials.")
    
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    patient_id = str(patient.id) if patient else None

    token = create_access_token({
        "sub": user.email, 
        "user_id": str(user.id), 
        "patient_id": patient_id, 
        "role": user.role.value if hasattr(user.role, 'value') else user.role
    })
    
    return {
        "user": {
            "user_id": str(user.id), 
            "patient_id": patient_id, 
            "name": patient.full_name if patient else "", 
            "role": user.role.value if hasattr(user.role, 'value') else user.role
        }, 
        "access_token": token
    }

def get_patient_profile(db: Session, user_id: str):
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        raise NotFound("Patient not found")
    user = db.query(User).filter(User.id == user_id).first()
    
    return {
        "patient_id": str(patient.id), 
        "name": patient.full_name, 
        "email": user.email, 
        "phone": patient.phone, 
        "date_of_birth": patient.date_of_birth, 
        "gender": patient.gender
    }

def update_patient_profile(db: Session, user_id: str, payload: dict):
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        raise NotFound("Patient not found")
    
    # Removed Pydantic's .model_dump() and replaced with standard dictionary iteration
    for key, value in payload.items():
        # Safety check to prevent overwriting critical IDs
        if key not in ['id', 'user_id', 'created_at']:
            setattr(patient, key, value)
            
    db.commit()
    db.refresh(patient)
    return get_patient_profile(db, user_id)