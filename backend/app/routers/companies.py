"""Company authentication is shared; company business routes belong to the partner."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import create_access_token, hash_password, require_company, verify_password
from ..database import get_db
from ..models import Company, Student
from ..schemas import CompanySignup, LoginRequest, TokenResponse

router = APIRouter(tags=["companies"])


@router.post("/auth/company/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def company_signup(payload: CompanySignup, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.scalar(select(Student).where(Student.email == email)) or db.scalar(select(Company).where(Company.email == email)):
        raise HTTPException(status_code=409, detail="This email is already registered")
    company = Company(name=payload.name.strip(), email=email, hashed_password=hash_password(payload.password), location=payload.location.strip())
    db.add(company)
    try:
        db.commit()
        db.refresh(company)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This email is already registered")
    return TokenResponse(access_token=create_access_token(company.id, "company"), role="company", user_id=company.id)


@router.post("/auth/company/login", response_model=TokenResponse)
def company_login(payload: LoginRequest, db: Session = Depends(get_db)):
    company = db.scalar(select(Company).where(Company.email == payload.email.lower().strip()))
    if not company or not verify_password(payload.password, company.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return TokenResponse(access_token=create_access_token(company.id, "company"), role="company", user_id=company.id)


@router.get("/companies/me")
def get_company_profile(identity: dict = Depends(require_company)):
    company = identity["user"]
    return {"id": company.id, "name": company.name, "email": company.email, "location": company.location, "description": company.description, "contact_information": company.contact_information, "profile_picture": company.profile_picture}
