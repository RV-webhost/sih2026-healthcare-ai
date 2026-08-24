from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.auth.models import UserRole, Gender

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PatientProfileUpdate(BaseModel):
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[str] = None