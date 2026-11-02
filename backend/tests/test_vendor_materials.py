from uuid import uuid4

import pytest
from fastapi import HTTPException


class FakeResult:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return self

    def one(self):
        return self.row


class FakeDatabase:
    def __init__(self, row):
        self.row = row
        self.statement = None
        self.parameters = None

    def execute(self, statement, parameters):
        self.statement = str(statement)
        self.parameters = parameters
        return FakeResult(self.row)


def test_source_record_does_not_overwrite_existing_identifier_url():
    from app.routers.vendor_materials import _source_record

    source_id = uuid4()
    db = FakeDatabase({"id": source_id, "source_url": "https://evidence.example.org/record/1"})
    result = _source_record(
        db,
        "Supplier certificate",
        "COA-123",
        "https://evidence.example.org/record/1",
    )
    assert result == source_id
    assert "DO UPDATE SET last_seen_at=now()" in db.statement
    assert "source_url=EXCLUDED.source_url" not in db.statement


def test_source_record_rejects_conflicting_url_for_existing_identifier():
    from app.routers.vendor_materials import _source_record

    db = FakeDatabase({"id": uuid4(), "source_url": "https://evidence.example.org/record/original"})
    with pytest.raises(HTTPException) as error:
        _source_record(
            db,
            "Supplier certificate",
            "COA-123",
            "https://evidence.example.org/record/changed",
        )
    assert error.value.status_code == 409
    assert "different URL" in error.value.detail


def test_source_record_rejects_non_https_before_database_write():
    from app.routers.vendor_materials import _source_record

    db = FakeDatabase({"id": uuid4(), "source_url": "http://evidence.example.org/record/1"})
    with pytest.raises(HTTPException) as error:
        _source_record(db, "Supplier report", "R-1", "http://evidence.example.org/record/1")
    assert error.value.status_code == 422
    assert db.statement is None
