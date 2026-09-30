from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..auth import require_student
from ..config import MAX_RESUME_BYTES, UPLOAD_DIR
from ..database import get_db
from ..models import Application, Job
from ..schemas import ApplicationResponse

router = APIRouter(tags=["student applications"])


def application_response(application: Application) -> dict:
    return {
        "id": application.id,
        "job_id": application.job.id,
        "job_title": application.job.title,
        "company_name": application.job.company.name,
        "applied_at": application.applied_at,
        "status": application.status,
        "original_filename": application.original_filename,
    }


@router.post("/jobs/{job_id}/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    job_id: int,
    resume: UploadFile = File(...),
    identity: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    filename = resume.filename or "resume.pdf"
    if resume.content_type != "application/pdf" or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are accepted")
    job = db.scalar(select(Job).options(joinedload(Job.company)).where(Job.id == job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = db.scalar(select(Application).where(Application.job_id == job_id, Application.student_id == identity["user_id"]))
    if existing:
        raise HTTPException(status_code=409, detail="You already applied to this job")
    content = await resume.read()
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail="Resume must be 10 MB or smaller")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_DIR / f"student_{identity['user_id']}_{uuid4().hex}.pdf"
    stored_path.write_bytes(content)
    application = Application(student_id=identity["user_id"], job_id=job_id, resume_path=str(stored_path), original_filename=filename, status="Pending")
    db.add(application)
    db.commit()
    db.refresh(application)
    application = db.scalar(select(Application).options(joinedload(Application.job).joinedload(Job.company)).where(Application.id == application.id))
    return application_response(application)


@router.get("/students/me/applications", response_model=list[ApplicationResponse])
def list_my_applications(
    status_filter: str | None = Query(default=None, alias="status"),
    identity: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    query = select(Application).options(joinedload(Application.job).joinedload(Job.company)).where(Application.student_id == identity["user_id"])
    if status_filter:
        normalized = status_filter.strip().capitalize()
        if normalized not in {"Pending", "Reviewed", "Declined"}:
            raise HTTPException(status_code=400, detail="Status must be Pending, Reviewed, or Declined")
        query = query.where(Application.status == normalized)
    applications = db.scalars(query.order_by(Application.applied_at.desc())).unique().all()
    return [application_response(application) for application in applications]
