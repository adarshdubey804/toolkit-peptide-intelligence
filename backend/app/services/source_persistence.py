"""Persistence helpers for durable, explicitly typed external source snapshots.

Normalized provider records are not mislabelled as raw upstream API responses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .provenance import build_source_envelope


def persist_normalized_source_record(
    db: Session,
    *,
    source_name: str,
    source_identifier: str,
    source_url: str,
    title: str,
    payload: dict[str, Any],
    retrieved_at: datetime | None = None,
    source_version: str | None = None,
) -> dict[str, str]:
    """Upsert stable source identity and insert/find an immutable normalized snapshot."""
    envelope = build_source_envelope(
        source_name=source_name,
        source_identifier=source_identifier,
        source_url=source_url,
        payload=payload,
        retrieved_at=retrieved_at,
        source_version=source_version,
    )
    row = db.execute(text("""
        INSERT INTO source_records (
            source_name, source_identifier, source_url, retrieved_at,
            source_version, content_hash, fetched_at, last_seen_at, raw_metadata
        ) VALUES (
            :source_name, :source_identifier, :source_url, :retrieved_at,
            :source_version, :content_hash, :retrieved_at, :retrieved_at,
            jsonb_build_object('record_title', :title, 'provenance_kind', 'normalized_provider_record')
        )
        ON CONFLICT (source_name, source_identifier) DO UPDATE SET
            source_url = EXCLUDED.source_url,
            source_version = COALESCE(EXCLUDED.source_version, source_records.source_version),
            content_hash = EXCLUDED.content_hash,
            fetched_at = EXCLUDED.fetched_at,
            last_seen_at = EXCLUDED.last_seen_at
        RETURNING id
    """), {
        "source_name": envelope["source_name"],
        "source_identifier": envelope["source_identifier"],
        "source_url": envelope["source_url"],
        "retrieved_at": envelope["retrieved_at"],
        "source_version": envelope["source_version"],
        "content_hash": envelope["content_hash"],
        "title": title,
    }).mappings().one()

    db.execute(text("""
        INSERT INTO source_record_versions (
            source_record_id, content_hash, raw_payload, captured_at, payload_kind
        ) VALUES (
            :source_id, :content_hash, CAST(:payload AS jsonb), :captured_at,
            'normalized_provider_record'
        )
        ON CONFLICT (source_record_id, content_hash) DO NOTHING
    """), {
        "source_id": row["id"],
        "content_hash": envelope["content_hash"],
        "payload": __import__("json").dumps(
            envelope["raw_payload"], ensure_ascii=False, allow_nan=False
        ),
        "captured_at": envelope["retrieved_at"],
    })
    version = db.execute(text("""
        SELECT id FROM source_record_versions
        WHERE source_record_id=:source_id AND content_hash=:content_hash
    """), {"source_id": row["id"], "content_hash": envelope["content_hash"]}).mappings().one()

    return {
        "source_record_id": str(row["id"]),
        "source_record_version_id": str(version["id"]),
        "content_hash": envelope["content_hash"],
        "source_url": envelope["source_url"],
    }
