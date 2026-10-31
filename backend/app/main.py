from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .db import engine
from .routers.peptides import router as peptide_router
from .routers.research import router as research_router

MIGRATION = Path(__file__).resolve().parents[1] / "database" / "migrations" / "001_initial_schema.sql"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development convenience only. Production migrations must run as a deployment job.
    if settings.app_env == "development":
        with engine.begin() as conn:
            conn.exec_driver_sql(MIGRATION.read_text(encoding="utf-8"))
    yield


app = FastAPI(
    title="Toolkit Peptide Intelligence API",
    version="0.2.1",
    description="Source-traceable peptide research information API; not a clinical decision system.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(peptide_router)
app.include_router(research_router)


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok", "service": "toolkit-peptide-intelligence-api", "version": "0.2.1"}


@app.get("/ready", tags=["operations"])
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    return {"status": "ready", "database": "reachable"}
