from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.schemas import RegisterRequest, LoginRequest, PatientProfileUpdate
from app.auth.service import register_user, authenticate_user, get_patient_profile, update_patient_profile
from app.auth.deps import get_current_user

router = APIRouter(prefix="/api", tags=["Auth & Patient"])

@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    result = register_user(db, payload)
    return {"success": True, "data": result, "message": "Registration successful."}

@router.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    result = authenticate_user(db, payload)
    return {"success": True, "data": result, "message": "Login successful."}

@router.get("/patients/me")
def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "data": get_patient_profile(db, current_user["user_id"])}

@router.patch("/patients/me")
def update_profile(payload: PatientProfileUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "data": update_patient_profile(db, current_user["user_id"], payload)}