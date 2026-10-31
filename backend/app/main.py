from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import settings
from .db import engine
from .routers.peptides import router as peptide_router

MIGRATION = Path(__file__).resolve().parents[2] / "database" / "migrations" / "001_initial_schema.sql"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development convenience only. Production migrations must run as a deployment job.
    if settings.app_env == "development":
        with engine.begin() as conn:
            conn.exec_driver_sql(MIGRATION.read_text(encoding="utf-8"))
    yield


app = FastAPI(
    title="Toolkit Peptide Intelligence API",
    version="0.2.0",
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


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok", "service": "toolkit-peptide-intelligence-api", "version": "0.2.0"}


@app.get("/ready", tags=["operations"])
def readiness():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready", "database": "reachable"}
