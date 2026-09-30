from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..auth import require_student
from ..database import get_db
from ..models import Event, EventRegistration, Student
from ..schemas import EventResponse, RegistrationResponse

router = APIRouter(tags=["student events"])


def event_response(event: Event) -> dict:
    return {
        "id": event.id,
        "name": event.name,
        "description": event.description,
        "event_date": event.event_date,
        "event_time": event.event_time,
        "location": event.location,
        "eligibility": event.eligibility,
        "company_id": event.company_id,
        "company_name": event.company.name,
    }


def eligible(event: Event, student: Student) -> bool:
    if not event.eligibility:
        return True
    text = event.eligibility.lower()
    student_values = [student.major, student.degree, student.college]
    return "all" in text or "any" in text or any(value and value.lower() in text for value in student_values)


@router.get("/events", response_model=list[EventResponse])
def search_events(
    name: str | None = Query(default=None),
    city: str | None = Query(default=None),
    _: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    query = select(Event).options(joinedload(Event.company)).where(Event.event_date >= date.today())
    if name:
        query = query.where(Event.name.ilike(f"%{name.strip()}%"))
    if city:
        query = query.where(Event.location.ilike(f"%{city.strip()}%"))
    events = db.scalars(query.order_by(Event.event_date, Event.event_time)).unique().all()
    return [event_response(event) for event in events]


@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, _: dict = Depends(require_student), db: Session = Depends(get_db)):
    event = db.scalar(select(Event).options(joinedload(Event.company)).where(Event.id == event_id))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event_response(event)


@router.post("/events/{event_id}/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_for_event(event_id: int, identity: dict = Depends(require_student), db: Session = Depends(get_db)):
    event = db.scalar(select(Event).options(joinedload(Event.company)).where(Event.id == event_id))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.event_date < date.today():
        raise HTTPException(status_code=400, detail="Registration is closed for past events")
    student = db.get(Student, identity["user_id"])
    if not eligible(event, student):
        raise HTTPException(status_code=403, detail="You are not eligible for this event")
    existing = db.scalar(select(EventRegistration).where(EventRegistration.event_id == event_id, EventRegistration.student_id == student.id))
    if existing:
        raise HTTPException(status_code=409, detail="You are already registered for this event")
    registration = EventRegistration(event_id=event_id, student_id=student.id)
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return {"id": registration.id, "event_id": event.id, "event_name": event.name, "event_date": event.event_date, "registered_at": registration.registered_at}


@router.get("/students/me/events", response_model=list[RegistrationResponse])
def registered_events(identity: dict = Depends(require_student), db: Session = Depends(get_db)):
    registrations = db.scalars(select(EventRegistration).options(joinedload(EventRegistration.event)).where(EventRegistration.student_id == identity["user_id"]).order_by(EventRegistration.registered_at.desc())).unique().all()
    return [{"id": item.id, "event_id": item.event.id, "event_name": item.event.name, "event_date": item.event.event_date, "registered_at": item.registered_at} for item in registrations]
