"""Student signup, sign in/out, profile, preferences, and browse routes.

Job search/apply and event registration are added here in Week 2.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import config
from app.auth import (
    create_access_token,
    get_current_student,
    get_token_claims,
    hash_password,
    revoke_token,
    verify_password,
)
from app.database import get_db
from app.models import Student, StudentPreference
from app.schemas import (
    LoginRequest,
    MessageResponse,
    PreferencesIn,
    PreferencesOut,
    StudentOut,
    StudentSignup,
    StudentSummary,
    StudentUpdate,
    TokenResponse,
)

router = APIRouter(prefix="/students", tags=["students"])

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
IMAGE_MAGIC = {
    ".jpg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".webp": (b"RIFF",),
}


# ---------- helpers ----------
def _split(text: str | None) -> list[str]:
    return [s.strip() for s in text.split(",") if s.strip()] if text else []


def _join(items: list[str] | None) -> str | None:
    return ", ".join(items) if items else None


def _picture_url(student: Student) -> str | None:
    return f"/uploads/{student.profile_picture}" if student.profile_picture else None


def to_student_out(s: Student) -> StudentOut:
    return StudentOut(
        id=s.id,
        name=s.name,
        email=s.email,
        college_name=s.college_name,
        date_of_birth=s.date_of_birth,
        city=s.city,
        state=s.state,
        country=s.country,
        career_objective=s.career_objective,
        degree=s.degree,
        major=s.major,
        graduation_year=s.graduation_year,
        cgpa=s.cgpa,
        experience=s.experience,
        phone=s.phone,
        skills=_split(s.skills),
        profile_picture_url=_picture_url(s),
        created_at=s.created_at,
    )


def to_summary(s: Student) -> StudentSummary:
    return StudentSummary(
        id=s.id,
        name=s.name,
        college_name=s.college_name,
        major=s.major,
        graduation_year=s.graduation_year,
        skills=_split(s.skills),
        profile_picture_url=_picture_url(s),
    )


# ---------- auth ----------
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: StudentSignup, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(Student).filter(Student.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    student = Student(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        college_name=payload.college_name,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return TokenResponse(
        access_token=create_access_token(student.id, "student"),
        role="student",
        user=to_student_out(student),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == payload.email.lower()).first()
    # Same error for unknown email and wrong password (no account enumeration)
    if student is None or not verify_password(payload.password, student.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return TokenResponse(
        access_token=create_access_token(student.id, "student"),
        role="student",
        user=to_student_out(student),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    claims: dict = Depends(get_token_claims),
    db: Session = Depends(get_db),
    _student: Student = Depends(get_current_student),
):
    revoke_token(db, claims["raw"])
    return MessageResponse(message="Signed out")


# ---------- own profile ----------
@router.get("/me", response_model=StudentOut)
def get_me(student: Student = Depends(get_current_student)):
    return to_student_out(student)


@router.put("/me", response_model=StudentOut)
def update_me(
    payload: StudentUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)

    # Required columns cannot be nulled out
    for required in ("name", "email", "college_name"):
        if required in data and data[required] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{required} cannot be empty")

    if "email" in data:
        data["email"] = str(data["email"]).lower()
        clash = (
            db.query(Student)
            .filter(Student.email == data["email"], Student.id != student.id)
            .first()
        )
        if clash:
            raise HTTPException(status.HTTP_409_CONFLICT, "That email is already in use")

    if "skills" in data:
        data["skills"] = _join(data["skills"])

    for field, value in data.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return to_student_out(student)


@router.post("/me/profile-picture", response_model=StudentOut)
async def upload_profile_picture(
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    ext = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Use a JPEG, PNG, or WebP image")
    content = await file.read(config.MAX_PROFILE_PIC_BYTES + 1)
    if len(content) > config.MAX_PROFILE_PIC_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image must be 2 MB or smaller")
    if not content.startswith(IMAGE_MAGIC[ext]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File contents do not match the image type")

    config.PROFILE_PIC_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"student_{student.id}_{uuid.uuid4().hex[:8]}{ext}"
    (config.PROFILE_PIC_DIR / filename).write_bytes(content)

    if student.profile_picture:  # remove the old picture
        old = config.UPLOAD_DIR / student.profile_picture
        if old.is_file():
            old.unlink()
    student.profile_picture = f"profile_pictures/{filename}"
    db.commit()
    db.refresh(student)
    return to_student_out(student)


# ---------- preferences (read by AI tool get_student_preferences) ----------
@router.get("/me/preferences", response_model=PreferencesOut)
def get_preferences(
    student: Student = Depends(get_current_student), db: Session = Depends(get_db)
):
    pref = db.query(StudentPreference).filter_by(student_id=student.id).first()
    if pref is None:
        return PreferencesOut(saved=False)
    return PreferencesOut(
        preferred_categories=_split(pref.preferred_categories),
        preferred_cities=_split(pref.preferred_cities),
        preferred_skills=_split(pref.preferred_skills),
        min_salary=pref.min_salary,
        remote_ok=pref.remote_ok,
        event_interests=_split(pref.event_interests),
        saved=True,
    )


@router.put("/me/preferences", response_model=PreferencesOut)
def update_preferences(
    payload: PreferencesIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    pref = db.query(StudentPreference).filter_by(student_id=student.id).first()
    if pref is None:
        pref = StudentPreference(student_id=student.id)
        db.add(pref)
    data = payload.model_dump(exclude_unset=True)
    for field in ("preferred_categories", "preferred_cities", "preferred_skills", "event_interests"):
        if field in data:
            data[field] = _join(data[field])
    for field, value in data.items():
        setattr(pref, field, value)
    db.commit()
    return get_preferences(student, db)


# ---------- browse students (any signed-in user) ----------
@router.get("", response_model=list[StudentSummary])
def list_students(
    name: str | None = Query(default=None, max_length=100),
    college: str | None = Query(default=None, max_length=200),
    major: str | None = Query(default=None, max_length=100),
    skill: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _claims: dict = Depends(get_token_claims),
    db: Session = Depends(get_db),
):
    q = db.query(Student)
    if name:
        q = q.filter(Student.name.ilike(f"%{name}%"))
    if college:
        q = q.filter(Student.college_name.ilike(f"%{college}%"))
    if major:
        q = q.filter(Student.major.ilike(f"%{major}%"))
    if skill:
        q = q.filter(Student.skills.ilike(f"%{skill}%"))
    rows = q.order_by(Student.name).offset(offset).limit(limit).all()
    return [to_summary(s) for s in rows]


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    _claims: dict = Depends(get_token_claims),
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return to_student_out(student)
