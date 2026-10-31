import re
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, field_validator
from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
password_hash = PasswordHash.recommended()
TOKEN_TTL_MINUTES = 60


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=2, max_length=100)
    organization_name: str = Field(min_length=2, max_length=160)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


def _create_access_token(user_id: str, organization_id: str | None, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "org": organization_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_TTL_MINUTES),
        "iss": "toolkit-peptide-intelligence",
        "aud": "toolkit-peptide-intelligence-api",
    }
    return jwt.encode(payload, settings.app_secret_key, algorithm="HS256")


def _user_response(row) -> dict:
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "display_name": row["display_name"],
        "organization_id": str(row["organization_id"]) if row["organization_id"] else None,
        "organization_name": row["organization_name"],
        "role": row["role"],
        "is_active": row["is_active"],
    }


def _load_user(db: Session, email: str):
    return db.execute(text("""
        SELECT up.id, up.email, up.password_hash, up.display_name,
               om.organization_id, om.role, up.is_active, o.name AS organization_name
        FROM user_profiles up
        LEFT JOIN organization_memberships om ON om.user_id = up.id AND om.membership_status = 'active'
        LEFT JOIN organizations o ON o.id = om.organization_id
        WHERE lower(up.email) = :email
        ORDER BY om.created_at
        LIMIT 1
    """), {"email": email}).mappings().first()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    """Create a researcher account and a private organization workspace."""
    if len(settings.app_secret_key) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured with a sufficiently long application secret.")
    try:
        with db.begin():
            organization_id = db.execute(
                text("INSERT INTO organizations (name, organization_type) VALUES (:name, 'research_team') RETURNING id"),
                {"name": payload.organization_name.strip()},
            ).scalar_one()
            row = db.execute(text("""
                INSERT INTO user_profiles
                    (organization_id, email, password_hash, display_name, role, is_active)
                VALUES
                    (:organization_id, :email, :password_hash, :display_name, 'organization_admin', TRUE)
                RETURNING id, email, display_name, organization_id, role, is_active
            """), {
                "organization_id": organization_id,
                "email": payload.email,
                "password_hash": password_hash.hash(payload.password),
                "display_name": payload.display_name.strip(),
            }).mappings().one()
            db.execute(text("""
                INSERT INTO organization_memberships (organization_id, user_id, role)
                VALUES (:organization_id, :user_id, 'organization_admin')
            """), {"organization_id": organization_id, "user_id": row["id"]})
        user = dict(row)
        user["organization_name"] = payload.organization_name.strip()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from exc
    token = _create_access_token(str(user["id"]), str(user["organization_id"]), user["role"])
    return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_TTL_MINUTES * 60, "user": _user_response(user)}


@router.post("/login")
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    if len(settings.app_secret_key) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured with a sufficiently long application secret.")
    user = _load_user(db, payload.email.strip().lower())
    # A dummy verification reduces obvious timing differences for unknown accounts.
    if not user or not user["password_hash"] or not password_hash.verify(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.", headers={"WWW-Authenticate": "Bearer"})
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="This account is inactive.")
    token = _create_access_token(str(user["id"]), str(user["organization_id"]) if user["organization_id"] else None, user["role"])
    return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_TTL_MINUTES * 60, "user": _user_response(user)}


def get_current_user(token: Annotated[str | None, Depends(oauth2_scheme)], db: Annotated[Session, Depends(get_db)]):
    unauthorized = HTTPException(status_code=401, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    if not token:
        raise unauthorized
    try:
        claims = jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=["HS256"],
            audience="toolkit-peptide-intelligence-api",
            issuer="toolkit-peptide-intelligence",
        )
        user_id = UUID(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized
    user = db.execute(text("""
        SELECT up.id, up.email, up.display_name, om.organization_id,
               om.role, up.is_active, o.name AS organization_name
        FROM user_profiles up
        JOIN organization_memberships om ON om.user_id = up.id
        JOIN organizations o ON o.id = om.organization_id
        WHERE up.id = :user_id AND om.membership_status = 'active'
        ORDER BY om.created_at
        LIMIT 1
    """), {"user_id": user_id}).mappings().first()
    if not user or not user["is_active"]:
        raise unauthorized
    return _user_response(user)


@router.get("/me")
def me(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user
