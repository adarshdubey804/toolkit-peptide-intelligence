"""Read-only adapter for EMA Article 57 public EEA medicinal-product snapshot.

This is a product-discovery source, not a canonical authorization registry. Source rows
are preserved as observations and must be reviewed before linking to peptide identities.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
from typing import Any

import httpx
from openpyxl import load_workbook

SOURCE_NAME = "European Medicines Agency Article 57 database"
SOURCE_PAGE = (
    "https://www.ema.europa.eu/en/human-regulatory-overview/post-authorisation/"
    "data-medicines-iso-idmp-standards-post-authorisation/public-data-article-57-database"
)
DATA_URL = "https://www.ema.europa.eu/en/documents/other/article-57-product-data_en.xlsx"
CACHE_TTL = timedelta(hours=6)
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
_cache: dict[str, Any] = {"payload": None, "retrieved_at": None, "etag": None, "last_modified": None}
_cache_lock = asyncio.Lock()


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().replace("_", " ").split())


def _column_index(headers: list[str], candidates: tuple[str, ...]) -> int | None:
    normalized = [_norm(value) for value in headers]
    for candidate in candidates:
        candidate_norm = _norm(candidate)
        for index, header in enumerate(normalized):
            if header == candidate_norm or candidate_norm in header:
                return index
    return None


def parse_article57_workbook(content: bytes, query: str, limit: int = 30) -> list[dict]:
    """Parse a source snapshot using header discovery rather than fixed row/column positions."""
    if not 2 <= len(content) <= MAX_DOWNLOAD_BYTES:
        raise ValueError("EMA Article 57 workbook size is outside the accepted range.")
    if not 2 <= len(query.strip()) <= 160:
        raise ValueError("EMA Article 57 query must contain 2 to 160 characters.")
    if not 1 <= limit <= 50:
        raise ValueError("EMA Article 57 result limit must be between 1 and 50.")

    try:
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:
        raise ValueError("EMA Article 57 response is not a readable XLSX workbook.") from exc

    term = _norm(query)
    results: list[dict] = []
    seen: set[str] = set()
    header_found = False
    try:
        for sheet in workbook.worksheets:
            header_row_number = None
            headers: list[str] = []
            for row_number, row in enumerate(sheet.iter_rows(min_row=1, max_row=30, values_only=True), start=1):
                candidate_headers = [str(value or "") for value in row]
                if (
                    _column_index(candidate_headers, ("product name", "product short name")) is not None
                    and _column_index(candidate_headers, ("active substance", "active substances")) is not None
                ):
                    header_row_number = row_number
                    headers = candidate_headers
                    break
            if header_row_number is None:
                continue
            header_found = True

            indexes = {
                "product_name": _column_index(headers, ("product name", "product short name")),
                "active_substance": _column_index(headers, ("active substance", "active substances")),
                "route": _column_index(headers, ("route of administration", "route")),
                "country": _column_index(headers, ("country of authorisation", "country of authorization")),
                "holder": _column_index(headers, ("marketing authorisation holder", "marketing authorization holder", "company")),
            }
            for row_number, row in enumerate(
                sheet.iter_rows(min_row=header_row_number + 1, values_only=True),
                start=header_row_number + 1,
            ):
                def value(key: str) -> str | None:
                    index = indexes[key]
                    if index is None or index >= len(row) or row[index] is None:
                        return None
                    text_value = " ".join(str(row[index]).split())
                    return text_value or None

                product_name = value("product_name")
                active_substance = value("active_substance")
                if not product_name or not active_substance:
                    continue
                if term not in _norm(product_name) and term not in _norm(active_substance):
                    continue
                normalized = {
                    "product_name": product_name,
                    "active_substance": active_substance,
                    "route_of_administration": value("route"),
                    "country_of_authorisation": value("country"),
                    "marketing_authorisation_holder": value("holder"),
                    "source_status": "valid_marketing_authorisation_in_article57_snapshot",
                    "jurisdiction": "EEA",
                    "source": SOURCE_NAME,
                    "source_url": SOURCE_PAGE,
                    "source_locator": f"{sheet.title}!row:{row_number}",
                    "curation_status": "not_reviewed",
                    "coverage_notice": (
                        "EMA Article 57 includes products with valid marketing authorisations in the "
                        "source snapshot. This row is not a peptide identity match or an independently "
                        "verified product-level authorization. Verify product, active substance, "
                        "country, route, and current status with the relevant competent authority."
                    ),
                }
                stable_material = "|".join(
                    [product_name, active_substance, value("country") or "", value("route") or ""]
                ).casefold()
                identifier = sha256(stable_material.encode("utf-8")).hexdigest()[:24]
                normalized["source_identifier"] = identifier
                if identifier not in seen:
                    seen.add(identifier)
                    results.append(normalized)
                if len(results) >= limit:
                    return results
    finally:
        workbook.close()
    if not header_found:
        raise ValueError("EMA Article 57 workbook schema changed: required product and active-substance columns were not found.")
    return results


class EmaArticle57Provider:
    async def _download_snapshot(self) -> tuple[bytes, str | None, str | None, str]:
        now = datetime.now(timezone.utc)
        async with _cache_lock:
            retrieved = _cache["retrieved_at"]
            if _cache["payload"] is not None and retrieved and now - retrieved < CACHE_TTL:
                return (
                    _cache["payload"],
                    _cache["etag"],
                    _cache["last_modified"],
                    retrieved.isoformat(),
                )

            timeout = httpx.Timeout(60.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(DATA_URL, headers={"Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})
                response.raise_for_status()
                if len(response.content) > MAX_DOWNLOAD_BYTES:
                    raise ValueError("EMA Article 57 workbook exceeds the configured download limit.")
                if not response.content.startswith(b"PK"):
                    raise ValueError("EMA Article 57 returned a non-XLSX response.")
                _cache.update({
                    "payload": response.content,
                    "retrieved_at": now,
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                })
                return (
                    response.content,
                    _cache["etag"],
                    _cache["last_modified"],
                    now.isoformat(),
                )

    async def search(self, query: str, limit: int = 30) -> dict:
        term = query.strip()
        if len(term) < 2:
            raise ValueError("EMA Article 57 search requires at least two characters.")
        if not 1 <= limit <= 50:
            raise ValueError("EMA Article 57 result limit must be between 1 and 50.")
        content, etag, last_modified, retrieved_at = await self._download_snapshot()
        items = parse_article57_workbook(content, term, limit)
        source_version = last_modified or etag or retrieved_at
        for item in items:
            item["source_version"] = source_version
        return {
            "source": SOURCE_NAME,
            "query": term,
            "status": "success",
            "total": len(items),
            "items": items,
            "retrieved_at": retrieved_at,
            "source_last_modified": last_modified,
            "source_etag": etag,
            "source_url": SOURCE_PAGE,
            "coverage_notice": (
                "Article 57 is a public EEA product snapshot of valid marketing authorisations. "
                "It does not cover every national register field, withdrawn or investigational products, "
                "and it does not determine whether a matched active substance is a peptide."
            ),
        }
