from datetime import date, datetime, time

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    college = Column(String(200), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    career_objective = Column(Text, nullable=True)
    degree = Column(String(150), nullable=True)
    major = Column(String(150), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    cgpa = Column(Float, nullable=True)
    experience = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    skills = Column(Text, nullable=True)
    profile_picture = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    applications = relationship("Application", back_populates="student")
    registrations = relationship("EventRegistration", back_populates="student")
    preferences = relationship("StudentPreference", back_populates="student", uselist=False)
    saved_items = relationship("SavedItem", back_populates="student")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    location = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    contact_information = Column(String(500), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    jobs = relationship("Job", back_populates="company")
    events = relationship("Event", back_populates="company")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(200), nullable=False, index=True)
    posting_date = Column(Date, default=date.today, nullable=False)
    deadline = Column(Date, nullable=True, index=True)
    location = Column(String(150), nullable=False, index=True)
    salary = Column(Float, nullable=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    skills = Column(Text, nullable=True)
    remote = Column(Boolean, default=False, nullable=False)

    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    resume_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), default="Pending", nullable=False)

    student = relationship("Student", back_populates="applications")
    job = relationship("Job", back_populates="applications")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    event_time = Column(Time, nullable=True)
    location = Column(String(200), nullable=False)
    eligibility = Column(String(500), nullable=True)

    company = relationship("Company", back_populates="events")
    registrations = relationship("EventRegistration", back_populates="event")


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    event = relationship("Event", back_populates="registrations")
    student = relationship("Student", back_populates="registrations")


class StudentPreference(Base):
    __tablename__ = "student_preferences"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True, nullable=False)
    preferred_cities = Column(String(500), nullable=True)
    preferred_categories = Column(String(500), nullable=True)
    preferred_skills = Column(String(500), nullable=True)

    student = relationship("Student", back_populates="preferences")


class SavedItem(Base):
    __tablename__ = "saved_items"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    item_type = Column(String(20), nullable=False)
    item_id = Column(Integer, nullable=False)

    student = relationship("Student", back_populates="saved_items")
