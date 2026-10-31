import json
from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..db import get_db
from .auth import get_current_user

router=APIRouter(prefix="/api/v1/evidence-intelligence",tags=["evidence intelligence"])
ROLES=("organization_admin","curator","reviewer")
def reviewer(user:dict,db:Session):
    org=user.get("organization_id")
    role=db.execute(text("SELECT role FROM organization_memberships WHERE organization_id=:org AND user_id=:uid AND membership_status='active'"),{"org":org,"uid":user["id"]}).scalar_one_or_none() if org else None
    if role not in ROLES: raise HTTPException(403,"Curator or reviewer permission is required.")
    return UUID(org)

class Appraisal(BaseModel):
    claim_id:UUID
    study_design:Literal["systematic_review","meta_analysis","randomized_trial","observational_human","animal","in_vitro","computational","case_report","other","unknown"]
    evidence_level:Literal["clinical_human","preclinical_animal","in_vitro","computational","secondary_research","unknown"]
    population_or_model:str|None=Field(default=None,max_length=500)
    sample_size:int|None=Field(default=None,ge=0,le=100000000)
    endpoint:str|None=Field(default=None,max_length=1000)
    risk_of_bias:Literal["low_concern","some_concerns","high_concern","not_assessed"]="not_assessed"
    replication_status:Literal["independently_replicated","single_study","not_applicable","unknown"]="unknown"
    methodological_domains:dict=Field(default_factory=dict)
    limitations:str=Field(min_length=20,max_length=4000)
    appraisal_rationale:str=Field(min_length=20,max_length=4000)

class DuplicatePair(BaseModel):
    publication_a:UUID
    publication_b:UUID
    match_basis:Literal["doi","pmid","title_year_author","manual"]
    match_details:dict=Field(default_factory=dict)

class DuplicateDecision(BaseModel):
    status:Literal["confirmed_duplicate","not_duplicate"]
    rationale:str=Field(min_length=20,max_length=4000)

@router.get("/claims")
def claims(user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)],q:str|None=Query(default=None,min_length=1,max_length=120),limit:int=Query(default=50,ge=1,le=100)):
    org=reviewer(user,db)
    rows=db.execute(text("""
      SELECT ec.id,ec.peptide_id,p.preferred_name,ec.claim_text,ec.claim_domain,ec.evidence_type,
      ec.confidence_label,ec.limitations,ec.review_status,
      COALESCE(jsonb_agg(DISTINCT jsonb_build_object('source_name',sr.source_name,'identifier',sr.source_identifier,'url',sr.source_url,'relationship',cs.relationship)) FILTER(WHERE sr.id IS NOT NULL),'[]'::jsonb) sources,
      (SELECT count(*) FROM evidence_appraisals ea WHERE ea.claim_id=ec.id) appraisal_count
      FROM evidence_claims ec JOIN peptides p ON p.id=ec.peptide_id
      LEFT JOIN claim_sources cs ON cs.claim_id=ec.id LEFT JOIN source_records sr ON sr.id=cs.source_record_id
      WHERE EXISTS (SELECT 1 FROM curation_reviews cr JOIN organization_memberships om ON om.user_id=cr.submitted_by WHERE cr.entity_type='evidence_claim' AND cr.entity_id=ec.id AND om.organization_id=:org AND om.membership_status='active') AND (:q IS NULL OR ec.claim_text ILIKE :term OR p.preferred_name ILIKE :term)
      GROUP BY ec.id,p.preferred_name ORDER BY ec.created_at DESC LIMIT :limit
    """),{"org":org,"q":q,"term":f"%{q}%" if q else None,"limit":limit}).mappings().all()
    return {"items":[dict(x) for x in rows],"count":len(rows),"notice":"Evidence level and methodological risk are distinct; no composite evidence score is calculated."}

@router.post("/appraisals",status_code=201)
def appraise(payload:Appraisal,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
    org=reviewer(user,db)
    found=db.execute(text("SELECT ec.id FROM evidence_claims ec WHERE ec.id=:id AND EXISTS (SELECT 1 FROM curation_reviews cr JOIN organization_memberships om ON om.user_id=cr.submitted_by WHERE cr.entity_type='evidence_claim' AND cr.entity_id=ec.id AND om.organization_id=:org AND om.membership_status='active')"),{"id":payload.claim_id,"org":org}).scalar_one_or_none()
    if not found: raise HTTPException(404,"Claim not found in this organization.")
    row=db.execute(text("""
      INSERT INTO evidence_appraisals(organization_id,claim_id,study_design,evidence_level,population_or_model,sample_size,endpoint,risk_of_bias,replication_status,methodological_domains,limitations,appraisal_rationale,reviewer_id)
      VALUES(:org,:claim,:design,:level,:model,:n,:endpoint,:bias,:replication,CAST(:domains AS jsonb),:limitations,:rationale,:reviewer)
      RETURNING id,claim_id,study_design,evidence_level,risk_of_bias,replication_status,appraisal_status,created_at
    """),{"org":org,"claim":payload.claim_id,"design":payload.study_design,"level":payload.evidence_level,"model":payload.population_or_model,"n":payload.sample_size,"endpoint":payload.endpoint,"bias":payload.risk_of_bias,"replication":payload.replication_status,"domains":json.dumps(payload.methodological_domains),"limitations":payload.limitations.strip(),"rationale":payload.appraisal_rationale.strip(),"reviewer":user["id"]}).mappings().one()
    db.execute(text("INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata) VALUES(:actor,:org,'evidence_appraisal_created','evidence_appraisal',:id,jsonb_build_object('claim_id',:claim,'evidence_level',:level,'risk_of_bias',:bias))"),{"actor":user["id"],"org":org,"id":row["id"],"claim":payload.claim_id,"level":payload.evidence_level,"bias":payload.risk_of_bias})
    db.commit()
    return dict(row)

@router.get("/appraisals/{claim_id}")
def get_appraisals(claim_id:UUID,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
    org=reviewer(user,db)
    rows=db.execute(text("SELECT ea.* FROM evidence_appraisals ea JOIN evidence_claims ec ON ec.id=ea.claim_id JOIN peptides p ON p.id=ec.peptide_id WHERE ea.claim_id=:claim AND ea.organization_id=:org ORDER BY ea.created_at DESC"),{"claim":claim_id,"org":org}).mappings().all()
    return {"items":[dict(x) for x in rows],"count":len(rows)}

@router.post("/duplicate-candidates",status_code=201)
def add_duplicate(payload:DuplicatePair,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
    org=reviewer(user,db)
    if payload.publication_a==payload.publication_b: raise HTTPException(422,"Choose two different publication records.")
    count=db.execute(text("SELECT count(*) FROM publications WHERE id IN (:a,:b)"),{"a":payload.publication_a,"b":payload.publication_b}).scalar_one()
    if count!=2: raise HTTPException(404,"Both publication records must exist.")
    a,b=sorted([payload.publication_a,payload.publication_b],key=str)
    row=db.execute(text("INSERT INTO publication_duplicate_candidates(organization_id,publication_a,publication_b,match_basis,match_details) VALUES(:org,:a,:b,:basis,CAST(:details AS jsonb)) ON CONFLICT(organization_id,publication_a,publication_b) DO NOTHING RETURNING id,status,match_basis,created_at"),{"org":org,"a":a,"b":b,"basis":payload.match_basis,"details":json.dumps(payload.match_details)}).mappings().first()
    if not row: raise HTTPException(409,"This publication pair is already queued.")
    db.commit()
    return dict(row)

@router.get("/duplicate-candidates")
def duplicate_queue(user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)],status:Literal["needs_review","confirmed_duplicate","not_duplicate"]="needs_review",limit:int=Query(default=50,ge=1,le=100)):
    org=reviewer(user,db)
    rows=db.execute(text("""
      SELECT d.id,d.match_basis,d.match_details,d.status,d.created_at,
      a.title publication_a_title,a.doi publication_a_doi,a.pmid publication_a_pmid,a.url publication_a_url,
      b.title publication_b_title,b.doi publication_b_doi,b.pmid publication_b_pmid,b.url publication_b_url
      FROM publication_duplicate_candidates d JOIN publications a ON a.id=d.publication_a JOIN publications b ON b.id=d.publication_b
      WHERE d.organization_id=:org AND d.status=:status ORDER BY d.created_at DESC LIMIT :limit
    """),{"org":org,"status":status,"limit":limit}).mappings().all()
    return {"items":[dict(x) for x in rows],"count":len(rows)}

@router.post("/duplicate-candidates/{candidate_id}/decision")
def decide_duplicate(candidate_id:UUID,payload:DuplicateDecision,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
    org=reviewer(user,db)
    row=db.execute(text("UPDATE publication_duplicate_candidates SET status=:status,reviewed_by=:reviewer,reviewed_at=now() WHERE id=:id AND organization_id=:org AND status='needs_review' RETURNING id,status,reviewed_by,reviewed_at"),{"status":payload.status,"reviewer":user["id"],"id":candidate_id,"org":org}).mappings().first()
    if not row: raise HTTPException(404,"Open duplicate candidate not found.")
    db.execute(text("INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata) VALUES(:actor,:org,'publication_duplicate_reviewed','publication_duplicate_candidate',:id,jsonb_build_object('status',:status,'rationale',:rationale))"),{"actor":user["id"],"org":org,"id":candidate_id,"status":payload.status,"rationale":payload.rationale.strip()})
    db.commit()
    return dict(row)
