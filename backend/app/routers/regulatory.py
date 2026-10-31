from datetime import date
import hashlib
import json
import xml.etree.ElementTree as ET
import httpx
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
APPROVED_REGULATORY_DOMAINS={"fda.gov","ema.europa.eu","gov.uk","cdsco.gov.in","who.int"}

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
from datetime import date
from typing import Annotated, Literal
from uuid import UUID
from urllib.parse import urlsplit
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user

class VersionObservation(BaseModel):
 version_or_revision: str | None = Field(default=None,max_length=100)
 publication_date: date | None = None
 effective_date: date | None = None
 source_url: HttpUrl
 content_hash: str | None = Field(default=None,pattern=r"^[a-fA-F0-9]{64}$")
 observation_note: str = Field(min_length=10,max_length=2000)
 change_type: Literal["new_version","source_content_changed","effective_date_changed","metadata_changed","possible_withdrawal"]
 change_summary: str = Field(min_length=20,max_length=4000)
 impact_assessment: str | None = Field(default=None,max_length=3000)

class ChangeDecision(BaseModel):
 decision: Literal["confirmed_change","not_a_change","published"]
 rationale: str = Field(min_length=20,max_length=4000)

@router.post("/{guidance_id}/observations",status_code=201)
def observe_guidance_version(guidance_id:UUID,payload:VersionObservation,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
 org,role=membership(user,db)
 if role not in SUBMIT: raise HTTPException(403,"Your role cannot submit monitoring observations.")
 record=db.execute(text("SELECT id,source_record_id FROM regulatory_guidance_records WHERE id=:id AND organization_id=:org AND review_status='verified'"),{"id":guidance_id,"org":org}).mappings().first()
 if not record: raise HTTPException(404,"Verified guidance record not found in your organization.")
 parsed=urlsplit(str(payload.source_url))
 if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password: raise HTTPException(422,"Observed source must use HTTPS without embedded credentials.")
 prior=db.execute(text("SELECT id,version_or_revision,content_hash,effective_date FROM regulatory_guidance_versions WHERE guidance_id=:id ORDER BY observed_at DESC LIMIT 1"),{"id":guidance_id}).mappings().first()
 normalized_hash=payload.content_hash.lower() if payload.content_hash else None
 duplicate=db.execute(text("""SELECT id FROM regulatory_guidance_versions
 WHERE guidance_id=:id AND source_url=:url
 AND version_or_revision IS NOT DISTINCT FROM :version
 AND content_hash IS NOT DISTINCT FROM :hash LIMIT 1"""),{"id":guidance_id,"url":str(payload.source_url),"version":payload.version_or_revision,"hash":normalized_hash}).scalar_one_or_none()
 if duplicate:
  raise HTTPException(409,"This exact version observation already exists.")
 version=db.execute(text("""INSERT INTO regulatory_guidance_versions(guidance_id,version_or_revision,publication_date,effective_date,source_url,content_hash,observed_by,observation_note)
 VALUES(:id,:version,:published,:effective,:url,:hash,:user,:note)
 RETURNING id,version_or_revision,observed_at,review_status"""),{"id":guidance_id,"version":payload.version_or_revision,"published":payload.publication_date,"effective":payload.effective_date,"url":str(payload.source_url),"hash":normalized_hash,"user":user["id"],"note":payload.observation_note}).mappings().one()
 event=db.execute(text("""INSERT INTO regulatory_change_events(guidance_id,previous_version_id,new_version_id,change_type,change_summary,impact_assessment,submitted_by)
 VALUES(:guidance,:previous,:new,:type,:summary,:impact,:user)
 RETURNING id,status,created_at"""),{"guidance":guidance_id,"previous":prior["id"] if prior else None,"new":version["id"],"type":payload.change_type,"summary":payload.change_summary,"impact":payload.impact_assessment,"user":user["id"]}).mappings().one()
 db.execute(text("""INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
 VALUES(:u,:o,'regulatory_change_observed','regulatory_change_event',:id,jsonb_build_object('guidance_id',:guidance,'version_id',:version))"""),{"u":user["id"],"o":org,"id":event["id"],"guidance":str(guidance_id),"version":str(version["id"])})
 db.commit()
 return {"version":dict(version),"change_event":dict(event),"notice":"Observation is unverified and requires curator review; no automatic regulatory interpretation was made."}

@router.get("/{guidance_id}/history")
def guidance_history(guidance_id:UUID,db:Session=Depends(get_db),limit:int=Query(50,ge=1,le=100)):
 rows=db.execute(text("""SELECT v.id,v.version_or_revision,v.publication_date,v.effective_date,v.source_url,v.content_hash,v.observed_at,v.review_status,
 e.id AS event_id,e.change_type,e.change_summary,e.impact_assessment,e.status AS event_status,e.created_at
 FROM regulatory_guidance_versions v LEFT JOIN regulatory_change_events e ON e.new_version_id=v.id
 JOIN regulatory_guidance_records g ON g.id=v.guidance_id
 WHERE v.guidance_id=:id AND g.review_status='verified' AND v.review_status='accepted'
 ORDER BY v.observed_at DESC LIMIT :lim"""),{"id":guidance_id,"lim":limit}).mappings().all()
 return {"items":[dict(x) for x in rows],"count":len(rows),"scope":"Only accepted version observations are shown. Change status reflects human review, not an automated determination."}

@router.get("/changes/reviews")
def change_review_queue(user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)],limit:int=Query(50,ge=1,le=100)):
 org,role=membership(user,db)
 if role not in REVIEW: raise HTTPException(403,"Curator or reviewer permission is required.")
 rows=db.execute(text("""SELECT e.id,e.guidance_id,e.change_type,e.change_summary,e.impact_assessment,e.status,e.created_at,
 g.authority,g.jurisdiction,g.document_title,v.version_or_revision,v.source_url,e.submitted_by
 FROM regulatory_change_events e JOIN regulatory_guidance_records g ON g.id=e.guidance_id
 JOIN regulatory_guidance_versions v ON v.id=e.new_version_id
 WHERE g.organization_id=:org AND e.status='needs_review' ORDER BY e.created_at LIMIT :lim"""),{"org":org,"lim":limit}).mappings().all()
 return {"items":[dict(x) for x in rows]}

@router.post("/changes/{event_id}/decisions")
def decide_change(event_id:UUID,payload:ChangeDecision,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
 org,role=membership(user,db)
 if role not in REVIEW: raise HTTPException(403,"Curator or reviewer permission is required.")
 event=db.execute(text("""SELECT e.id,e.submitted_by,e.new_version_id,e.guidance_id
 FROM regulatory_change_events e JOIN regulatory_guidance_records g ON g.id=e.guidance_id
 WHERE e.id=:id AND g.organization_id=:org AND e.status='needs_review'"""),{"id":event_id,"org":org}).mappings().first()
 if not event: raise HTTPException(404,"Open regulatory change event not found.")
 if str(event["submitted_by"])==user["id"]: raise HTTPException(403,"Submitters cannot review their own change observations.")
 db.execute(text("INSERT INTO regulatory_change_decisions(event_id,organization_id,reviewer_id,decision,rationale) VALUES(:id,:org,:user,:decision,:rationale)"),{"id":event_id,"org":org,"user":user["id"],"decision":payload.decision,"rationale":payload.rationale})
 db.execute(text("UPDATE regulatory_change_events SET status=:status,reviewed_by=:user,reviewed_at=now() WHERE id=:id"),{"status":payload.decision,"user":user["id"],"id":event_id})
 if payload.decision in {"confirmed_change","published"}:
  db.execute(text("UPDATE regulatory_guidance_versions SET review_status='accepted' WHERE id=:id"),{"id":event["new_version_id"]})
 elif payload.decision=="not_a_change":
  db.execute(text("UPDATE regulatory_guidance_versions SET review_status='rejected' WHERE id=:id"),{"id":event["new_version_id"]})
 db.execute(text("""INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
 VALUES(:u,:o,'regulatory_change_decided','regulatory_change_event',:id,jsonb_build_object('decision',:decision))"""),{"u":user["id"],"o":org,"id":event_id,"decision":payload.decision})
 db.commit()
 return {"event_id":str(event_id),"decision":payload.decision}


class RegulatorySourceInput(BaseModel):
 authority: str = Field(min_length=2,max_length=150)
 jurisdiction: str = Field(min_length=2,max_length=100)
 source_name: str = Field(min_length=2,max_length=150)
 source_type: Literal["rss","api","manual"] = "manual"
 feed_url: HttpUrl
 official_domain: str = Field(min_length=4,max_length=253,pattern=r"^[A-Za-z0-9.-]+$")
 description: str = Field(min_length=10,max_length=1500)
 polling_interval_hours: int = Field(default=24,ge=1,le=720)

@router.get("/sources")
def list_regulatory_sources(user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
 org,role=membership(user,db)
 if role not in REVIEW: raise HTTPException(403,"Curator or reviewer permission is required.")
 rows=db.execute(text("""SELECT id,authority,jurisdiction,source_name,source_type,feed_url,official_domain,description,polling_interval_hours,is_active,created_at
 FROM regulatory_source_registry WHERE organization_id=:org ORDER BY authority,source_name"""),{"org":org}).mappings().all()
 return {"items":[dict(x) for x in rows],"count":len(rows),"notice":"Registry entries are organization-managed source metadata; registration does not certify an authority or initiate automated polling."}

@router.post("/sources",status_code=201)
def register_regulatory_source(payload:RegulatorySourceInput,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
 org,role=membership(user,db)
 if role not in {"organization_admin","curator"}: raise HTTPException(403,"Organization admin or curator permission is required.")
 parsed=urlsplit(str(payload.feed_url))
 domain=payload.official_domain.lower().rstrip(".")
 host=(parsed.hostname or "").lower().rstrip(".")
 if domain not in APPROVED_REGULATORY_DOMAINS or parsed.scheme!="https" or not host or parsed.username or parsed.password or (host!=domain and not host.endswith("."+domain)):
  raise HTTPException(422,"Feed URL must use HTTPS and its host must equal or be a subdomain of the declared official domain.")
 row=db.execute(text("""INSERT INTO regulatory_source_registry(organization_id,authority,jurisdiction,source_name,source_type,feed_url,official_domain,description,polling_interval_hours,created_by)
 VALUES(:org,:authority,:jurisdiction,:name,:type,:url,:domain,:description,:interval,:user)
 ON CONFLICT(organization_id,feed_url) DO NOTHING
 RETURNING id,authority,jurisdiction,source_name,source_type,feed_url,official_domain,description,polling_interval_hours,is_active,created_at"""),{"org":org,"authority":payload.authority,"jurisdiction":payload.jurisdiction,"name":payload.source_name,"type":payload.source_type,"url":str(payload.feed_url),"domain":domain,"description":payload.description,"interval":payload.polling_interval_hours,"user":user["id"]}).mappings().first()
 if not row: raise HTTPException(409,"This source URL is already registered in the organization.")
 db.execute(text("""INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
 VALUES(:u,:o,'regulatory_source_registered','regulatory_source',:id,jsonb_build_object('feed_url',:url,'official_domain',:domain))"""),{"u":user["id"],"o":org,"id":row["id"],"url":str(payload.feed_url),"domain":domain})
 db.commit()
 return dict(row)


def _parse_rss_items(xml_bytes: bytes):
 if b"<!DOCTYPE" in xml_bytes.upper() or b"<!ENTITY" in xml_bytes.upper():
  raise ValueError("DTD and entity declarations are not accepted.")
 root=ET.fromstring(xml_bytes)
 items=[]
 for node in root.findall(".//item")[:100]:
  def value(tag):
   child=node.find(tag)
   return " ".join("".join(child.itertext()).split())[:4000] if child is not None else None
  title=value("title")
  link=value("link")
  guid=value("guid") or link
  if not title or not link or not guid: continue
  parsed=urlsplit(link)
  if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password: continue
  items.append({"guid":guid[:1000],"title":title[:1000],"url":link[:2000],"published":value("pubDate"),"summary":value("description")})
 return items


@router.post("/sources/{source_id}/poll")
async def poll_regulatory_source(source_id:UUID,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
 org,role=membership(user,db)
 if role not in REVIEW: raise HTTPException(403,"Curator or reviewer permission is required.")
 source=db.execute(text("SELECT * FROM regulatory_source_registry WHERE id=:id AND organization_id=:org AND is_active=true FOR UPDATE"),{"id":source_id,"org":org}).mappings().first()
 if not source: raise HTTPException(404,"Active registered source not found.")
 if source["source_type"]!="rss": raise HTTPException(422,"Only RSS sources are supported by this polling endpoint.")
 domain=str(source["official_domain"]).lower().rstrip(".")
 host=(urlsplit(source["feed_url"]).hostname or "").lower().rstrip(".")
 if domain not in APPROVED_REGULATORY_DOMAINS or (host!=domain and not host.endswith("."+domain)):
  raise HTTPException(422,"Source domain is not on the platform allowlist.")
 try:
  async with httpx.AsyncClient(timeout=httpx.Timeout(15.0,connect=4.0),follow_redirects=False,headers={"User-Agent":"ToolkitPeptideIntelligence/0.1","Accept":"application/rss+xml, application/xml, text/xml"}) as client:
   response=await client.get(source["feed_url"])
   response.raise_for_status()
   if len(response.content)>2_000_000: raise HTTPException(413,"Feed exceeds the 2 MB response limit.")
   content_type=response.headers.get("content-type","").lower()
   if not any(x in content_type for x in ("xml","rss","atom")): raise HTTPException(415,"Source did not return an XML feed.")
   items=_parse_rss_items(response.content)
 except HTTPException: raise
 except (httpx.HTTPError,ValueError,ET.ParseError) as exc:
  raise HTTPException(502,"Registered RSS source could not be safely retrieved or parsed.") from exc
 inserted=0
 for item in items:
  digest=hashlib.sha256(json.dumps(item,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
  result=db.execute(text("""INSERT INTO regulatory_source_observations(organization_id,source_id,external_identifier,item_title,item_url,published_at,summary,content_hash,raw_metadata)
  VALUES(:org,:source,:guid,:title,:url,:published,:summary,:hash,CAST(:metadata AS jsonb))
  ON CONFLICT(source_id,external_identifier) DO NOTHING RETURNING id"""),
  {"org":org,"source":source_id,"guid":item["guid"],"title":item["title"],"url":item["url"],"published":item["published"],"summary":item["summary"],"hash":digest,"metadata":json.dumps(item)}).first()
  if result: inserted+=1
 db.execute(text("""INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
 VALUES(:u,:o,'regulatory_source_polled','regulatory_source',:id,jsonb_build_object('items_seen',:seen,'items_added',:added))"""),
 {"u":user["id"],"o":org,"id":source_id,"seen":len(items),"added":inserted})
 db.commit()
 return {"source_id":str(source_id),"items_seen":len(items),"new_observations":inserted,"duplicates_skipped":len(items)-inserted,"curation_status":"not_reviewed","notice":"Feed observations require curator review; no regulatory interpretation or guidance promotion occurs automatically."}


@router.get("/sources/observations")
def list_regulatory_source_observations(user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)],limit:int=Query(50,ge=1,le=100)):
 org,role=membership(user,db)
 if role not in REVIEW: raise HTTPException(403,"Curator or reviewer permission is required.")
 rows=db.execute(text("""SELECT o.id,o.source_id,s.authority,s.jurisdiction,s.source_name,o.external_identifier,o.item_title,o.item_url,o.published_at,o.summary,o.content_hash,o.review_status,o.observed_at
 FROM regulatory_source_observations o JOIN regulatory_source_registry s ON s.id=o.source_id
 WHERE o.organization_id=:org AND o.review_status='pending_review' ORDER BY o.observed_at DESC LIMIT :limit"""),{"org":org,"limit":limit}).mappings().all()
 return {"items":[dict(row) for row in rows],"count":len(rows),"notice":"Unreviewed feed observations, not verified regulatory guidance."}


class RegulatoryFeedDecision(BaseModel):
 decision:Literal["accepted","rejected","duplicate"]
 rationale:str=Field(min_length=20,max_length=4000)


@router.post("/sources/observations/{observation_id}/decision")
def decide_regulatory_source_observation(observation_id:UUID,payload:RegulatoryFeedDecision,user:Annotated[dict,Depends(get_current_user)],db:Annotated[Session,Depends(get_db)]):
 org,role=membership(user,db)
 if role not in REVIEW: raise HTTPException(403,"Curator or reviewer permission is required.")
 row=db.execute(text("SELECT id FROM regulatory_source_observations WHERE id=:id AND organization_id=:org AND review_status='pending_review' FOR UPDATE"),{"id":observation_id,"org":org}).mappings().first()
 if not row: raise HTTPException(404,"Pending feed observation not found.")
 db.execute(text("UPDATE regulatory_source_observations SET review_status=:decision,reviewed_by=:user,review_rationale=:rationale,reviewed_at=now() WHERE id=:id"),{"decision":payload.decision,"user":user["id"],"rationale":payload.rationale.strip(),"id":observation_id})
 db.execute(text("""INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
 VALUES(:u,:o,'regulatory_feed_observation_decided','regulatory_source_observation',:id,jsonb_build_object('decision',:decision))"""),{"u":user["id"],"o":org,"id":observation_id,"decision":payload.decision})
 db.commit()
 return {"observation_id":str(observation_id),"decision":payload.decision}
