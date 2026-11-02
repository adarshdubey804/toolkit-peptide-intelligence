from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.rate_limit import enforce_rate_limit


class FakeResult:
    def __init__(self, value=None):
        self.value = value

    def scalar_one(self):
        return self.value


class FakeDB:
    def __init__(self, count, now):
        self.count = count
        self.now = now
        self.statements = []
        self.committed = False

    def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append((sql, params or {}))
        if "clock_timestamp()" in sql:
            return FakeResult(self.now)
        if "RETURNING request_count" in sql:
            return FakeResult(self.count)
        return FakeResult()

    def commit(self):
        self.committed = True


def test_rate_limit_uses_database_clock_and_commits_shared_bucket():
    now = datetime(2026, 11, 2, 10, 0, 5, tzinfo=timezone.utc)
    db = FakeDB(count=1, now=now)

    enforce_rate_limit(
        db,
        scope="login",
        identity="192.0.2.10",
        limit=10,
        window_seconds=60,
    )

    assert db.committed
    assert "pg_advisory_xact_lock" in db.statements[0][0]
    insert_sql, params = db.statements[2]
    assert "ON CONFLICT (bucket_key) DO UPDATE" in insert_sql
    assert params["bucket_key"] == "login:192.0.2.10"
    assert params["window_started_at"] == datetime(2026, 11, 2, 10, 0, 0, tzinfo=timezone.utc)


def test_rate_limit_returns_429_and_retry_after_when_exceeded():
    now = datetime(2026, 11, 2, 10, 0, 5, tzinfo=timezone.utc)
    db = FakeDB(count=11, now=now)

    with pytest.raises(HTTPException) as error:
        enforce_rate_limit(
            db,
            scope="login",
            identity="192.0.2.10",
            limit=10,
            window_seconds=60,
        )

    assert db.committed
    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"] == "55"
