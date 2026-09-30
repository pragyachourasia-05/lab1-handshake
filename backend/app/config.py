from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

PAIR = int(os.getenv("PAIR", "23"))
PORT_BASE = int(os.getenv("PORT_BASE", str(9000 + PAIR * 10)))
SEED = int(os.getenv("SEED", str(PAIR)))
CITY_SET = ["San Francisco", "Oakland", "San Jose"]
DATABASE_PREFIX = f"p{PAIR}"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://root:change_me_locally@localhost:3306/{DATABASE_PREFIX}_handshake",
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-local-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "backend/app/uploads"))
MAX_RESUME_BYTES = 10 * 1024 * 1024
