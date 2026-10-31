"""Shared provenance envelope helpers for external research records.

These helpers normalize metadata only; they do not persist records or mark them verified.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit


def canonicalize_source_url(url: str) -> str:
    """Remove fragments and default ports while preserving path and query semantics."""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    if not scheme or not hostname:
        raise ValueError("A source URL must be absolute and include a host.")
    port = parts.port
    netloc = hostname
    if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        netloc = f"{hostname}:{port}"
    if parts.username or parts.password:
        raise ValueError("Credentials are not allowed in source URLs.")
    return urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))


def stable_content_hash(payload: Any) -> str:
    """SHA-256 of deterministic UTF-8 JSON; rejects non-JSON payloads."""
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_source_envelope(
    *,
    source_name: str,
    source_identifier: str,
    source_url: str,
    payload: Any,
    retrieved_at: datetime | None = None,
    source_version: str | None = None,
) -> dict[str, Any]:
    """Build a traceable, explicitly unreviewed external-source record."""
    if not source_name.strip() or not source_identifier.strip():
        raise ValueError("Source name and stable source identifier are required.")
    timestamp = retrieved_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware.")
    return {
        "source_name": source_name.strip(),
        "source_identifier": source_identifier.strip(),
        "source_url": canonicalize_source_url(source_url),
        "retrieved_at": timestamp.astimezone(timezone.utc).isoformat(),
        "source_version": source_version,
        "content_hash": stable_content_hash(payload),
        "raw_payload": payload,
        "curation_status": "not_reviewed",
        "property_origin": "external_source",
    }
