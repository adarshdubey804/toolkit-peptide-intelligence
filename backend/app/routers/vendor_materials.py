from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl, model_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/vendor-materials", tags=["vendor material and batch traceability"])
SUBMIT_ROLES = {"organization_admin", "curator", "researcher"}
REVIEW_ROLES = {"organization_admin", "curator", "reviewer"}


class SourceFields(BaseModel):
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    evidence_scope: str = Field(min_length=5, max_length=1000)


class OfferingSubmission(SourceFields):
    vendor_id: UUID
    site_id: UUID | None = None
    service_id: UUID | None = None
    peptide_id: UUID
    chemical_form_id: UUID
    product_name: str = Field(min_length=2, max_length=300)
    catalogue_reference: str | None = Field(default=None, max_length=200)
    material_description: str | None = Field(default=None, max_length=3000)
    supplied_material_label: str | None = Field(default=None, max_length=500)
    packaging_description: str | None = Field(default=None, max_length=1000)
    stated_storage_conditions: str | None = Field(default=None, max_length=1000)
    stated_shipping_conditions: str | None = Field(default=None, max_length=1000)


class BatchSubmission(SourceFields):
    lot_identifier: str = Field(min_length=1, max_length=200)
    manufacturer_batch_identifier: str | None = Field(default=None, max_length=200)
    manufactured_on: date | None = None
    retest_on: date | None = None
    expires_on: date | None = None
    quantity: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=6)
    quantity_unit: str | None = Field(default=None, max_length=40)
    availability_statement: Literal[
        "unknown", "stated_available", "stated_unavailable", "discontinued",
        "quarantined", "recalled", "depleted"
    ] = "unknown"
    storage_conditions: str | None = Field(default=None, max_length=1000)
    shipping_conditions: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.manufactured_on and self.retest_on and self.retest_on < self.manufactured_on:
            raise ValueError("Retest date cannot precede manufacture date.")
        if self.manufactured_on and self.expires_on and self.expires_on < self.manufactured_on:
            raise ValueError("Expiry date cannot precede manufacture date.")
        return self


class BatchTestResultSubmission(SourceFields):
    test_id: UUID
    method_id: UUID
    laboratory_service_id: UUID | None = None
    tested_at: datetime | None = None
    sample_identifier: str | None = Field(default=None, max_length=200)
    sample_matrix: str | None = Field(default=None, max_length=500)
    method_version: str | None = Field(default=None, max_length=100)
    instrument_platform: str | None = Field(default=None, max_length=500)
    reference_standard: str | None = Field(default=None, max_length=1000)
    acceptance_criteria_source_name: str | None = Field(default=None, min_length=2, max_length=120)
    acceptance_criteria_source_identifier: str | None = Field(default=None, min_length=1, max_length=200)
    acceptance_criteria_source_url: HttpUrl | None = None
    observed_value: Decimal | None = Field(default=None, max_digits=24, decimal_places=10)
    observed_text: str | None = Field(default=None, max_length=2000)
    result_unit: str | None = Field(default=None, max_length=100)
    result_status: Literal["pass", "fail", "inconclusive", "not_reported"] = "not_reported"
    interpretation: str | None = Field(default=None, max_length=3000)

    @model_validator(mode="after")
    def validate_result_and_criteria_source(self):
        if self.observed_value is None and not (self.observed_text and self.observed_text.strip()):
            raise ValueError("Provide an observed numeric value or a non-empty observed text result.")
        criteria_parts = (
            self.acceptance_criteria_source_name,
            self.acceptance_criteria_source_identifier,
            self.acceptance_criteria_source_url,
        )
        if any(value is not None for value in criteria_parts) and not all(value is not None for value in criteria_parts):
            raise ValueError("Acceptance-criteria provenance requires source name, identifier and URL.")
        return self


class MaterialDecision(BaseModel):
    decision: Literal["verified", "rejected", "needs_changes"]
    rationale: str = Field(min_length=20, max_length=4000)
    visibility_scope: Literal["public", "organization", "restricted"] = "restricted"


def _membership(user: dict, db: Session):
    organization_id = user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    role = db.execute(text("""
        SELECT role FROM organization_memberships
        WHERE organization_id=:org AND user_id=:user_id AND membership_status='active'
    """), {"org": organization_id, "user_id": user["id"]}).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    return organization_id, role


def _source_record(db: Session, name: str, identifier: str, url: str):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Evidence sources must use HTTPS without embedded credentials.")
    return db.execute(text("""
        INSERT INTO source_records (source_name, source_identifier, source_url, retrieved_at, raw_metadata)
        VALUES (:name, :identifier, :url, now(), '{}'::jsonb)
        ON CONFLICT (source_name, source_identifier)
        DO UPDATE SET source_url=EXCLUDED.source_url, last_seen_at=now()
        RETURNING id
    """), {"name": name.strip(), "identifier": identifier.strip(), "url": url}).scalar_one()


def _audit(db: Session, user: dict, org, action: str, entity_type: str, entity_id, metadata: dict):
    db.execute(text("""
        INSERT INTO audit_events
            (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, :action, :entity_type, :entity_id, CAST(:metadata AS jsonb))
    """), {
        "actor": user["id"], "org": org, "action": action, "entity_type": entity_type,
        "entity_id": entity_id, "metadata": __import__("json").dumps(metadata, default=str),
    })


def _require_submitter(user: dict, db: Session):
    org, role = _membership(user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your organization role cannot submit vendor material records.")
    return org


@router.get("/offerings")
def public_material_offerings(
    db: Annotated[Session, Depends(get_db)],
    peptide_id: UUID | None = None,
    chemical_form_id: UUID | None = None,
    vendor_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    rows = db.execute(text("""
        SELECT o.id, o.vendor_id, v.legal_name AS vendor_name, o.site_id,
               site.site_name, o.peptide_id, p.preferred_name AS peptide_name,
               o.chemical_form_id, f.form_name, o.product_name, o.catalogue_reference,
               o.material_description, o.packaging_description, o.stated_storage_conditions,
               o.stated_shipping_conditions, o.reviewed_at,
               sr.source_name, sr.source_identifier, sr.source_url
        FROM vendor_material_offerings o
        JOIN vendors v ON v.id=o.vendor_id
          AND v.review_status='verified' AND v.verification_status='verified'
        JOIN peptides p ON p.id=o.peptide_id AND p.review_status='verified'
        JOIN peptide_chemical_forms f ON f.id=o.chemical_form_id AND f.review_status='verified'
        LEFT JOIN vendor_sites site ON site.id=o.site_id AND site.review_status='verified'
        JOIN source_records sr ON sr.id=o.source_id
        WHERE o.review_status='verified' AND o.visibility_scope='public'
          AND (:peptide IS NULL OR o.peptide_id=:peptide)
          AND (:form IS NULL OR o.chemical_form_id=:form)
          AND (:vendor IS NULL OR o.vendor_id=:vendor)
        ORDER BY v.legal_name, o.product_name
        LIMIT :limit
    """), {"peptide": peptide_id, "form": chemical_form_id, "vendor": vendor_id, "limit": limit}).mappings().all()
    return {
        "items": [dict(row) for row in rows],
        "count": len(rows),
        "scope": "Only public, curator-reviewed offerings for verified peptide identities, chemical forms and vendors are listed. Listings do not establish live stock or batch quality."
    }


@router.post("/offerings", status_code=201)
def submit_material_offering(
    payload: OfferingSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    org = _require_submitter(current_user, db)
    vendor = db.execute(text("""
        SELECT id FROM vendors
        WHERE id=:vendor AND organization_id=:org
          AND review_status='verified' AND verification_status='verified'
    """), {"vendor": payload.vendor_id, "org": org}).scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Verified vendor identity was not found in this organization.")
    peptide = db.execute(text("""
        SELECT p.id FROM peptides p
        JOIN peptide_chemical_forms f ON f.peptide_id=p.id
        WHERE p.id=:peptide AND f.id=:form
          AND p.review_status='verified' AND f.review_status='verified'
    """), {"peptide": payload.peptide_id, "form": payload.chemical_form_id}).scalar_one_or_none()
    if not peptide:
        raise HTTPException(status_code=404, detail="Verified peptide and exact chemical form combination was not found.")
    if payload.site_id:
        site = db.execute(text("""
            SELECT id FROM vendor_sites WHERE id=:site AND vendor_id=:vendor
              AND organization_id=:org AND review_status='verified'
        """), {"site": payload.site_id, "vendor": payload.vendor_id, "org": org}).scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=422, detail="Selected site is not a verified site of this vendor.")
    if payload.service_id:
        service = db.execute(text("""
            SELECT id FROM vendor_services
            WHERE id=:service AND vendor_id=:vendor AND review_status='verified'
              AND (:site IS NULL OR site_id=:site)
        """), {"service": payload.service_id, "vendor": payload.vendor_id, "site": payload.site_id}).scalar_one_or_none()
        if not service:
            raise HTTPException(status_code=422, detail="Selected service is not a verified service of this vendor and site.")
    source_id = _source_record(db, payload.source_name, payload.source_identifier, str(payload.source_url))
    row = db.execute(text("""
        INSERT INTO vendor_material_offerings (
            organization_id, vendor_id, site_id, service_id, peptide_id, chemical_form_id,
            product_name, catalogue_reference, material_description, supplied_material_label,
            packaging_description, stated_storage_conditions, stated_shipping_conditions,
            source_id, review_status, submitted_by, visibility_scope
        ) VALUES (
            :org, :vendor, :site, :service, :peptide, :form, :name, :catalogue,
            :description, :label, :packaging, :storage, :shipping, :source,
            'in_review', :submitter, 'restricted'
        )
        RETURNING id, vendor_id, peptide_id, chemical_form_id, product_name, review_status, created_at
    """), {
        "org": org, "vendor": payload.vendor_id, "site": payload.site_id, "service": payload.service_id,
        "peptide": payload.peptide_id, "form": payload.chemical_form_id, "name": payload.product_name.strip(),
        "catalogue": payload.catalogue_reference, "description": payload.material_description,
        "label": payload.supplied_material_label, "packaging": payload.packaging_description,
        "storage": payload.stated_storage_conditions, "shipping": payload.stated_shipping_conditions,
        "source": source_id, "submitter": current_user["id"],
    }).mappings().one()
    _audit(db, current_user, org, "vendor_material_offering_submitted", "vendor_material_offering",
           row["id"], {"source_record_id": str(source_id), "chemical_form_id": str(payload.chemical_form_id)})
    db.commit()
    return {**dict(row), "visibility_scope": "restricted",
            "note": "The offering remains restricted and in review. It is not public or a live-inventory assertion."}


@router.get("/offerings/{offering_id}/batches")
def list_organization_batches(
    offering_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    org, _ = _membership(current_user, db)
    offering = db.execute(text("""
        SELECT id FROM vendor_material_offerings WHERE id=:id AND organization_id=:org
    """), {"id": offering_id, "org": org}).scalar_one_or_none()
    if not offering:
        raise HTTPException(status_code=404, detail="Material offering was not found in this organization.")
    rows = db.execute(text("""
        SELECT b.id, b.offering_id, b.lot_identifier, b.manufacturer_batch_identifier,
               b.manufactured_on, b.retest_on, b.expires_on, b.quantity, b.quantity_unit,
               b.availability_statement, b.storage_conditions, b.shipping_conditions,
               b.review_status, b.created_at, sr.source_name, sr.source_identifier, sr.source_url
        FROM vendor_material_batches b
        JOIN source_records sr ON sr.id=b.source_id
        WHERE b.offering_id=:offering AND b.organization_id=:org
        ORDER BY b.created_at DESC LIMIT :limit
    """), {"offering": offering_id, "org": org, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows),
            "scope": "Physical lot records are visible only to the owning organization."}


@router.post("/offerings/{offering_id}/batches", status_code=201)
def submit_material_batch(
    offering_id: UUID,
    payload: BatchSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    org = _require_submitter(current_user, db)
    offering = db.execute(text("""
        SELECT id FROM vendor_material_offerings
        WHERE id=:id AND organization_id=:org
    """), {"id": offering_id, "org": org}).scalar_one_or_none()
    if not offering:
        raise HTTPException(status_code=404, detail="Material offering was not found in this organization.")
    source_id = _source_record(db, payload.source_name, payload.source_identifier, str(payload.source_url))
    try:
        row = db.execute(text("""
            INSERT INTO vendor_material_batches (
                offering_id, organization_id, lot_identifier, manufacturer_batch_identifier,
                manufactured_on, retest_on, expires_on, quantity, quantity_unit,
                availability_statement, storage_conditions, shipping_conditions,
                source_id, review_status, submitted_by
            ) VALUES (
                :offering, :org, :lot, :manufacturer_lot, :manufactured, :retest, :expires,
                :quantity, :unit, :availability, :storage, :shipping, :source, 'in_review', :submitter
            )
            RETURNING id, offering_id, lot_identifier, manufacturer_batch_identifier,
                      manufactured_on, retest_on, expires_on, quantity, quantity_unit,
                      availability_statement, review_status, created_at
        """), {
            "offering": offering_id, "org": org, "lot": payload.lot_identifier.strip(),
            "manufacturer_lot": payload.manufacturer_batch_identifier, "manufactured": payload.manufactured_on,
            "retest": payload.retest_on, "expires": payload.expires_on, "quantity": payload.quantity,
            "unit": payload.quantity_unit, "availability": payload.availability_statement,
            "storage": payload.storage_conditions, "shipping": payload.shipping_conditions,
            "source": source_id, "submitter": current_user["id"],
        }).mappings().one()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="That lot identifier already exists for this material offering.") from exc
    _audit(db, current_user, org, "vendor_material_batch_submitted", "vendor_material_batch",
           row["id"], {"offering_id": str(offering_id), "source_record_id": str(source_id)})
    db.commit()
    return {**dict(row), "note": "Supplier-stated availability is not live inventory; this lot remains in review."}


@router.post("/batches/{batch_id}/test-results", status_code=201)
def submit_batch_test_result(
    batch_id: UUID,
    payload: BatchTestResultSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    org = _require_submitter(current_user, db)
    batch = db.execute(text("""
        SELECT b.id, o.vendor_id, o.site_id
        FROM vendor_material_batches b
        JOIN vendor_material_offerings o ON o.id=b.offering_id
        WHERE b.id=:batch AND b.organization_id=:org AND o.organization_id=:org
    """), {"batch": batch_id, "org": org}).mappings().first()
    if not batch:
        raise HTTPException(status_code=404, detail="Material batch was not found in this organization.")
    test = db.execute(text("""
        SELECT id FROM analytical_test_catalogue WHERE id=:id AND review_status='verified'
    """), {"id": payload.test_id}).scalar_one_or_none()
    method = db.execute(text("""
        SELECT id FROM analytical_methods WHERE id=:id AND review_status='verified'
    """), {"id": payload.method_id}).scalar_one_or_none()
    if not test or not method:
        raise HTTPException(status_code=422, detail="Batch results must reference verified analytical test and method catalogue records.")
    if payload.laboratory_service_id:
        service = db.execute(text("""
            SELECT id FROM vendor_services
            WHERE id=:service AND vendor_id=:vendor AND review_status='verified'
              AND (:site IS NULL OR site_id=:site)
        """), {"service": payload.laboratory_service_id, "vendor": batch["vendor_id"], "site": batch["site_id"]}).scalar_one_or_none()
        if not service:
            raise HTTPException(status_code=422, detail="Laboratory service must belong to the offering vendor and selected site.")
    report_source_id = _source_record(db, payload.source_name, payload.source_identifier, str(payload.source_url))
    criteria_source_id = None
    if payload.acceptance_criteria_source_url:
        criteria_source_id = _source_record(
            db, payload.acceptance_criteria_source_name,
            payload.acceptance_criteria_source_identifier,
            str(payload.acceptance_criteria_source_url),
        )
    row = db.execute(text("""
        INSERT INTO batch_analytical_test_results (
            batch_id, organization_id, test_id, method_id, laboratory_service_id, tested_at,
            sample_identifier, sample_matrix, method_version, instrument_platform, reference_standard,
            acceptance_criteria_source_id, observed_value, observed_text, result_unit, result_status,
            interpretation, report_source_id, review_status, submitted_by
        ) VALUES (
            :batch, :org, :test, :method, :service, :tested_at, :sample, :matrix, :version,
            :platform, :standard, :criteria_source, :value, :observed_text, :unit, :status,
            :interpretation, :report_source, 'in_review', :submitter
        )
        RETURNING id, batch_id, test_id, method_id, tested_at, observed_value, observed_text,
                  result_unit, result_status, review_status, created_at
    """), {
        "batch": batch_id, "org": org, "test": payload.test_id, "method": payload.method_id,
        "service": payload.laboratory_service_id, "tested_at": payload.tested_at,
        "sample": payload.sample_identifier, "matrix": payload.sample_matrix,
        "version": payload.method_version, "platform": payload.instrument_platform,
        "standard": payload.reference_standard, "criteria_source": criteria_source_id,
        "value": payload.observed_value, "observed_text": payload.observed_text,
        "unit": payload.result_unit, "status": payload.result_status,
        "interpretation": payload.interpretation, "report_source": report_source_id,
        "submitter": current_user["id"],
    }).mappings().one()
    _audit(db, current_user, org, "batch_analytical_result_submitted", "batch_analytical_test_result",
           row["id"], {"batch_id": str(batch_id), "test_id": str(payload.test_id),
                       "method_id": str(payload.method_id), "report_source_id": str(report_source_id)})
    db.commit()
    return {**dict(row), "note": "Reported result is unverified until independent review; a pass label does not establish method validation or product suitability."}


@router.get("/reviews")
def material_review_queue(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    org, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    offerings = db.execute(text("""
        SELECT 'offering' AS record_type, o.id, o.product_name AS label, o.submitted_by,
               o.review_status, o.created_at, sr.source_name, sr.source_identifier, sr.source_url
        FROM vendor_material_offerings o JOIN source_records sr ON sr.id=o.source_id
        WHERE o.organization_id=:org AND o.review_status='in_review'
        ORDER BY o.created_at LIMIT :limit
    """), {"org": org, "limit": limit}).mappings().all()
    batches = db.execute(text("""
        SELECT 'batch' AS record_type, b.id, b.lot_identifier AS label, b.submitted_by,
               b.review_status, b.created_at, sr.source_name, sr.source_identifier, sr.source_url
        FROM vendor_material_batches b JOIN source_records sr ON sr.id=b.source_id
        WHERE b.organization_id=:org AND b.review_status='in_review'
        ORDER BY b.created_at LIMIT :limit
    """), {"org": org, "limit": limit}).mappings().all()
    results = db.execute(text("""
        SELECT 'test_result' AS record_type, r.id, t.test_name AS label, r.submitted_by,
               r.review_status, r.created_at, sr.source_name, sr.source_identifier, sr.source_url
        FROM batch_analytical_test_results r
        JOIN analytical_test_catalogue t ON t.id=r.test_id
        JOIN source_records sr ON sr.id=r.report_source_id
        WHERE r.organization_id=:org AND r.review_status='in_review'
        ORDER BY r.created_at LIMIT :limit
    """), {"org": org, "limit": limit}).mappings().all()
    items = [dict(row) for row in (*offerings, *batches, *results)]
    items.sort(key=lambda item: item["created_at"])
    return {"items": items[:limit], "count": min(len(items), limit),
            "scope": "Organization-scoped queue. Submitters cannot review their own records."}


@router.post("/reviews/{record_type}/{record_id}/decisions", status_code=201)
def decide_material_record(
    record_type: Literal["offering", "batch", "test_result"],
    record_id: UUID,
    payload: MaterialDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    org, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    table = {
        "offering": "vendor_material_offerings",
        "batch": "vendor_material_batches",
        "test_result": "batch_analytical_test_results",
    }[record_type]
    record = db.execute(text(f"""
        SELECT id, submitted_by FROM {table}
        WHERE id=:id AND organization_id=:org AND review_status='in_review'
        FOR UPDATE
    """), {"id": record_id, "org": org}).mappings().first()
    if not record:
        raise HTTPException(status_code=404, detail="Pending material record was not found in this organization.")
    if str(record["submitted_by"]) == str(current_user["id"]):
        raise HTTPException(status_code=409, detail="A submitter cannot review their own material record.")
    if record_type == "test_result":
        db.execute(text("""
            INSERT INTO batch_analytical_test_result_decisions
                (result_id, organization_id, reviewer_id, decision, rationale)
            VALUES (:id, :org, :reviewer, :decision, :rationale)
        """), {"id": record_id, "org": org, "reviewer": current_user["id"],
               "decision": payload.decision, "rationale": payload.rationale.strip()})
    status = "verified" if payload.decision == "verified" else (
        "rejected" if payload.decision == "rejected" else "draft"
    )
    if record_type == "offering":
        db.execute(text("""
            UPDATE vendor_material_offerings
            SET review_status=:status, reviewed_by=:reviewer, reviewed_at=now(),
                visibility_scope=:visibility_scope
            WHERE id=:id
        """), {"status": status, "reviewer": current_user["id"], "id": record_id,
               "visibility_scope": payload.visibility_scope if status == "verified" else "restricted"})
    else:
        db.execute(text(f"""
            UPDATE {table} SET review_status=:status, reviewed_by=:reviewer, reviewed_at=now()
            WHERE id=:id
        """), {"status": status, "reviewer": current_user["id"], "id": record_id})
    _audit(db, current_user, org, f"vendor_material_{record_type}_decided", record_type,
           record_id, {"decision": payload.decision, "rationale": payload.rationale.strip()})
    db.commit()
    return {"record_id": str(record_id), "record_type": record_type,
            "review_status": status, "decision": payload.decision,
            "visibility_scope": payload.visibility_scope if record_type == "offering" and status == "verified" else "restricted"}
