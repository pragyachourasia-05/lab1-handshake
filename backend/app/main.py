from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401
from .config import UPLOAD_DIR
from .database import Base, engine
from .routers import applications, assistant, companies, events, jobs, students

app = FastAPI(title="Lab 1 Handshake API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables() -> None:
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(students.router)
app.include_router(companies.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(events.router)
app.include_router(assistant.router)
