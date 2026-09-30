"""Shared Pydantic request/response schemas.

Student schemas live here; Partner B adds Company/Job/Event schemas below.
"""
import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PHONE_RE = re.compile(r"^\+?[0-9\s\-().]{7,20}$")


def _clean_list(value) -> list[str] | None:
    """Accept a list or comma-separated string; return trimmed, de-duplicated list."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.split(",")
    seen, out = set(), []
    for item in value:
        item = str(item).strip()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            out.append(item)
    return out


# ---------- auth ----------
class StudentSignup(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    college_name: str = Field(min_length=1, max_length=200)

    @field_validator("name", "college_name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("password must contain at least one letter and one number")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password is too long (bcrypt limit is 72 bytes)")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


# ---------- student profile ----------
class StudentUpdate(BaseModel):
    """All fields optional; only the ones sent are updated."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    college_name: str | None = Field(default=None, min_length=1, max_length=200)
    date_of_birth: date | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    career_objective: str | None = Field(default=None, max_length=2000)
    degree: str | None = Field(default=None, max_length=100)
    major: str | None = Field(default=None, max_length=100)
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    cgpa: float | None = Field(default=None, ge=0.0, le=4.0)
    experience: str | None = Field(default=None, max_length=5000)
    phone: str | None = None
    skills: list[str] | None = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_in_past(cls, v):
        if v is not None and v >= date.today():
            raise ValueError("date of birth must be in the past")
        return v

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v):
        if v is not None and v != "" and not PHONE_RE.match(v):
            raise ValueError("invalid phone number")
        return v

    @field_validator("skills", mode="before")
    @classmethod
    def clean_skills(cls, v):
        return _clean_list(v)


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    college_name: str
    date_of_birth: date | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    career_objective: str | None = None
    degree: str | None = None
    major: str | None = None
    graduation_year: int | None = None
    cgpa: float | None = None
    experience: str | None = None
    phone: str | None = None
    skills: list[str] = []
    profile_picture_url: str | None = None
    created_at: datetime | None = None


class StudentSummary(BaseModel):
    """Lightweight row for browse/search lists."""

    id: int
    name: str
    college_name: str
    major: str | None = None
    graduation_year: int | None = None
    skills: list[str] = []
    profile_picture_url: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: StudentOut


class MessageResponse(BaseModel):
    message: str


# ---------- student preferences ----------
class PreferencesIn(BaseModel):
    preferred_categories: list[str] | None = None
    preferred_cities: list[str] | None = None
    preferred_skills: list[str] | None = None
    min_salary: int | None = Field(default=None, ge=0, le=1_000_000)
    remote_ok: bool | None = None
    event_interests: list[str] | None = None

    @field_validator(
        "preferred_categories",
        "preferred_cities",
        "preferred_skills",
        "event_interests",
        mode="before",
    )
    @classmethod
    def clean(cls, v):
        return _clean_list(v)

    @field_validator("preferred_categories")
    @classmethod
    def valid_categories(cls, v):
        allowed = {"full_time", "part_time", "on_campus", "internship"}
        if v:
            bad = [c for c in v if c not in allowed]
            if bad:
                raise ValueError(f"invalid categories {bad}; allowed: {sorted(allowed)}")
        return v


class PreferencesOut(BaseModel):
    preferred_categories: list[str] = []
    preferred_cities: list[str] = []
    preferred_skills: list[str] = []
    min_salary: int | None = None
    remote_ok: bool = False
    event_interests: list[str] = []
    saved: bool = False  # False when the student has never saved preferences
