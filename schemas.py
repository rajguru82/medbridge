from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str                          # "patient" | "doctor"
    specialty: Optional[str] = None
    city: Optional[str] = None
    experience_years: Optional[int] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: str
    specialty: Optional[str] = None
    city: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str


# ── Doctors ───────────────────────────────────────────────────────────────
class DoctorInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    specialty: Optional[str] = None
    city: Optional[str] = None
    experience_years: Optional[int] = None


# ── Cases ─────────────────────────────────────────────────────────────────
class CaseCreate(BaseModel):
    symptoms: str
    age: int
    medical_history: Optional[str] = None
    current_medications: Optional[str] = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symptoms: str
    age: int
    medical_history: Optional[str] = None
    current_medications: Optional[str] = None
    ai_summary: Optional[str] = None
    specialist_type: Optional[str] = None
    status: str
    created_at: datetime


# ── Appointments ──────────────────────────────────────────────────────────
class AppointmentCreate(BaseModel):
    case_id: int
    doctor_id: int
    slot_datetime: str


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    doctor_id: int
    patient_id: int
    slot_datetime: str
    status: str
    doctor_response: Optional[str] = None
    created_at: datetime


class ConsultResponse(BaseModel):
    response: str
