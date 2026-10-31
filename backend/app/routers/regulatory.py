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

router=APIRouter(prefix="/api/v1/regulatory",tags=["regulatory and quality intelligence"])
SUBMIT={"organization_admin","curator","researcher"}
REVIEW={"organization_admin","curator","reviewer"}

def membership(user,db):
 org=user.get("organization_id")
 if not org: raise HTTPException(403,"Active organization membership required.")
 role=db.execute(text("SELECT role FROM organization_memberships WHERE organization_id=:o AND user_id=:u AND membership_status='active'"),{"o":org,"u":user["id"]}).scalar_one_or_none()
 if not role: raise HTTPException(403,"Active organization membership required.")
 return org,role

def source_record(db,name,identifier,url):
 p=urlsplit(str(url))
 if p.scheme!="https" or not p.hostname or p.username or p.password: raise HTTPException(422,"Source must be HTTPS and contain no embedded credentials.")
 return db.execute(text("""INSERT INTO source_records(source_name,source_identifier,source_url,retrieved_at,raw_metadata)
 VALUES(:n,:i,:u,now(),'{}'::jsonb) ON CONFLICT(source_name,source_identifier)
 DO UPDATE SET source_url=EXCLUDED.source_url,last_seen_at=now() RETURNING id"""),{"n":name,"i":identifier,"u":str(url)}).scalar_one()

class GuidanceInput(BaseModel):
 authority:str=Field(min_length=2,max_length=150)
 jurisdiction:str=Field(min_length=2,max_length=100)
 document_type:Literal["guidance","regulation","standard","pharmacopoeia","inspection_reference","quality_framework","other"]
 document_title:str=Field(min_length=5,max_length=500)
 document_identifier:str|None=Field(default=None,max_length=200)
 version_or_revision:str|None=Field(default=None,max_length=100)
 publication_date:date|None=None
 effective_date:date|None=None
 scope_summary:str=Field(min_length=20,max_length=4000)
 limitations:str|None=Field(default=None,max_length=2000)
 source_name:str=Field(min_length=2,max_length=120)
 source_identifier:str=Field(min_length=1,max_length=200)
 source_url:HttpUrl

class Decision(BaseModel):
 decision:Literal["verified","rejected","needs_changes"]
 rationale:str=Field(min_length=20,max_length=4000)

@router.get("")
def list_guidance(jurisdiction:str|None=None,authority:str|None=None,document_type:str|None=None,limit:int=Query(50,ge=1,le=100),db:Session=Depends(get_db)):
 rows=db.execute(text("""SELECT g.id,g.authority,g.jurisdiction,g.document_type,g.document_title,g.document_identifier,
 g.version_or_revision,g.publication_date,g.effective_date,g.scope_summary,g.limitations,
 s.source_name,s.source_identifier,s.source_url
 FROM regulatory_guidance_records g JOIN source_records s ON s.id=g.source_record_id
 WHERE g.review_status='verified' AND (:j IS NULL OR lower(g.jurisdiction)=lower(:j))
 AND (:a IS NULL OR lower(g.authority)=lower(:a)) AND (:t IS NULL OR g.document_type=:t)
 ORDER BY g.jurisdiction,g.authority,g.document_title LIMIT :lim"""),{"j":jurisdiction,"a":authority,"t":document_type,"lim":limit}).mappings().all()
 return {"items":[dict(x) for x in rows],"count":len(rows),"scope":"Only curator-reviewed source records are shown. Inclusion does not establish legal applicability or organizational compliance."}

@router.post("",status_code=201)
def submit_guidance(payload:GuidanceInput,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
 org,role=membership(user,db)
 if role not in SUBMIT: raise HTTPException(403,"Your role cannot submit regulatory references.")
 sid=source_record(db,payload.source_name,payload.source_identifier,payload.source_url)
 row=db.execute(text("""INSERT INTO regulatory_guidance_records(organization_id,authority,jurisdiction,document_type,document_title,document_identifier,version_or_revision,publication_date,effective_date,scope_summary,limitations,source_record_id,submitted_by)
 VALUES(:org,:authority,:jurisdiction,:type,:title,:identifier,:version,:published,:effective,:scope,:limitations,:source,:user)
 RETURNING id,document_title,review_status,created_at"""),{"org":org,"authority":payload.authority,"jurisdiction":payload.jurisdiction,"type":payload.document_type,"title":payload.document_title,"identifier":payload.document_identifier,"version":payload.version_or_revision,"published":payload.publication_date,"effective":payload.effective_date,"scope":payload.scope_summary,"limitations":payload.limitations,"source":sid,"user":user["id"]}).mappings().one()
 db.execute(text("""INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
 VALUES(:u,:o,'regulatory_guidance_submitted','regulatory_guidance',:id,jsonb_build_object('source_record_id',:source))"""),{"u":user["id"],"o":org,"id":row["id"],"source":str(sid)})
 db.commit()
 return dict(row)

@router.get("/reviews")
def review_queue(user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)],limit:int=Query(50,ge=1,le=100)):
 org,role=membership(user,db)
 if role not in REVIEW: raise HTTPException(403,"Curator or reviewer permission is required.")
 rows=db.execute(text("""SELECT g.id,g.authority,g.jurisdiction,g.document_type,g.document_title,g.document_identifier,g.version_or_revision,g.scope_summary,g.submitted_by,s.source_url,s.source_name,s.source_identifier
 FROM regulatory_guidance_records g JOIN source_records s ON s.id=g.source_record_id
 WHERE g.organization_id=:org AND g.review_status='in_review' ORDER BY g.created_at LIMIT :lim"""),{"org":org,"lim":limit}).mappings().all()
 return {"items":[dict(x) for x in rows]}

@router.post("/{guidance_id}/decisions")
def decide(guidance_id:UUID,payload:Decision,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
 org,role=membership(user,db)
 if role not in REVIEW: raise HTTPException(403,"Curator or reviewer permission is required.")
 rec=db.execute(text("SELECT id,submitted_by FROM regulatory_guidance_records WHERE id=:id AND organization_id=:org AND review_status='in_review'"),{"id":guidance_id,"org":org}).mappings().first()
 if not rec: raise HTTPException(404,"Open guidance review not found.")
 if str(rec["submitted_by"])==user["id"]: raise HTTPException(403,"Submitters cannot review their own records.")
 db.execute(text("INSERT INTO regulatory_guidance_decisions(guidance_id,organization_id,reviewer_id,decision,rationale) VALUES(:id,:org,:user,:decision,:rationale)"),{"id":guidance_id,"org":org,"user":user["id"],"decision":payload.decision,"rationale":payload.rationale})
 db.execute(text("UPDATE regulatory_guidance_records SET review_status=:status,reviewed_by=:user,reviewed_at=now() WHERE id=:id"),{"status":"verified" if payload.decision=="verified" else "rejected" if payload.decision=="rejected" else "draft","user":user["id"],"id":guidance_id})
 db.execute(text("""INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
 VALUES(:u,:o,'regulatory_guidance_decided','regulatory_guidance',:id,jsonb_build_object('decision',:decision))"""),{"u":user["id"],"o":org,"id":guidance_id,"decision":payload.decision})
 db.commit()
 return {"guidance_id":str(guidance_id),"decision":payload.decision}
