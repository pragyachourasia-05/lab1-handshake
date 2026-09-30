from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..auth import require_student
from ..database import get_db
from ..models import Company, Job
from ..schemas import JobResponse

router = APIRouter(tags=["student jobs"])


def job_response(job: Job) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "company_id": job.company_id,
        "company_name": job.company.name,
        "company_location": job.company.location,
        "location": job.location,
        "category": job.category,
        "salary": job.salary,
        "deadline": job.deadline,
        "posting_date": job.posting_date,
        "description": job.description,
        "skills": job.skills,
        "remote": job.remote,
    }


@router.get("/jobs", response_model=list[JobResponse])
def search_jobs(
    company: str | None = Query(default=None),
    title: str | None = Query(default=None),
    category: str | None = Query(default=None),
    city: str | None = Query(default=None),
    min_salary: float | None = Query(default=None, ge=0),
    max_salary: float | None = Query(default=None, ge=0),
    skills: str | None = Query(default=None),
    remote: bool | None = Query(default=None),
    _: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    query = select(Job).options(joinedload(Job.company)).where((Job.deadline.is_(None)) | (Job.deadline >= date.today()))
    if company:
        query = query.where(Job.company.has(Company.name.ilike(f"%{company.strip()}%")))
    if title:
        query = query.where(Job.title.ilike(f"%{title.strip()}%"))
    if category:
        query = query.where(Job.category.ilike(category.strip()))
    if city:
        query = query.where(Job.location.ilike(f"%{city.strip()}%"))
    if min_salary is not None:
        query = query.where(Job.salary >= min_salary)
    if max_salary is not None:
        query = query.where(Job.salary <= max_salary)
    if skills:
        query = query.where(Job.skills.ilike(f"%{skills.strip()}%"))
    if remote is not None:
        query = query.where(Job.remote == remote)
    jobs = db.scalars(query.order_by(Job.deadline.is_(None), Job.deadline, Job.posting_date.desc())).unique().all()
    return [job_response(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_details(job_id: int, _: dict = Depends(require_student), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).options(joinedload(Job.company)).where(Job.id == job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_response(job)
