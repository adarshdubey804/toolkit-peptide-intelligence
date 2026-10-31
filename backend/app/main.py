from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .db import engine, get_db

MIGRATION = Path(__file__).resolve().parents[1] / "database" / "migrations" / "001_initial_schema.sql"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development convenience only. Production migrations must run as a deployment job.
    if settings.app_env == "development":
        with engine.begin() as conn:
            conn.exec_driver_sql(MIGRATION.read_text())
    yield


app = FastAPI(title="Toolkit Peptide Intelligence API", version="0.1.0", description="Scientific information API; not a clinical decision system.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["GET", "OPTIONS"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "toolkit-peptide-intelligence-api", "version": "0.1.0"}


@app.get("/api/v1/peptides")
def list_peptides(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id,preferred_name,peptide_category,description,development_status,intended_use_class,review_status,created_at FROM peptides WHERE review_status='verified' ORDER BY preferred_name LIMIT 200")).mappings().all()
    return [dict(row) for row in rows]


@app.get("/api/v1/peptides/{peptide_id}")
def get_peptide(peptide_id: str, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id,preferred_name,peptide_category,description,development_status,intended_use_class,review_status,created_at FROM peptides WHERE id=:id AND review_status='verified'"), {"id": peptide_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Verified peptide record not found")
    return dict(row)
