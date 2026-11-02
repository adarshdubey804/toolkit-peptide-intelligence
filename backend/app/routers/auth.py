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
# One-time Argon2 hash used so unknown emails and password-less accounts still
# perform a password verification with comparable cost to a real account.
DUMMY_PASSWORD_HASH = password_hash.hash("toolkit-invalid-login-dummy-secret")
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
    # Always perform one Argon2 verification, including for unknown email
    # addresses and accounts without a password hash, to reduce timing-based
    # account enumeration.
    stored_hash = user["password_hash"] if user and user["password_hash"] else DUMMY_PASSWORD_HASH
    password_valid = password_hash.verify(payload.password, stored_hash)
    if not user or not password_valid:
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
        # Bind the authenticated session to the organization selected when the
        # token was issued. Never choose an arbitrary active membership.
        organization_id = UUID(claims["org"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized
    user = db.execute(text("""
        SELECT up.id, up.email, up.display_name, om.organization_id,
               om.role, up.is_active, o.name AS organization_name
        FROM user_profiles up
        JOIN organization_memberships om ON om.user_id = up.id
        JOIN organizations o ON o.id = om.organization_id
        WHERE up.id = :user_id
          AND om.organization_id = :organization_id
          AND om.membership_status = 'active'
        LIMIT 1
    """), {"user_id": user_id, "organization_id": organization_id}).mappings().first()
    if not user or not user["is_active"]:
        raise unauthorized
    return _user_response(user)



class SwitchOrganizationRequest(BaseModel):
    organization_id: UUID


@router.get("/organizations")
def list_user_organizations(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    rows = db.execute(text("""
        SELECT o.id AS organization_id, o.name AS organization_name,
               om.role, om.created_at AS membership_created_at
        FROM organization_memberships om
        JOIN organizations o ON o.id = om.organization_id
        JOIN user_profiles up ON up.id = om.user_id
        WHERE om.user_id = :user_id
          AND om.membership_status = 'active'
          AND up.is_active = TRUE
        ORDER BY om.created_at, o.name
    """), {"user_id": current_user["id"]}).mappings().all()
    return {
        "items": [
            {
                "organization_id": str(row["organization_id"]),
                "organization_name": row["organization_name"],
                "role": row["role"],
                "membership_created_at": row["membership_created_at"],
                "is_current": str(row["organization_id"]) == current_user["organization_id"],
            }
            for row in rows
        ],
        "count": len(rows),
    }


@router.post("/switch-organization")
def switch_organization(
    payload: SwitchOrganizationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    membership = db.execute(text("""
        SELECT up.id, up.email, up.display_name, up.is_active,
               om.organization_id, om.role, o.name AS organization_name
        FROM organization_memberships om
        JOIN user_profiles up ON up.id = om.user_id
        JOIN organizations o ON o.id = om.organization_id
        WHERE om.user_id = :user_id
          AND om.organization_id = :organization_id
          AND om.membership_status = 'active'
          AND up.is_active = TRUE
    """), {
        "user_id": current_user["id"],
        "organization_id": payload.organization_id,
    }).mappings().first()
    if not membership:
        raise HTTPException(status_code=404, detail="Active organization membership not found.")

    user = dict(membership)
    db.execute(text("""
        INSERT INTO audit_events
            (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES
            (:actor, :organization_id, 'organization_context_switched', 'organization',
             :organization_id, jsonb_build_object('previous_organization_id', :previous_organization_id))
    """), {
        "actor": current_user["id"],
        "organization_id": payload.organization_id,
        "previous_organization_id": current_user["organization_id"],
    })
    db.commit()
    token = _create_access_token(
        str(user["id"]), str(user["organization_id"]), user["role"]
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_TTL_MINUTES * 60,
        "user": _user_response(user),
    }


@router.get("/me")
def me(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user
