
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from sqlalchemy import func
from sqlmodel import Field, Session, SQLModel, create_engine, select


# --------------------------------------------------
# 1. Load environment variables
# --------------------------------------------------

load_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Check your backend/.env file."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# --------------------------------------------------
# 2. Hiring stage choices
# --------------------------------------------------

class HiringStage(str, Enum):
    APPLIED = "Applied"
    SCREENING = "Screening"
    INTERVIEWING = "Interviewing"
    OFFER = "Offer"
    HIRED = "Hired"
    REJECTED = "Rejected"


# --------------------------------------------------
# 3. Candidate schemas and database model
# --------------------------------------------------

class CandidateBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(index=True, max_length=254)
    role: str = Field(min_length=1, max_length=100)
    stage: HiringStage = Field(default=HiringStage.APPLIED)


class Candidate(CandidateBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={
            "onupdate": lambda: datetime.now(timezone.utc)
        },
    )


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    role: str | None = Field(default=None, min_length=1, max_length=100)
    stage: HiringStage | None = None


# --------------------------------------------------
# 4. Database session
# --------------------------------------------------

def get_session():
    with Session(engine) as session:
        yield session


# --------------------------------------------------
# 5. Application startup
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alembic manages database schema changes.
    # Apply migrations before starting the application.
    yield


app = FastAPI(
    title="TalentTrack Mini ATS",
    description="A simple Applicant Tracking System API",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# 6. CORS configuration
# --------------------------------------------------

FRONTEND_URL = os.getenv("FRONTEND_URL", "").rstrip("/")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://talenttrack-mini-ats.vercel.app",
]

if FRONTEND_URL and FRONTEND_URL not in allowed_origins:
    allowed_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# 7. Health check
# --------------------------------------------------

@app.get("/")
def read_root():
    return {
        "message": "Welcome to TalentTrack Mini ATS API",
        "docs": "/docs",
    }


@app.get("/health")
def health_check(session: Session = Depends(get_session)):
    try:
        session.exec(select(1)).first()
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from exc


# --------------------------------------------------
# 8. List, search, and filter candidates
# --------------------------------------------------

@app.get("/candidates", response_model=list[Candidate])
def get_candidates(
    search: str | None = Query(default=None),
    stage: HiringStage | None = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(Candidate)

    if search:
        search_term = f"%{search.strip()}%"
        statement = statement.where(
            Candidate.name.ilike(search_term)
            | Candidate.email.ilike(search_term)
            | Candidate.role.ilike(search_term)
        )

    if stage:
        statement = statement.where(Candidate.stage == stage)

    statement = statement.order_by(Candidate.id.desc())

    return session.exec(statement).all()


# --------------------------------------------------
# 9. Create a candidate
# --------------------------------------------------

@app.post("/candidates", response_model=Candidate, status_code=201)
def create_candidate(
    candidate_data: CandidateCreate,
    session: Session = Depends(get_session),
):
    email = str(candidate_data.email).lower()

    existing_candidate = session.exec(
        select(Candidate).where(Candidate.email == email)
    ).first()

    if existing_candidate:
        raise HTTPException(
            status_code=409,
            detail="A candidate with this email already exists",
        )

    candidate = Candidate.model_validate(
        candidate_data,
        update={
            "email": email,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    )

    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    return candidate


# --------------------------------------------------
# 10. Get one candidate
# --------------------------------------------------

@app.get("/candidates/{candidate_id}", response_model=Candidate)
def get_candidate(
    candidate_id: int,
    session: Session = Depends(get_session),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    return candidate


# --------------------------------------------------
# 11. Update a candidate
# --------------------------------------------------

@app.put("/candidates/{candidate_id}", response_model=Candidate)
def update_candidate(
    candidate_id: int,
    candidate_data: CandidateUpdate,
    session: Session = Depends(get_session),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    update_data = candidate_data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = str(update_data["email"]).lower()

        duplicate = session.exec(
            select(Candidate).where(
                Candidate.email == update_data["email"],
                Candidate.id != candidate_id,
            )
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Another candidate already uses this email",
            )

    for field, value in update_data.items():
        setattr(candidate, field, value)

    candidate.updated_at = datetime.now(timezone.utc)

    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    return candidate


# --------------------------------------------------
# 12. Delete a candidate
# --------------------------------------------------

@app.delete("/candidates/{candidate_id}")
def delete_candidate(
    candidate_id: int,
    session: Session = Depends(get_session),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    session.delete(candidate)
    session.commit()

    return {
        "message": "Candidate deleted successfully",
        "candidate_id": candidate_id,
    }


# --------------------------------------------------
# 13. Dashboard statistics
# --------------------------------------------------

@app.get("/dashboard")
def get_dashboard(session: Session = Depends(get_session)):
    total_candidates = session.exec(
        select(func.count()).select_from(Candidate)
    ).one()

    stage_counts = {}

    for hiring_stage in HiringStage:
        count = session.exec(
            select(func.count())
            .select_from(Candidate)
            .where(Candidate.stage == hiring_stage)
        ).one()

        stage_counts[hiring_stage.value] = count

    return {
        "total_candidates": total_candidates,
        "stage_counts": stage_counts,
    }
