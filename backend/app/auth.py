"""Password hashing (bcrypt), JWT issue/verify, and auth dependencies."""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.models import Company, RevokedToken, Student

bearer_scheme = HTTPBearer(auto_error=False)


# ---------- passwords ----------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ---------- tokens ----------
def create_access_token(subject_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject_id),
        "role": role,  # "student" or "company"
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def revoke_token(db: Session, token: str) -> None:
    claims = decode_token(token)
    if not db.get(RevokedToken, claims["jti"]):
        db.add(
            RevokedToken(
                jti=claims["jti"],
                expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc).replace(
                    tzinfo=None
                ),
            )
        )
        db.commit()


# ---------- dependencies ----------
def get_token_claims(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = decode_token(creds.credentials)
    if db.get(RevokedToken, claims["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been signed out",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims["raw"] = creds.credentials
    return claims


def get_current_student(
    claims: dict = Depends(get_token_claims), db: Session = Depends(get_db)
) -> Student:
    if claims.get("role") != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Student access only")
    student = db.get(Student, int(claims["sub"]))
    if student is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account no longer exists")
    return student


def get_current_company(
    claims: dict = Depends(get_token_claims), db: Session = Depends(get_db)
) -> Company:
    if claims.get("role") != "company":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Company access only")
    company = db.get(Company, int(claims["sub"]))
    if company is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account no longer exists")
    return company
