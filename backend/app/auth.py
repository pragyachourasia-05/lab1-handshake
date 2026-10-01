from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from .database import get_db
from .models import Company, Student

security = HTTPBearer()
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": f"{role}:{user_id}", "role": role, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_identity(token: str) -> dict[str, Any]:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        role = payload.get("role")
        if not subject or role not in {"student", "company"}:
            raise credentials_error
        subject_role, raw_id = subject.split(":", 1)
        if subject_role != role:
            raise credentials_error
        return {"role": role, "user_id": int(raw_id)}
    except (JWTError, ValueError, IndexError):
        raise credentials_error


def get_current_identity(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = decode_identity(credentials.credentials)
    model = Student if identity["role"] == "student" else Company
    user = db.get(model, identity["user_id"])
    if user is None:
        raise HTTPException(status_code=401, detail="Authenticated user no longer exists")
    return {**identity, "user": user}


def require_student(identity: dict[str, Any] = Depends(get_current_identity)) -> dict[str, Any]:
    if identity["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access is required")
    return identity


def require_company(identity: dict[str, Any] = Depends(get_current_identity)) -> dict[str, Any]:
    if identity["role"] != "company":
        raise HTTPException(status_code=403, detail="Company access is required")
    return identity
