from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_identity, hash_password, require_student, verify_password
from ..database import get_db
from ..models import Company, Student, StudentPreference
from ..schemas import LoginRequest, StudentDirectoryResponse, StudentProfileResponse, StudentProfileUpdate, StudentSignup, TokenResponse

router = APIRouter(tags=["students"])


@router.post("/auth/student/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def student_signup(payload: StudentSignup, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.scalar(select(Student).where(Student.email == email)) or db.scalar(select(Company).where(Company.email == email)):
        raise HTTPException(status_code=409, detail="This email is already registered")
    student = Student(name=payload.name.strip(), email=email, hashed_password=hash_password(payload.password), college=payload.college.strip())
    db.add(student)
    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This email is already registered")
    return TokenResponse(access_token=create_access_token(student.id, "student"), role="student", user_id=student.id)


@router.post("/auth/student/login", response_model=TokenResponse)
def student_login(payload: LoginRequest, db: Session = Depends(get_db)):
    student = db.scalar(select(Student).where(Student.email == payload.email.lower().strip()))
    if not student or not verify_password(payload.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return TokenResponse(access_token=create_access_token(student.id, "student"), role="student", user_id=student.id)


@router.post("/auth/logout")
def logout(_: dict = Depends(get_current_identity)):
    return {"message": "Signed out. Remove the bearer token from the client."}


@router.get("/students/me", response_model=StudentProfileResponse)
def get_my_profile(identity: dict = Depends(require_student)):
    return identity["user"]


@router.patch("/students/me", response_model=StudentProfileResponse)
def update_my_profile(payload: StudentProfileUpdate, identity: dict = Depends(require_student), db: Session = Depends(get_db)):
    student = identity["user"]
    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates:
        new_email = updates["email"].lower().strip()
        if db.scalar(select(Student).where(Student.email == new_email, Student.id != student.id)) or db.scalar(select(Company).where(Company.email == new_email)):
            raise HTTPException(status_code=409, detail="This email is already registered")
        updates["email"] = new_email
    for field, value in updates.items():
        setattr(student, field, value.strip() if isinstance(value, str) else value)
    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not update the profile")
    return student


@router.get("/students", response_model=list[StudentDirectoryResponse])
def search_students(
    name: str | None = Query(default=None),
    college: str | None = Query(default=None),
    major: str | None = Query(default=None),
    _: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    query = select(Student)
    if name:
        query = query.where(Student.name.ilike(f"%{name.strip()}%"))
    if college:
        query = query.where(Student.college.ilike(f"%{college.strip()}%"))
    if major:
        query = query.where(Student.major.ilike(f"%{major.strip()}%"))
    return list(db.scalars(query.order_by(Student.name)).all())


@router.get("/students/{student_id}", response_model=StudentDirectoryResponse)
def get_student_profile(student_id: int, _: dict = Depends(require_student), db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/students/me/preferences")
def get_preferences(identity: dict = Depends(require_student), db: Session = Depends(get_db)):
    preference = db.scalar(select(StudentPreference).where(StudentPreference.student_id == identity["user_id"]))
    if not preference:
        return {"message": "No preferences saved", "preferred_cities": [], "preferred_categories": [], "preferred_skills": []}
    return {
        "preferred_cities": [value for value in (preference.preferred_cities or "").split(",") if value],
        "preferred_categories": [value for value in (preference.preferred_categories or "").split(",") if value],
        "preferred_skills": [value for value in (preference.preferred_skills or "").split(",") if value],
    }
