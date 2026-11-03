"""Import peptide catalogue workbooks as source-backed, unresolved dossier folders."""
from __future__ import annotations

import hashlib
import json
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from openpyxl import load_workbook
from pydantic import BaseModel, Field, HttpUrl, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..db import get_db
from ..rate_limit_dependencies import authenticated_write_rate_limit

router = APIRouter(prefix="/api/v1/dossiers", tags=["peptide scientific dossiers"])

EXPECTED_COLUMNS = (
    "Peptide (generic / common name)",
    "Brand / Other Names",
    "Treatment Category",
    "Primary Use / Indication",
    "FDA Approved?",
    "Status Detail",
    "First US Approval",
    "Notes",
)


def _membership(user: dict, db: Session) -> tuple[str, str]:
    org = user.get("organization_id")
    if not org:
        raise HTTPException(status_code=403, detail="Organization membership required.")
    role = db.execute(text("""
        SELECT role FROM organization_memberships
        WHERE organization_id=:org AND user_id=:user_id AND membership_status='active'
    """), {"org": org, "user_id": user["id"]}).scalar_one_or_none()
    if role not in {"organization_admin", "researcher", "curator"}:
        raise HTTPException(status_code=403, detail="Researcher, curator or organization administrator access required.")
    return str(org), role


def _json_value(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


@router.post(
    "/import-workbook",
    dependencies=[Depends(authenticated_write_rate_limit("dossier_write"))],
)
async def import_peptide_workbook(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Import workbook rows into isolated, editable discovery folders without asserting facts."""
    organization_id, _ = _membership(current_user, db)
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=415, detail="Upload an .xlsx workbook.")
    raw = await file.read()
    if not raw or len(raw) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Workbook must be non-empty and no larger than 15 MB.")
    file_hash = hashlib.sha256(raw).hexdigest()
    try:
        workbook = load_workbook(BytesIO(raw), read_only=True, data_only=True)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="The uploaded workbook could not be read.") from exc
    if "Peptides" not in workbook.sheetnames:
        raise HTTPException(status_code=422, detail="Workbook must contain a 'Peptides' worksheet.")
    sheet = workbook["Peptides"]
    headers = tuple(_json_value(cell.value) for cell in next(sheet.iter_rows(min_row=1, max_row=1)))
    if headers[:len(EXPECTED_COLUMNS)] != EXPECTED_COLUMNS:
        raise HTTPException(status_code=422, detail="The Peptides worksheet headers do not match the expected catalogue format.")

    rows = []
    for row_number, values in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        row = {str(headers[i]): _json_value(values[i]) for i in range(min(len(headers), len(values))) if headers[i]}
        name = row.get(EXPECTED_COLUMNS[0])
        if name is None or not str(name).strip():
            continue
        rows.append((row_number, row, str(name).strip()))
    if not rows:
        raise HTTPException(status_code=422, detail="No peptide rows were found.")
    if len(rows) > 1000:
        raise HTTPException(status_code=422, detail="A single workbook import is limited to 1,000 rows.")

    batch = db.execute(text("""
        INSERT INTO peptide_workbook_import_batches
            (source_name, source_sha256, uploaded_filename, uploaded_by, organization_id)
        VALUES ('User peptide workbook', :hash, :filename, :user_id, :org)
        ON CONFLICT (source_sha256, organization_id) DO UPDATE
          SET uploaded_filename=EXCLUDED.uploaded_filename
        RETURNING id
    """), {"hash": file_hash, "filename": file.filename[:255], "user_id": current_user["id"], "org": organization_id}).scalar_one()

    imported = []
    try:
        for row_number, row, name in rows:
            row_json = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
            row_hash = hashlib.sha256(row_json.encode("utf-8")).hexdigest()
            source_identifier = f"{file_hash}:Peptides:{row_number}"
            source_id = db.execute(text("""
                INSERT INTO source_records (source_name, source_identifier, source_url, retrieved_at, license_notes, raw_metadata)
                VALUES ('User peptide workbook', :identifier, NULL, now(),
                        'User-provided workbook; preserve attribution and do not redistribute without permission.',
                        jsonb_build_object('filename', :filename, 'worksheet', 'Peptides', 'row_number', :row_number,
                                           'uploaded_by', :user_id))
                ON CONFLICT (source_name, source_identifier) DO UPDATE
                    SET retrieved_at=now()
                RETURNING id
            """), {"identifier": source_identifier, "filename": file.filename[:255],
                   "row_number": row_number, "user_id": current_user["id"]}).scalar_one()

            candidate = db.execute(text("""
                INSERT INTO peptide_discovery_candidates (
                    source_record_id, source_entity_identifier, source_entity_url,
                    candidate_name, candidate_kind, source_development_status,
                    source_jurisdiction_code, identity_match_status, candidate_status, raw_metadata
                ) VALUES (
                    :source_id, :entity_identifier, NULL, :name, 'unknown', :reported_status,
                    'US', 'unresolved', 'needs_review', CAST(:metadata AS jsonb)
                )
                ON CONFLICT (source_record_id, source_entity_identifier) DO UPDATE SET
                    candidate_name=EXCLUDED.candidate_name,
                    source_development_status=EXCLUDED.source_development_status,
                    raw_metadata=EXCLUDED.raw_metadata,
                    last_seen_at=now(), last_observed_at=now(), updated_at=now()
                RETURNING id
            """), {
                "source_id": source_id, "entity_identifier": source_identifier,
                "name": name, "reported_status": str(row.get("Status Detail") or row.get("FDA Approved?") or "Not stated"),
                "metadata": json.dumps({"workbook_row": row, "source_type": "user_supplied_catalogue",
                                        "regulatory_status_is_unverified": True}, ensure_ascii=False),
            }).scalar_one()

            db.execute(text("""
                INSERT INTO peptide_discovery_observations
                    (candidate_id, source_record_id, source_version, payload, payload_hash)
                VALUES (:candidate_id, :source_id, :version, CAST(:payload AS jsonb), :hash)
                ON CONFLICT (candidate_id, payload_hash) DO NOTHING
            """), {"candidate_id": candidate, "source_id": source_id, "version": file_hash,
                   "payload": row_json, "hash": row_hash})

            db.execute(text("""
                INSERT INTO peptide_workbook_import_rows
                    (batch_id, worksheet_name, worksheet_row_number, candidate_id, source_row, row_sha256)
                VALUES (:batch, 'Peptides', :row_number, :candidate, CAST(:source_row AS jsonb), :row_hash)
                ON CONFLICT (batch_id, worksheet_name, worksheet_row_number) DO UPDATE
                    SET source_row=EXCLUDED.source_row, row_sha256=EXCLUDED.row_sha256,
                        candidate_id=EXCLUDED.candidate_id
            """), {"batch": batch, "row_number": row_number, "candidate": candidate,
                   "source_row": row_json, "row_hash": row_hash})
            imported.append({"candidate_id": str(candidate), "name": name, "worksheet_row": row_number})

        db.execute(text("""
            UPDATE peptide_workbook_import_batches SET imported_row_count=:count WHERE id=:batch
        """), {"count": len(imported), "batch": batch})
        db.execute(text("""
            INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
            VALUES (:actor, :org, 'peptide_workbook_import', 'peptide_workbook_import_batch', :batch,
                    jsonb_build_object('row_count', :count, 'source_sha256', :hash, 'filename', :filename))
        """), {"actor": current_user["id"], "org": organization_id, "batch": batch,
               "count": len(imported), "hash": file_hash, "filename": file.filename[:255]})
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        workbook.close()

    return {
        "batch_id": str(batch),
        "source_sha256": file_hash,
        "imported_count": len(imported),
        "items": imported,
        "status": "imported_as_unresolved_source_observations",
        "governance": (
            "Every row has an independent discovery folder. Workbook-provided FDA status, "
            "indications and names remain unverified source assertions; no canonical peptide, "
            "mechanism, clinical conclusion or authorization is created by this import."
        ),
    }


class DossierReferenceInput(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    source_name: str = Field(min_length=2, max_length=160)
    url: HttpUrl
    doi: str | None = Field(default=None, max_length=200)
    pmid: str | None = Field(default=None, max_length=40)
    registry_id: str | None = Field(default=None, max_length=100)
    locator: str | None = Field(default=None, max_length=500)
    evidence_type: str = Field(default="unknown", max_length=60)
    notes: str | None = Field(default=None, max_length=2000)


class DossierMediaInput(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    image_url: HttpUrl
    asset_type: str = Field(default="other", max_length=60)
    caption: str | None = Field(default=None, max_length=1000)
    alt_text: str = Field(min_length=5, max_length=500)
    source_name: str = Field(min_length=2, max_length=160)
    source_identifier: str | None = Field(default=None, max_length=200)
    attribution: str | None = Field(default=None, max_length=500)
    license_or_reuse_terms: str = Field(min_length=3, max_length=1000)
    is_prediction: bool = False


class DossierSectionInput(BaseModel):
    content: dict = Field(default_factory=dict)
    references: list[DossierReferenceInput] = Field(default_factory=list, max_length=100)
    media: list[DossierMediaInput] = Field(default_factory=list, max_length=30)


@router.get("/candidates/{candidate_id}/sections")
def list_candidate_dossier_sections(
    candidate_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, _ = _membership(current_user, db)
    rows = db.execute(text("""
        SELECT id, section_key, content, references, media, revision, updated_at
        FROM peptide_dossier_sections
        WHERE candidate_id=:candidate AND organization_id=:org
        ORDER BY section_key
    """), {"candidate": candidate_id, "org": organization_id}).mappings().all()
    return {"items": [dict(row) for row in rows], "candidate_id": candidate_id}


@router.put("/candidates/{candidate_id}/sections/{section_key}")
def save_candidate_dossier_section(
    candidate_id: str,
    section_key: str,
    payload: DossierSectionInput,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, _ = _membership(current_user, db)
    if not section_key or len(section_key) > 80 or not section_key.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=422, detail="Section key must be a short lowercase slug.")
    candidate_exists = db.execute(text("""
        SELECT 1 FROM peptide_discovery_candidates WHERE id=:candidate
    """), {"candidate": candidate_id}).scalar_one_or_none()
    if not candidate_exists:
        raise HTTPException(status_code=404, detail="Peptide discovery folder not found.")
    references = [item.model_dump(mode="json") for item in payload.references]
    media = [item.model_dump(mode="json") for item in payload.media]
    row = db.execute(text("""
        INSERT INTO peptide_dossier_sections
            (candidate_id, organization_id, section_key, content, references, media, updated_by)
        VALUES (:candidate, :org, :section_key, CAST(:content AS jsonb),
                CAST(:references AS jsonb), CAST(:media AS jsonb), :user_id)
        ON CONFLICT (candidate_id, organization_id, section_key) DO UPDATE SET
            content=EXCLUDED.content, references=EXCLUDED.references,
            media=EXCLUDED.media, updated_by=EXCLUDED.updated_by
        RETURNING id, section_key, content, references, media, revision, updated_at
    """), {
        "candidate": candidate_id, "org": organization_id, "section_key": section_key,
        "content": json.dumps(payload.content, ensure_ascii=False),
        "references": json.dumps(references, ensure_ascii=False),
        "media": json.dumps(media, ensure_ascii=False),
        "user_id": current_user["id"],
    }).mappings().one()
    db.commit()
    return {"section": dict(row), "notice": "Section saved; an immutable revision was recorded."}
