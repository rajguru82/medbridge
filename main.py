from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
import anthropic
import json
import os

from database import get_db, engine
import models
import schemas
import auth

# ── DB init ────────────────────────────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedBridge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Seed doctors ───────────────────────────────────────────────────────────
SEED_DOCTORS = [
    {"name": "Dr. Priya Sharma",  "email": "priya.sharma@medbridge.com",  "specialty": "Cardiologist",       "city": "Mumbai",    "exp": 14},
    {"name": "Dr. Rahul Mehta",   "email": "rahul.mehta@medbridge.com",   "specialty": "Neurologist",        "city": "Delhi",     "exp": 11},
    {"name": "Dr. Sunita Patel",  "email": "sunita.patel@medbridge.com",  "specialty": "Oncologist",         "city": "Bangalore", "exp": 16},
    {"name": "Dr. Arun Kumar",    "email": "arun.kumar@medbridge.com",    "specialty": "Orthopedic",         "city": "Hyderabad", "exp": 9},
    {"name": "Dr. Meena Joshi",   "email": "meena.joshi@medbridge.com",   "specialty": "Gastroenterologist", "city": "Chennai",   "exp": 12},
    {"name": "Dr. Vikram Singh",  "email": "vikram.singh@medbridge.com",  "specialty": "Pulmonologist",      "city": "Kolkata",   "exp": 8},
    {"name": "Dr. Anita Desai",   "email": "anita.desai@medbridge.com",   "specialty": "Endocrinologist",    "city": "Pune",      "exp": 10},
    {"name": "Dr. Rajesh Nair",   "email": "rajesh.nair@medbridge.com",   "specialty": "Cardiologist",       "city": "Bangalore", "exp": 18},
    {"name": "Dr. Pooja Gupta",   "email": "pooja.gupta@medbridge.com",   "specialty": "Neurologist",        "city": "Mumbai",    "exp": 7},
    {"name": "Dr. Sanjay Reddy",  "email": "sanjay.reddy@medbridge.com",  "specialty": "Oncologist",         "city": "Delhi",     "exp": 13},
]


@app.on_event("startup")
def seed_database():
    db = next(get_db())
    try:
        for doc in SEED_DOCTORS:
            exists = db.query(models.User).filter(models.User.email == doc["email"]).first()
            if not exists:
                db.add(models.User(
                    email=doc["email"],
                    name=doc["name"],
                    password_hash=auth.hash_password("doctor123"),
                    role="doctor",
                    specialty=doc["specialty"],
                    city=doc["city"],
                    experience_years=doc["exp"],
                ))
        db.commit()
    finally:
        db.close()


# ── Auth ───────────────────────────────────────────────────────────────────
@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(400, "Email already registered")
    if user.role not in ("patient", "doctor"):
        raise HTTPException(400, "Role must be 'patient' or 'doctor'")

    db_user = models.User(
        email=user.email,
        name=user.name,
        password_hash=auth.hash_password(user.password),
        role=user.role,
        specialty=user.specialty,
        city=user.city,
        experience_years=user.experience_years,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "name": user.name}


@app.get("/api/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# ── Patient routes ─────────────────────────────────────────────────────────
@app.post("/api/cases", response_model=schemas.CaseResponse)
def create_case(
    case: schemas.CaseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(403, "Only patients can submit cases")

    ai_summary, specialist_type = _generate_ai_summary(case)

    db_case = models.Case(
        patient_id=current_user.id,
        symptoms=case.symptoms,
        age=case.age,
        medical_history=case.medical_history,
        current_medications=case.current_medications,
        ai_summary=ai_summary,
        specialist_type=specialist_type,
        status="pending",
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


@app.get("/api/cases/my", response_model=List[schemas.CaseResponse])
def get_my_cases(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.Case)
        .filter(models.Case.patient_id == current_user.id)
        .order_by(models.Case.created_at.desc())
        .all()
    )


@app.get("/api/doctors", response_model=List[schemas.DoctorInfo])
def get_doctors(
    specialty: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    q = db.query(models.User).filter(models.User.role == "doctor")
    if specialty:
        q = q.filter(models.User.specialty.ilike(f"%{specialty}%"))
    return q.all()


@app.post("/api/appointments", response_model=schemas.AppointmentResponse)
def book_appointment(
    appt: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(403, "Only patients can book appointments")

    case = db.query(models.Case).filter(
        models.Case.id == appt.case_id,
        models.Case.patient_id == current_user.id,
    ).first()
    if not case:
        raise HTTPException(404, "Case not found")

    doctor = db.query(models.User).filter(
        models.User.id == appt.doctor_id,
        models.User.role == "doctor",
    ).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")

    db_appt = models.Appointment(
        case_id=appt.case_id,
        doctor_id=appt.doctor_id,
        patient_id=current_user.id,
        slot_datetime=appt.slot_datetime,
        status="scheduled",
    )
    db.add(db_appt)
    case.status = "scheduled"
    db.commit()
    db.refresh(db_appt)
    return db_appt


@app.get("/api/appointments/my", response_model=List[schemas.AppointmentResponse])
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role == "patient":
        return (
            db.query(models.Appointment)
            .filter(models.Appointment.patient_id == current_user.id)
            .order_by(models.Appointment.created_at.desc())
            .all()
        )
    return (
        db.query(models.Appointment)
        .filter(models.Appointment.doctor_id == current_user.id)
        .order_by(models.Appointment.created_at.desc())
        .all()
    )


# ── Doctor routes ──────────────────────────────────────────────────────────
@app.get("/api/doctor/queue")
def get_doctor_queue(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "doctor":
        raise HTTPException(403, "Doctors only")

    appointments = (
        db.query(models.Appointment)
        .filter(models.Appointment.doctor_id == current_user.id)
        .order_by(models.Appointment.created_at.desc())
        .all()
    )

    result = []
    for appt in appointments:
        case = db.query(models.Case).filter(models.Case.id == appt.case_id).first()
        patient = db.query(models.User).filter(models.User.id == appt.patient_id).first()
        if case and patient:
            result.append({
                "appointment_id": appt.id,
                "patient_name": patient.name,
                "patient_city": patient.city or "Not specified",
                "slot_datetime": appt.slot_datetime,
                "status": appt.status,
                "doctor_response": appt.doctor_response,
                "case_id": case.id,
                "symptoms": case.symptoms,
                "age": case.age,
                "medical_history": case.medical_history or "None reported",
                "current_medications": case.current_medications or "None",
                "ai_summary": case.ai_summary or "No AI summary available.",
                "specialist_type": case.specialist_type or "General Physician",
                "case_created": case.created_at.isoformat(),
            })
    return result


@app.put("/api/appointments/{appt_id}/respond")
def respond_to_case(
    appt_id: int,
    body: schemas.ConsultResponse,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "doctor":
        raise HTTPException(403, "Doctors only")

    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appt_id,
        models.Appointment.doctor_id == current_user.id,
    ).first()
    if not appt:
        raise HTTPException(404, "Appointment not found")

    appt.doctor_response = body.response
    appt.status = "completed"

    case = db.query(models.Case).filter(models.Case.id == appt.case_id).first()
    if case:
        case.status = "completed"

    db.commit()
    return {"message": "Response submitted successfully"}


# ── AI helper ──────────────────────────────────────────────────────────────
def _generate_ai_summary(case: schemas.CaseCreate):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_summary(case), "General Physician"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            "You are a medical triage AI assisting doctors in Indian tier-2/3 cities.\n\n"
            "Analyze the patient info below and respond ONLY with a valid JSON object — "
            "no markdown fences, no extra text.\n\n"
            f"Patient Age: {case.age}\n"
            f"Symptoms: {case.symptoms}\n"
            f"Medical History: {case.medical_history or 'None'}\n"
            f"Current Medications: {case.current_medications or 'None'}\n\n"
            "JSON format:\n"
            "{\n"
            '  "summary": "2-3 sentence clinical brief for specialist review",\n'
            '  "specialist_type": "One of: Cardiologist, Neurologist, Oncologist, '
            "Orthopedic, Gastroenterologist, Pulmonologist, Endocrinologist, General Physician\"\n"
            "}"
        )

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        content = msg.content[0].text.strip()

        # Strip accidental markdown fences
        if "```" in content:
            for chunk in content.split("```"):
                chunk = chunk.strip().lstrip("json").strip()
                if chunk.startswith("{"):
                    content = chunk
                    break

        data = json.loads(content)
        return (
            data.get("summary", _fallback_summary(case)),
            data.get("specialist_type", "General Physician"),
        )
    except Exception:
        return _fallback_summary(case), "General Physician"


def _fallback_summary(case: schemas.CaseCreate) -> str:
    return (
        f"{case.age}-year-old patient presenting with: {case.symptoms}. "
        f"Medical history: {case.medical_history or 'None reported'}. "
        f"Current medications: {case.current_medications or 'None'}. "
        "Awaiting specialist evaluation."
    )


# ── Static files ───────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


@app.get("/patient")
def serve_patient():
    return FileResponse("static/patient.html")


@app.get("/doctor")
def serve_doctor():
    return FileResponse("static/doctor.html")
