# 🏥 MedBridge

**AI-powered specialist matching and teleconsultation platform for tier 2/3 cities in India.**

Built with FastAPI · Anthropic Claude API · SQLite · Vanilla JS

---

## Features

- **AI Case Triage** — Patients describe symptoms; Claude API generates a structured clinical brief and recommends the right specialist type
- **Specialist Directory** — Filter 10+ pre-loaded specialists by specialty
- **Appointment Booking** — Pick available time slots and book against a specific case
- **Doctor Dashboard** — Doctors view their case queue with AI summaries and submit consultation responses
- **JWT Auth** — Separate patient and doctor roles

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI |
| Database | SQLite (auto-created) |
| AI | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| Auth | JWT via python-jose |
| Frontend | Vanilla HTML/CSS/JS |
| Deploy | Render.com |

---

## Local Development

```bash
# 1. Clone
git clone https://github.com/yourusername/medbridge
cd medbridge

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 5. Run
uvicorn main:app --reload
```

Open http://localhost:8000

---

## Deploy to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service → connect repo
3. Render auto-detects `render.yaml`
4. Add environment variable: `ANTHROPIC_API_KEY = your_key`
5. Deploy ✅

---

## Demo Credentials

**Patients:** Register a new account on the landing page.

**Doctors (pre-seeded):**
| Email | Password | Specialty |
|---|---|---|
| priya.sharma@medbridge.com | doctor123 | Cardiologist |
| rahul.mehta@medbridge.com | doctor123 | Neurologist |
| sunita.patel@medbridge.com | doctor123 | Oncologist |
| arun.kumar@medbridge.com | doctor123 | Orthopedic |

*All 10 doctors use password: `doctor123`*

---

## Project Structure

```
medbridge/
├── main.py          # FastAPI app + all routes
├── database.py      # SQLAlchemy setup
├── models.py        # DB models (User, Case, Appointment)
├── schemas.py       # Pydantic schemas
├── auth.py          # JWT authentication
├── requirements.txt
├── render.yaml      # Render deployment config
└── static/
    ├── index.html   # Login / Register
    ├── patient.html # Patient dashboard
    └── doctor.html  # Doctor dashboard
```

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login → JWT token |
| GET | /api/me | Get current user |
| POST | /api/cases | Submit case (AI analysis) |
| GET | /api/cases/my | Get patient's cases |
| GET | /api/doctors | List/filter doctors |
| POST | /api/appointments | Book appointment |
| GET | /api/appointments/my | Get appointments |
| GET | /api/doctor/queue | Doctor's case queue |
| PUT | /api/appointments/{id}/respond | Doctor submits response |

Interactive docs: `http://localhost:8000/docs`
