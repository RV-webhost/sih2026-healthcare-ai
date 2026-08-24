from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.auth.models import User, Patient, UserRole
from app.auth.schemas import RegisterRequest, LoginRequest, PatientProfileUpdate
from app.auth.utils import hash_password, verify_password, create_access_token

def register_user(db: Session, payload: RegisterRequest):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail={"success": False, "message": "Email already exists."})
    
    user = User(email=payload.email, password_hash=hash_password(payload.password), role=UserRole.PATIENT)
    db.add(user)
    db.commit()
    db.refresh(user)

    patient = Patient(user_id=user.id, full_name=payload.name, phone=payload.phone)
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return {"user_id": str(user.id), "patient_id": str(patient.id), "name": patient.full_name, "email": user.email, "role": user.role}

def authenticate_user(db: Session, payload: LoginRequest):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail={"success": False, "message": "Invalid credentials."})
    
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    patient_id = str(patient.id) if patient else None

    token = create_access_token({"sub": user.email, "user_id": str(user.id), "patient_id": patient_id, "role": user.role.value})
    
    return {"user": {"user_id": str(user.id), "patient_id": patient_id, "name": patient.full_name if patient else "", "role": user.role}, "access_token": token}

def get_patient_profile(db: Session, user_id: str):
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    user = db.query(User).filter(User.id == user_id).first()
    return {"patient_id": str(patient.id), "name": patient.full_name, "email": user.email, "phone": patient.phone, "date_of_birth": patient.date_of_birth, "gender": patient.gender}

def update_patient_profile(db: Session, user_id: str, payload: PatientProfileUpdate):
    patient = db.query(Patient).filter(Patient.user_id == user_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    update_data = payload.model_dump(exclude_unset=True) 
    for key, value in update_data.items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return get_patient_profile(db, user_id)