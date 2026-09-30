from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config
from app.database import init_db
from app.routers import students


@asynccontextmanager
async def lifespan(_app: FastAPI):
    config.PROFILE_PIC_DIR.mkdir(parents=True, exist_ok=True)
    config.RESUME_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(title="Lab 1 Handshake API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Profile pictures are served from /uploads/profile_pictures/...
# (resumes are NOT public; serve them through an authorized route in Week 2)
config.PROFILE_PIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount(
    "/uploads/profile_pictures",
    StaticFiles(directory=config.PROFILE_PIC_DIR),
    name="profile_pictures",
)

app.include_router(students.router)
# Partner B: app.include_router(companies.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
