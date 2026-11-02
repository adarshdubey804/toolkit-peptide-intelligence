from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.rate_limit import enforce_rate_limit


class FakeResult:
    def __init__(self, value=None):
        self.value = value

    def scalar_one(self):
        return self.value

    def scalar_one_or_none(self):
        return self.value


class FakeDB:
    def __init__(self, count, now, context=None):
        self.count = count
        self.now = now
        self.context = dict(context or {})
        self.statements = []
        self.committed = False

    def execute(self, statement, params=None):
        sql = str(statement)
        values = params or {}
        self.statements.append((sql, values))
        if "current_setting('app.organization_id'" in sql:
            return FakeResult(self.context.get("app.organization_id"))
        if "current_setting('app.user_id'" in sql:
            return FakeResult(self.context.get("app.user_id"))
        if "set_config('app.organization_id'" in sql:
            self.context["app.organization_id"] = values["organization_id"]
            return FakeResult(values["organization_id"])
        if "set_config('app.user_id'" in sql:
            self.context["app.user_id"] = values["user_id"]
            return FakeResult(values["user_id"])
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
    assert any("pg_advisory_xact_lock" in sql for sql, _ in db.statements)
    insert_sql, params = next(
        item for item in db.statements if "ON CONFLICT (bucket_key) DO UPDATE" in item[0]
    )
    assert params["bucket_key"].startswith("login:")
    assert "192.0.2.10" not in params["bucket_key"]
    assert params["window_started_at"] == datetime(2026, 11, 2, 10, 0, 0, tzinfo=timezone.utc)
    assert any("api_rate_limit_maintenance" in sql for sql, _ in db.statements)


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



def test_request_identity_ignores_untrusted_forwarded_headers():
    from types import SimpleNamespace

    from app.rate_limit import request_client_identity

    request = SimpleNamespace(
        client=SimpleNamespace(host="10.0.0.8"),
        headers={"x-forwarded-for": "203.0.113.77"},
    )
    assert request_client_identity(request) == "10.0.0.8"


def test_public_research_router_has_rate_limit_dependency():
    from app.routers.research import limit_public_research_discovery, router

    assert any(
        dependency.dependency is limit_public_research_discovery
        for dependency in router.dependencies
    )


def test_rate_limit_restores_transaction_local_tenant_context_after_commit():
    now = datetime(2026, 11, 2, 10, 0, 5, tzinfo=timezone.utc)
    organization_id = "9b4c3e5c-9e75-4e45-a11b-1a57ac1c2f3e"
    user_id = "e3b4e2a2-4ad1-4a0f-b5bd-3b99cb6c6c11"
    db = FakeDB(
        count=1,
        now=now,
        context={
            "app.organization_id": organization_id,
            "app.user_id": user_id,
        },
    )

    enforce_rate_limit(
        db,
        scope="agent_execution",
        identity=user_id,
        limit=10,
        window_seconds=60,
    )

    assert db.committed
    assert db.context == {
        "app.organization_id": organization_id,
        "app.user_id": user_id,
    }
    restore_statements = [
        sql for sql, _ in db.statements
        if "set_config('app.organization_id'" in sql or "set_config('app.user_id'" in sql
    ]
    assert len(restore_statements) == 2


def test_public_rate_limit_does_not_create_missing_tenant_context():
    now = datetime(2026, 11, 2, 10, 0, 5, tzinfo=timezone.utc)
    db = FakeDB(count=1, now=now)

    enforce_rate_limit(
        db,
        scope="public_research_discovery",
        identity="192.0.2.10",
        limit=30,
        window_seconds=60,
    )

    assert db.context == {}
    assert not any(
        "set_config(" in sql for sql, _ in db.statements
    )
