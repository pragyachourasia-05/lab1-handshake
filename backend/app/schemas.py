from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


class StudentSignup(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    college: str = Field(min_length=2, max_length=200)


class CompanySignup(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    location: str = Field(min_length=2, max_length=200)


class StudentProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    date_of_birth: Optional[date] = None
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    career_objective: Optional[str] = None
    college: Optional[str] = Field(default=None, max_length=200)
    degree: Optional[str] = Field(default=None, max_length=150)
    major: Optional[str] = Field(default=None, max_length=150)
    graduation_year: Optional[int] = Field(default=None, ge=1950, le=2200)
    cgpa: Optional[float] = Field(default=None, ge=0, le=10)
    experience: Optional[str] = None
    email: Optional[str] = Field(default=None, min_length=5, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    skills: Optional[str] = None
    profile_picture: Optional[str] = Field(default=None, max_length=500)


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    college: str
    date_of_birth: Optional[date] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    career_objective: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    cgpa: Optional[float] = None
    experience: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[str] = None
    profile_picture: Optional[str] = None


class StudentDirectoryResponse(BaseModel):
    id: int
    name: str
    college: str
    major: Optional[str] = None
    city: Optional[str] = None
    skills: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    title: str
    company_id: int
    company_name: str
    company_location: Optional[str] = None
    location: str
    category: str
    salary: Optional[float] = None
    deadline: Optional[date] = None
    posting_date: date
    description: str
    skills: Optional[str] = None
    remote: bool


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    job_title: str
    company_name: str
    applied_at: datetime
    status: str
    original_filename: str


class EventResponse(BaseModel):
    id: int
    name: str
    description: str
    event_date: date
    event_time: Optional[time] = None
    location: str
    eligibility: Optional[str] = None
    company_id: int
    company_name: str


class RegistrationResponse(BaseModel):
    id: int
    event_id: int
    event_name: str
    event_date: date
    registered_at: datetime
