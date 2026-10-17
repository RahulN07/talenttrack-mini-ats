
import os
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from sqlmodel import Field, Session, SQLModel, create_engine, select


# -----------------------------
# Database configuration
# -----------------------------

# Load .env from the same directory as this file.
load_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Add it to your backend/.env file."
    )

# Keep SQLite support if you ever choose to use it again.
connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# -----------------------------
# Hiring stages
# -----------------------------

class HiringStage(str, Enum):
    APPLIED = "Applied"
    SCREENING = "Screening"
    INTERVIEWING = "Interviewing"
    OFFER = "Offer"
    HIRED = "Hired"
    REJECTED = "Rejected"


# -----------------------------
# Database and API models
# -----------------------------

class CandidateBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(index=True, max_length=254)
    role: str = Field(min_length=1, max_length=100)
    stage: HiringStage = Field(default=HiringStage.APPLIED)


class Candidate(CandidateBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class CandidateCreate(CandidateBase):
    email: EmailStr


class CandidateUpdate(CandidateBase):
    email: EmailStr


# -----------------------------
# FastAPI application
# -----------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Mini ATS API",
    description="Applicant Tracking System for managing candidates",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Basic endpoints
# -----------------------------

@app.get("/")
def home():
    return {"message": "Welcome to Mini ATS API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# -----------------------------
# List, search and filter
# -----------------------------

@app.get("/candidates", response_model=list[Candidate])
def get_candidates(
    search: str = Query(default=""),
    stage: HiringStage | None = None,
    session: Session = Depends(get_session),
):
    statement = select(Candidate)

    if search.strip():
        term = f"%{search.strip()}%"
        statement = statement.where(
            Candidate.name.ilike(term)
            | Candidate.email.ilike(term)
            | Candidate.role.ilike(term)
        )

    if stage is not None:
        statement = statement.where(Candidate.stage == stage)

    statement = statement.order_by(Candidate.id.desc())

    return session.exec(statement).all()


# -----------------------------
# Create candidate
# -----------------------------

@app.post(
    "/candidates",
    response_model=Candidate,
    status_code=201,
)
def create_candidate(
    data: CandidateCreate,
    session: Session = Depends(get_session),
):
    email = str(data.email).strip().lower()

    existing = session.exec(
        select(Candidate).where(Candidate.email == email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A candidate with this email already exists.",
        )

    candidate = Candidate(
        name=data.name.strip(),
        email=email,
        role=data.role.strip(),
        stage=data.stage,
    )

    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    return candidate


# -----------------------------
# Get one candidate
# -----------------------------

@app.get("/candidates/{candidate_id}", response_model=Candidate)
def get_candidate(
    candidate_id: int,
    session: Session = Depends(get_session),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    return candidate


# -----------------------------
# Update candidate
# -----------------------------

@app.put("/candidates/{candidate_id}", response_model=Candidate)
def update_candidate(
    candidate_id: int,
    data: CandidateUpdate,
    session: Session = Depends(get_session),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    email = str(data.email).strip().lower()

    existing = session.exec(
        select(Candidate).where(Candidate.email == email)
    ).first()

    if existing is not None and existing.id != candidate_id:
        raise HTTPException(
            status_code=409,
            detail="That email belongs to another candidate.",
        )

    candidate.name = data.name.strip()
    candidate.email = email
    candidate.role = data.role.strip()
    candidate.stage = data.stage

    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    return candidate


# -----------------------------
# Delete candidate
# -----------------------------

@app.delete("/candidates/{candidate_id}")
def delete_candidate(
    candidate_id: int,
    session: Session = Depends(get_session),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    session.delete(candidate)
    session.commit()

    return {"message": "Candidate deleted successfully."}


# -----------------------------
# Dashboard statistics
# -----------------------------

@app.get("/dashboard")
def dashboard(session: Session = Depends(get_session)):
    all_candidates = session.exec(select(Candidate)).all()

    stage_counts = {
        stage.value: sum(
            1 for candidate in all_candidates
            if candidate.stage == stage
        )
        for stage in HiringStage
    }

    return {
        "total_candidates": len(all_candidates),
        "stage_counts": stage_counts,
    }
