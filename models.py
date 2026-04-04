from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)          # "patient" | "doctor"
    specialty = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    experience_years = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symptoms = Column(Text, nullable=False)
    age = Column(Integer, nullable=False)
    medical_history = Column(Text, nullable=True)
    current_medications = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    specialist_type = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")     # pending | scheduled | completed
    created_at = Column(DateTime, default=datetime.utcnow)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slot_datetime = Column(String(80), nullable=False)
    status = Column(String(20), default="scheduled")   # scheduled | completed
    doctor_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
