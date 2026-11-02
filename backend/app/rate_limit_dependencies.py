"""Reusable rate-limit dependencies for authenticated write endpoints."""
from typing import Annotated, Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .rate_limit import enforce_rate_limit, request_client_identity
from .routers.auth import get_current_user


def authenticated_write_rate_limit(scope: str, limit: int | None = None) -> Callable:
    """Build a per-user, database-shared rate-limit dependency for a write route."""
    def dependency(
        current_user: Annotated[dict, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> None:
        enforce_rate_limit(
            db,
            scope=scope,
            identity=str(current_user["id"]),
            limit=limit or settings.sensitive_write_rate_limit_per_window,
            window_seconds=settings.rate_limit_window_seconds,
        )

    dependency.rate_limit_scope = scope
    return dependency


def public_request_rate_limit(scope: str, limit: int | None = None) -> Callable:
    """Build a shared per-network-peer limit for unauthenticated compute endpoints."""
    def dependency(
        request: Request,
        db: Annotated[Session, Depends(get_db)],
    ) -> None:
        enforce_rate_limit(
            db,
            scope=scope,
            identity=request_client_identity(request),
            limit=limit or settings.public_research_rate_limit_per_window,
            window_seconds=settings.rate_limit_window_seconds,
        )

    dependency.rate_limit_scope = scope
    return dependency
