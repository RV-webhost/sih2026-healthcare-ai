from dataclasses import dataclass
from typing import Optional
from app.auth.models import UserRole, Gender

@dataclass
class RegisterRequest:
    name: str
    email: str
    password: str
    phone: Optional[str] = None

@dataclass
class LoginRequest:
    email: str
    password: str

@dataclass
class PatientProfileUpdate:
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[str] = None