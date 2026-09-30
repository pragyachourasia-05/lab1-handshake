"""Pair constants plus environment-driven settings."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Repo root is three levels up from this file: app -> backend -> repo root
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# ---- Pair-derived constants (Lab 1 spec) ----
PAIR = 23
PORT_BASE = 9000 + (PAIR * 10)
SEED = PAIR
CITY_SET = ["San Francisco", "Oakland", "San Jose"]
DATABASE_PREFIX = f"p{PAIR}"

# ---- Database ----
DB_NAME = os.getenv("DB_NAME", f"{DATABASE_PREFIX}_handshake")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
# Optional full override (used by tests, e.g. sqlite:///./test.db)
DATABASE_URL_OVERRIDE = os.getenv("DATABASE_URL")

# ---- Auth ----
JWT_SECRET = os.getenv("JWT_SECRET", "change_me_locally")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

# ---- Uploads ----
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
PROFILE_PIC_DIR = UPLOAD_DIR / "profile_pictures"
RESUME_DIR = UPLOAD_DIR / "resumes"
MAX_PROFILE_PIC_BYTES = 2 * 1024 * 1024

# ---- CORS ----
FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")
