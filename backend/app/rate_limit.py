from datetime import datetime, timedelta, timezone
from math import ceil

from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session


def request_client_identity(request: Request) -> str:
    """Return the immediate network peer; do not trust caller-supplied forwarding headers."""
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_rate_limit(
    db: Session,
    *,
    scope: str,
    identity: str,
    limit: int,
    window_seconds: int = 60,
) -> None:
    """Atomically enforce a fixed-window limit shared by every API instance.

    A transaction-scoped advisory lock serializes updates for one bucket. The
    database clock is read after acquiring that lock so requests straddling a
    window boundary cannot reset or increment the wrong window.
    """
    if limit < 1 or window_seconds < 1:
        raise ValueError("Rate limit and window must be positive.")

    bucket_key = f"{scope}:{identity}"
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:bucket_key, 0))"),
        {"bucket_key": bucket_key},
    )
    now = db.execute(text("SELECT clock_timestamp()")).scalar_one()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    epoch = int(now.timestamp())
    window_epoch = epoch - (epoch % window_seconds)
    window_start = datetime.fromtimestamp(window_epoch, tz=timezone.utc)

    count = db.execute(
        text("""
            INSERT INTO api_rate_limit_buckets
                (bucket_key, window_started_at, request_count, updated_at)
            VALUES
                (:bucket_key, :window_started_at, 1, :now)
            ON CONFLICT (bucket_key) DO UPDATE
            SET window_started_at = EXCLUDED.window_started_at,
                request_count = CASE
                    WHEN api_rate_limit_buckets.window_started_at = EXCLUDED.window_started_at
                    THEN api_rate_limit_buckets.request_count + 1
                    ELSE 1
                END,
                updated_at = EXCLUDED.updated_at
            RETURNING request_count
        """),
        {
            "bucket_key": bucket_key,
            "window_started_at": window_start,
            "now": now,
        },
    ).scalar_one()
    # Only one request per hour wins the atomic maintenance marker update.
    cleanup_due = db.execute(text("""
        UPDATE api_rate_limit_maintenance
        SET last_cleanup_at = clock_timestamp()
        WHERE singleton = TRUE
          AND last_cleanup_at < clock_timestamp() - interval '1 hour'
        RETURNING singleton
    """)).scalar_one_or_none()
    if cleanup_due:
        db.execute(text("""
            DELETE FROM api_rate_limit_buckets
            WHERE updated_at < clock_timestamp() - interval '30 days'
        """))

    db.commit()

    if count > limit:
        retry_after = max(1, ceil((window_start + timedelta(seconds=window_seconds) - now).total_seconds()))
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please retry after the current rate-limit window.",
            headers={"Retry-After": str(retry_after)},
        )
