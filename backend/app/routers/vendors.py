from datetime import date
from typing import Annotated, Literal
from uuid import UUID
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/vendors", tags=["vendor and laboratory directory"])
SUBMIT_ROLES = {"organization_admin", "curator", "researcher"}
REVIEW_ROLES = {"organization_admin", "curator", "reviewer"}


class VendorSubmission(BaseModel):
    legal_name: str = Field(min_length=2, max_length=300)
    website_url: HttpUrl
    country_code: str = Field(min_length=2, max_length=2)
    vendor_type: Literal["peptide_manufacturer", "cdmo", "cro", "analytical_laboratory", "research_reagent_supplier", "other"]
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    evidence_scope: str = Field(min_length=5, max_length=1000)


class VendorServiceSubmission(BaseModel):
    service_name: str = Field(min_length=2, max_length=200)
    capability_description: str = Field(min_length=10, max_length=3000)
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl


class VendorDecision(BaseModel):
    decision: Literal["verified", "rejected", "needs_changes"]
    rationale: str = Field(min_length=20, max_length=4000)


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


def _source_host(url: str):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Evidence source must use HTTPS without embedded credentials.")
    return url


def _source_record(db: Session, source_name: str, identifier: str, url: str):
    url = _source_host(url)
    row = db.execute(text("""
        INSERT INTO source_records (source_name, source_identifier, source_url, retrieved_at, raw_metadata)
        VALUES (:name, :identifier, :url, now(), '{}'::jsonb)
        ON CONFLICT (source_name, source_identifier)
        DO UPDATE SET source_url=EXCLUDED.source_url, last_seen_at=now()
        RETURNING id
    """), {"name": source_name, "identifier": identifier, "url": url}).scalar_one()
    return row


@router.get("")
def verified_vendor_directory(
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(default=None, min_length=2, max_length=100),
    vendor_type: str | None = None,
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Public directory; only records with verified identity and review state are discoverable."""
    rows = db.execute(text("""
        SELECT v.id, v.legal_name, v.website_url, v.country_code, v.vendor_type,
               v.verification_status, v.last_verified_at,
               COALESCE(jsonb_agg(DISTINCT jsonb_build_object(
                   'service_name', vs.service_name,
                   'capability_description', vs.capability_description
               )) FILTER (WHERE vs.id IS NOT NULL), '[]'::jsonb) AS services,
               COALESCE(jsonb_agg(DISTINCT jsonb_build_object(
                   'certification_name', vc.certification_name,
                   'issuing_body', vc.issuing_body,
                   'scope', vc.scope,
                   'valid_until', vc.valid_until,
                   'verification_status', vc.verification_status
               )) FILTER (WHERE vc.id IS NOT NULL), '[]'::jsonb) AS certifications
        FROM vendors v
        LEFT JOIN vendor_services vs ON vs.vendor_id=v.id AND vs.review_status='verified'
        LEFT JOIN vendor_certifications vc ON vc.vendor_id=v.id AND vc.verification_status='verified'
        WHERE v.review_status='verified' AND v.verification_status='verified'
          AND (:q IS NULL OR v.legal_name ILIKE '%' || :q || '%' OR v.vendor_type ILIKE '%' || :q || '%')
          AND (:vendor_type IS NULL OR v.vendor_type=:vendor_type)
          AND (:country_code IS NULL OR v.country_code=:country_code)
        GROUP BY v.id
        ORDER BY v.legal_name
        LIMIT :limit
    """), {"q": q, "vendor_type": vendor_type, "country_code": country_code.upper() if country_code else None, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows), "scope": "Only curator-reviewed vendor identities with verified status are listed."}


@router.post("", status_code=201)
def submit_vendor(
    payload: VendorSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot submit vendor records.")
    source_id = _source_record(db, payload.source_name, payload.source_identifier, str(payload.source_url))
    vendor = db.execute(text("""
        INSERT INTO vendors (legal_name, website_url, country_code, vendor_type,
                             verification_status, review_status, submitted_by, organization_id)
        VALUES (:name, :website, :country, :type, 'unverified', 'in_review', :submitter, :org)
        RETURNING id, legal_name, review_status, verification_status, created_at
    """), {"name": payload.legal_name.strip(), "website": str(payload.website_url),
           "country": payload.country_code.upper(), "type": payload.vendor_type,
           "submitter": current_user["id"], "org": organization_id}).mappings().one()
    db.execute(text("""
        INSERT INTO vendor_sources (vendor_id, source_record_id, evidence_scope)
        VALUES (:vendor, :source, :scope)
    """), {"vendor": vendor["id"], "source": source_id, "scope": payload.evidence_scope})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'vendor_submitted', 'vendor', :id,
                jsonb_build_object('vendor_type', :type, 'source_record_id', :source))
    """), {"actor": current_user["id"], "org": organization_id, "id": vendor["id"],
           "type": payload.vendor_type, "source": str(source_id)})
    db.commit()
    return dict(vendor)


@router.post("/{vendor_id}/services", status_code=201)
def submit_vendor_service(
    vendor_id: UUID,
    payload: VendorServiceSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot submit vendor capabilities.")
    vendor = db.execute(text("""
        SELECT id FROM vendors
        WHERE id=:id AND organization_id=:org
          AND review_status='verified' AND verification_status='verified'
    """), {"id": vendor_id, "org": organization_id}).mappings().first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Verified vendor was not found in this organization.")
    source_id = _source_record(db, payload.source_name, payload.source_identifier, str(payload.source_url))
    service = db.execute(text("""
        INSERT INTO vendor_services
            (vendor_id, service_name, capability_description, evidence_source_id, review_status, submitted_by)
        VALUES (:vendor, :name, :description, :source, 'in_review', :submitter)
        RETURNING id, service_name, capability_description, review_status
    """), {"vendor": vendor_id, "name": payload.service_name.strip(),
           "description": payload.capability_description.strip(), "source": source_id,
           "submitter": current_user["id"]}).mappings().one()
    db.execute(text("""
        INSERT INTO vendor_sources (vendor_id, source_record_id, evidence_scope)
        VALUES (:vendor, :source, :scope) ON CONFLICT DO NOTHING
    """), {"vendor": vendor_id, "source": source_id, "scope": "Service capability: " + payload.service_name})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'vendor_service_submitted', 'vendor', :id,
                jsonb_build_object('service_id', :service, 'source_record_id', :source))
    """), {"actor": current_user["id"], "org": organization_id, "id": vendor_id,
           "service": str(service["id"]), "source": str(source_id)})
    db.commit()
    return dict(service)


@router.get("/reviews")
def vendor_review_queue(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    rows = db.execute(text("""
        SELECT v.id, v.legal_name, v.website_url, v.country_code, v.vendor_type,
               v.review_status, v.verification_status, v.submitted_by, v.created_at,
               COALESCE(jsonb_agg(DISTINCT jsonb_build_object(
                   'source_name', sr.source_name, 'source_identifier', sr.source_identifier,
                   'source_url', sr.source_url, 'evidence_scope', vsrc.evidence_scope
               )) FILTER (WHERE sr.id IS NOT NULL), '[]'::jsonb) AS sources
        FROM vendors v
        LEFT JOIN vendor_sources vsrc ON vsrc.vendor_id=v.id
        LEFT JOIN source_records sr ON sr.id=vsrc.source_record_id
        WHERE v.review_status='in_review' AND v.organization_id=:org
        GROUP BY v.id ORDER BY v.created_at ASC LIMIT :limit
    """), {"org": organization_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@router.post("/{vendor_id}/decisions", status_code=201)
def decide_vendor(
    vendor_id: UUID,
    payload: VendorDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    vendor = db.execute(text("""
        SELECT v.* FROM vendors v
        WHERE v.id=:id AND v.review_status='in_review' AND v.organization_id=:org
        FOR UPDATE OF v
    """), {"id": vendor_id, "org": organization_id}).mappings().first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor review not found in this organization.")
    if str(vendor["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="A submitter cannot review their own vendor record.")
    if payload.decision == "verified":
        sources = db.execute(text("""
            SELECT count(*) FROM vendor_sources vs
            JOIN source_records sr ON sr.id=vs.source_record_id
            WHERE vs.vendor_id=:vendor AND sr.source_url IS NOT NULL
        """), {"vendor": vendor_id}).scalar_one()
        if sources < 1:
            raise HTTPException(status_code=409, detail="Verification requires an original source URL.")
    db.execute(text("""
        INSERT INTO vendor_review_decisions (vendor_id, organization_id, reviewer_id, decision, rationale)
        VALUES (:vendor, :org, :reviewer, :decision, :rationale)
    """), {"vendor": vendor_id, "org": organization_id, "reviewer": current_user["id"],
           "decision": payload.decision, "rationale": payload.rationale.strip()})
    new_status = "verified" if payload.decision == "verified" else ("rejected" if payload.decision == "rejected" else "draft")
    db.execute(text("""
        UPDATE vendors SET review_status=:status, verification_status=:verification,
            reviewed_by=:reviewer, reviewed_at=now(), last_verified_at=CASE WHEN :status='verified' THEN now() ELSE last_verified_at END,
            verification_notes=:rationale
        WHERE id=:vendor
    """), {"status": new_status, "verification": "verified" if payload.decision == "verified" else "unverified",
           "reviewer": current_user["id"], "rationale": payload.rationale.strip(), "vendor": vendor_id})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'vendor_review_decided', 'vendor', :id,
                jsonb_build_object('decision', :decision))
    """), {"actor": current_user["id"], "org": organization_id, "id": vendor_id, "decision": payload.decision})
    db.commit()
    return {"vendor_id": str(vendor_id), "review_status": new_status, "decision": payload.decision}


@router.get("/services/reviews")
def vendor_service_review_queue(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    rows = db.execute(text("""
        SELECT vs.id, vs.vendor_id, v.legal_name, vs.service_name,
               vs.capability_description, vs.review_status, vs.submitted_by,
               sr.source_name, sr.source_identifier, sr.source_url
        FROM vendor_services vs
        JOIN vendors v ON v.id=vs.vendor_id
        LEFT JOIN source_records sr ON sr.id=vs.evidence_source_id
        WHERE v.organization_id=:org AND v.review_status='verified'
          AND v.verification_status='verified' AND vs.review_status='in_review'
        ORDER BY vs.id LIMIT :limit
    """), {"org": organization_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows),
            "scope": "Service capability claims are independently reviewed after vendor identity verification."}


@router.post("/services/{service_id}/decisions", status_code=201)
def decide_vendor_service(
    service_id: UUID,
    payload: VendorDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    service = db.execute(text("""
        SELECT vs.id, vs.vendor_id, vs.submitted_by, vs.evidence_source_id
        FROM vendor_services vs
        JOIN vendors v ON v.id=vs.vendor_id
        WHERE vs.id=:id AND v.organization_id=:org
          AND v.review_status='verified' AND v.verification_status='verified'
          AND vs.review_status='in_review'
        FOR UPDATE OF vs
    """), {"id": service_id, "org": organization_id}).mappings().first()
    if not service:
        raise HTTPException(status_code=404, detail="Pending service review was not found in this organization.")
    if str(service["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="A service submitter cannot review their own capability claim.")
    source = db.execute(text("""
        SELECT source_url FROM source_records WHERE id=:id
    """), {"id": service["evidence_source_id"]}).scalar_one_or_none()
    if payload.decision == "verified" and not source:
        raise HTTPException(status_code=409, detail="Service verification requires a source URL.")
    db.execute(text("""
        INSERT INTO vendor_service_decisions
            (service_id, organization_id, reviewer_id, decision, rationale)
        VALUES (:service, :org, :reviewer, :decision, :rationale)
    """), {"service": service_id, "org": organization_id, "reviewer": current_user["id"],
           "decision": payload.decision, "rationale": payload.rationale.strip()})
    new_status = "verified" if payload.decision == "verified" else (
        "rejected" if payload.decision == "rejected" else "draft"
    )
    db.execute(text("""
        UPDATE vendor_services
        SET review_status=:status, reviewed_by=:reviewer, reviewed_at=now(),
            verified_at=CASE WHEN :status='verified' THEN now() ELSE NULL END
        WHERE id=:id
    """), {"status": new_status, "reviewer": current_user["id"], "id": service_id})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'vendor_service_review_decided', 'vendor_service', :id,
                jsonb_build_object('decision', :decision, 'vendor_id', :vendor))
    """), {"actor": current_user["id"], "org": organization_id, "id": service_id,
           "decision": payload.decision, "vendor": str(service["vendor_id"])})
    db.commit()
    return {"service_id": str(service_id), "review_status": new_status, "decision": payload.decision}



class VendorServiceEvidenceLinkSubmission(BaseModel):
    relationship_type: Literal[
        "peptide_supply", "peptide_manufacturing",
        "peptide_specific_testing", "method_service", "formulation_development"
    ]
    peptide_id: UUID | None = None
    method_id: UUID | None = None
    evidence_scope: str = Field(min_length=5, max_length=1500)
    limitations: str = Field(min_length=10, max_length=2000)
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl


class VendorServiceEvidenceLinkDecision(BaseModel):
    decision: Literal["verified", "rejected", "needs_changes"]
    rationale: str = Field(min_length=20, max_length=4000)


class VendorCertificationSubmission(BaseModel):
    certification_name: str = Field(min_length=2, max_length=200)
    issuing_body: str = Field(min_length=2, max_length=200)
    certificate_reference: str = Field(min_length=2, max_length=200)
    scope: str = Field(min_length=5, max_length=2000)
    valid_from: date | None = None
    valid_until: date | None = None
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl


@router.post("/{vendor_id}/certifications", status_code=201)
def submit_vendor_certification(
    vendor_id: UUID,
    payload: VendorCertificationSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot submit certification evidence.")
    vendor = db.execute(text("SELECT id, submitted_by FROM vendors WHERE id=:id AND organization_id=:org AND review_status='in_review'"),
                        {"id": vendor_id, "org": organization_id}).mappings().first()
    if not vendor or str(vendor["submitted_by"]) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Your submitted vendor record was not found.")
    source_id = _source_record(db, payload.source_name, payload.source_identifier, str(payload.source_url))
    certification = db.execute(text("""
        INSERT INTO vendor_certifications
            (vendor_id, certification_name, issuing_body, certificate_reference, scope,
             valid_from, valid_until, verification_source_id, verification_status)
        VALUES (:vendor, :name, :issuer, :reference, :scope, :valid_from, :valid_until, :source, 'unverified')
        RETURNING id, certification_name, issuing_body, scope, valid_from, valid_until, verification_status
    """), {"vendor": vendor_id, "name": payload.certification_name.strip(),
           "issuer": payload.issuing_body.strip(), "reference": payload.certificate_reference.strip(),
           "scope": payload.scope.strip(), "valid_from": payload.valid_from,
           "valid_until": payload.valid_until, "source": source_id}).mappings().one()
    db.execute(text("""
        INSERT INTO vendor_sources (vendor_id, source_record_id, evidence_scope)
        VALUES (:vendor, :source, :scope) ON CONFLICT DO NOTHING
    """), {"vendor": vendor_id, "source": source_id,
           "scope": "Certification evidence: " + payload.certification_name})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'vendor_certification_submitted', 'vendor', :id,
                jsonb_build_object('certification_id', :certification, 'source_record_id', :source))
    """), {"actor": current_user["id"], "org": organization_id, "id": vendor_id,
           "certification": str(certification["id"]), "source": str(source_id)})
    db.commit()
    return dict(certification)


class VendorCertificationDecision(BaseModel):
    decision: Literal["verified", "rejected", "needs_changes"]
    rationale: str = Field(min_length=20, max_length=4000)


@router.get("/certifications/reviews")
def vendor_certification_review_queue(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    rows = db.execute(text("""
        SELECT vc.id, vc.vendor_id, v.legal_name, vc.certification_name,
               vc.issuing_body, vc.certificate_reference, vc.scope,
               vc.valid_from, vc.valid_until, vc.verification_status,
               sr.source_name, sr.source_identifier, sr.source_url,
               v.submitted_by
        FROM vendor_certifications vc
        JOIN vendors v ON v.id=vc.vendor_id
        LEFT JOIN source_records sr ON sr.id=vc.verification_source_id
        WHERE v.organization_id=:org AND vc.verification_status='unverified'
          AND v.review_status='verified' AND v.verification_status='verified'
        ORDER BY vc.id LIMIT :limit
    """), {"org": organization_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows),
            "scope": "Certification claims are reviewed independently of vendor identity."}


@router.post("/certifications/{certification_id}/decisions", status_code=201)
def decide_vendor_certification(
    certification_id: UUID,
    payload: VendorCertificationDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    certification = db.execute(text("""
        SELECT vc.id, vc.vendor_id, vc.verification_source_id, vc.verification_status,
               v.submitted_by
        FROM vendor_certifications vc
        JOIN vendors v ON v.id=vc.vendor_id
        WHERE vc.id=:id AND v.organization_id=:org
          AND v.review_status='verified' AND v.verification_status='verified'
        FOR UPDATE OF vc
    """), {"id": certification_id, "org": organization_id}).mappings().first()
    if not certification or certification["verification_status"] != "unverified":
        raise HTTPException(status_code=404, detail="Pending certification review was not found in this organization.")
    if str(certification["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="A vendor submitter cannot review their own certification claim.")
    source = db.execute(text("""
        SELECT source_url FROM source_records WHERE id=:id
    """), {"id": certification["verification_source_id"]}).scalar_one_or_none()
    if payload.decision == "verified" and not source:
        raise HTTPException(status_code=409, detail="Certification verification requires a source URL.")
    db.execute(text("""
        INSERT INTO vendor_certification_decisions
            (certification_id, organization_id, reviewer_id, decision, rationale)
        VALUES (:certification, :org, :reviewer, :decision, :rationale)
    """), {"certification": certification_id, "org": organization_id,
           "reviewer": current_user["id"], "decision": payload.decision,
           "rationale": payload.rationale.strip()})
    new_status = "verified" if payload.decision == "verified" else (
        "rejected" if payload.decision == "rejected" else "unverified"
    )
    db.execute(text("""
        UPDATE vendor_certifications
        SET verification_status=:status,
            verified_by=:reviewer,
            verified_at=CASE WHEN :status='verified' THEN now() ELSE NULL END
        WHERE id=:id
    """), {"status": new_status, "reviewer": current_user["id"], "id": certification_id})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'vendor_certification_review_decided', 'vendor_certification', :id,
                jsonb_build_object('decision', :decision, 'vendor_id', :vendor))
    """), {"actor": current_user["id"], "org": organization_id, "id": certification_id,
           "decision": payload.decision, "vendor": str(certification["vendor_id"])})
    db.commit()
    return {"certification_id": str(certification_id), "verification_status": new_status,
            "decision": payload.decision}


@router.post("/services/{service_id}/evidence-links", status_code=201)
def submit_vendor_service_evidence_link(
    service_id: UUID,
    payload: VendorServiceEvidenceLinkSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot submit vendor capability evidence.")
    service = db.execute(text("""
        SELECT vs.id, vs.vendor_id FROM vendor_services vs
        JOIN vendors v ON v.id=vs.vendor_id
        WHERE vs.id=:id AND v.organization_id=:org
          AND v.review_status='verified' AND v.verification_status='verified'
          AND vs.review_status='verified'
    """), {"id": service_id, "org": organization_id}).mappings().first()
    if not service:
        raise HTTPException(status_code=404, detail="Verified service was not found in this organization.")
    if payload.relationship_type in {"peptide_supply", "peptide_manufacturing", "peptide_specific_testing", "formulation_development"} and not payload.peptide_id:
        raise HTTPException(status_code=422, detail="This relationship requires a peptide identity.")
    if payload.relationship_type in {"method_service", "peptide_specific_testing"} and not payload.method_id:
        raise HTTPException(status_code=422, detail="This relationship requires an analytical method identity.")
    if payload.peptide_id:
        peptide = db.execute(text("""
            SELECT id FROM peptides WHERE id=:id AND review_status='verified'
        """), {"id": payload.peptide_id}).scalar_one_or_none()
        if not peptide:
            raise HTTPException(status_code=422, detail="Linked peptide must already be curator-verified.")
    if payload.method_id:
        method = db.execute(text("""
            SELECT id FROM analytical_methods WHERE id=:id AND review_status='verified'
        """), {"id": payload.method_id}).scalar_one_or_none()
        if not method:
            raise HTTPException(status_code=422, detail="Linked analytical method must already be curator-verified.")
    source_id = _source_record(db, payload.source_name, payload.source_identifier, str(payload.source_url))
    link = db.execute(text("""
        INSERT INTO vendor_service_evidence_links
            (organization_id, service_id, peptide_id, method_id, relationship_type,
             evidence_scope, limitations, source_id, review_status, submitted_by)
        VALUES (:org, :service, :peptide, :method, :relationship,
                :scope, :limitations, :source, 'in_review', :submitter)
        RETURNING id, service_id, peptide_id, method_id, relationship_type, review_status
    """), {"org": organization_id, "service": service_id, "peptide": payload.peptide_id,
           "method": payload.method_id, "relationship": payload.relationship_type,
           "scope": payload.evidence_scope.strip(), "limitations": payload.limitations.strip(),
           "source": source_id, "submitter": current_user["id"]}).mappings().one()
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'vendor_service_evidence_link_submitted', 'vendor_service_evidence_link', :id,
                jsonb_build_object('service_id', :service, 'peptide_id', :peptide, 'method_id', :method,
                                   'source_record_id', :source))
    """), {"actor": current_user["id"], "org": organization_id, "id": link["id"],
           "service": str(service_id), "peptide": str(payload.peptide_id) if payload.peptide_id else None,
           "method": str(payload.method_id) if payload.method_id else None, "source": str(source_id)})
    db.commit()
    return dict(link)


@router.get("/service-evidence-links/reviews")
def vendor_service_evidence_link_review_queue(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    rows = db.execute(text("""
        SELECT l.id, l.service_id, l.relationship_type, l.evidence_scope, l.limitations,
               l.submitted_by, v.legal_name, vs.service_name,
               p.id AS peptide_id, p.preferred_name AS peptide_name,
               am.id AS method_id, am.method_name,
               sr.source_name, sr.source_identifier, sr.source_url
        FROM vendor_service_evidence_links l
        JOIN vendor_services vs ON vs.id=l.service_id
        JOIN vendors v ON v.id=vs.vendor_id
        LEFT JOIN peptides p ON p.id=l.peptide_id
        LEFT JOIN analytical_methods am ON am.id=l.method_id
        JOIN source_records sr ON sr.id=l.source_id
        WHERE l.organization_id=:org AND l.review_status='in_review'
          AND v.review_status='verified' AND v.verification_status='verified'
          AND vs.review_status='verified'
        ORDER BY l.created_at ASC LIMIT :limit
    """), {"org": organization_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows),
            "scope": "Only source-backed links to curator-verified peptide and method identities are eligible."}


@router.post("/service-evidence-links/{link_id}/decisions", status_code=201)
def decide_vendor_service_evidence_link(
    link_id: UUID,
    payload: VendorServiceEvidenceLinkDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    link = db.execute(text("""
        SELECT l.id, l.service_id, l.submitted_by, l.review_status
        FROM vendor_service_evidence_links l
        JOIN vendor_services vs ON vs.id=l.service_id
        JOIN vendors v ON v.id=vs.vendor_id
        WHERE l.id=:id AND l.organization_id=:org AND l.review_status='in_review'
          AND v.review_status='verified' AND v.verification_status='verified'
          AND vs.review_status='verified'
        FOR UPDATE OF l
    """), {"id": link_id, "org": organization_id}).mappings().first()
    if not link:
        raise HTTPException(status_code=404, detail="Pending service evidence link was not found in this organization.")
    if str(link["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="A submitter cannot review their own service evidence link.")
    db.execute(text("""
        INSERT INTO vendor_service_evidence_link_decisions
            (link_id, organization_id, reviewer_id, decision, rationale)
        VALUES (:link, :org, :reviewer, :decision, :rationale)
    """), {"link": link_id, "org": organization_id, "reviewer": current_user["id"],
           "decision": payload.decision, "rationale": payload.rationale.strip()})
    new_status = "verified" if payload.decision == "verified" else (
        "rejected" if payload.decision == "rejected" else "draft"
    )
    db.execute(text("""
        UPDATE vendor_service_evidence_links
        SET review_status=:status, reviewed_by=:reviewer, reviewed_at=now()
        WHERE id=:id
    """), {"status": new_status, "reviewer": current_user["id"], "id": link_id})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'vendor_service_evidence_link_decided', 'vendor_service_evidence_link', :id,
                jsonb_build_object('decision', :decision, 'service_id', :service))
    """), {"actor": current_user["id"], "org": organization_id, "id": link_id,
           "decision": payload.decision, "service": str(link["service_id"])})
    db.commit()
    return {"link_id": str(link_id), "review_status": new_status, "decision": payload.decision}


@router.get("/{vendor_id}/capabilities")
def verified_vendor_capabilities(
    vendor_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    vendor = db.execute(text("""
        SELECT id, legal_name FROM vendors
        WHERE id=:id AND review_status='verified' AND verification_status='verified'
    """), {"id": vendor_id}).mappings().first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Verified vendor was not found.")
    rows = db.execute(text("""
        SELECT vs.id AS service_id, vs.service_name, vs.capability_description,
               l.id AS link_id, l.relationship_type, l.evidence_scope, l.limitations,
               p.id AS peptide_id, p.preferred_name AS peptide_name,
               am.id AS method_id, am.method_name,
               sr.source_name, sr.source_identifier, sr.source_url
        FROM vendor_services vs
        JOIN vendor_service_evidence_links l ON l.service_id=vs.id AND l.review_status='verified'
        LEFT JOIN peptides p ON p.id=l.peptide_id AND p.review_status='verified'
        LEFT JOIN analytical_methods am ON am.id=l.method_id AND am.review_status='verified'
        JOIN source_records sr ON sr.id=l.source_id
        WHERE vs.vendor_id=:vendor AND vs.review_status='verified'
          AND (l.peptide_id IS NULL OR p.id IS NOT NULL)
          AND (l.method_id IS NULL OR am.id IS NOT NULL)
        ORDER BY vs.service_name, l.relationship_type
    """), {"vendor": vendor_id}).mappings().all()
    return {"vendor": dict(vendor), "items": [dict(row) for row in rows], "count": len(rows),
            "scope": "Source-backed, curator-verified service-to-peptide/method links only."}
