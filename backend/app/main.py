from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .db import engine
from .routers.auth import router as auth_router
from .routers.agents import router as agents_router
from .routers.bioinformatics import router as bioinformatics_router
from .routers.analytical_methods import router as analytical_method_router
from .routers.curation import router as curation_router
from .routers.dossiers import router as dossier_router
from .routers.enrichment import router as enrichment_router
from .routers.evidence_intelligence import router as evidence_intelligence_router
from .routers.formulations import router as formulation_router
from .routers.interactions import router as interaction_router
from .routers.organizations import router as organization_router
from .routers.peptides import router as peptide_router
from .routers.process_knowledge import router as process_knowledge_router
from .routers.research import router as research_router
from .routers.regulatory import router as regulatory_router
from .routers.vendors import router as vendor_router

_APP_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = _APP_ROOT / "database" / "migrations"
if not MIGRATIONS_DIR.is_dir():
    # In the source checkout, migrations live at repository_root/database.
    MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "database" / "migrations"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development convenience only. Production migrations must run as a deployment job.
    if settings.app_env == "development":
        with engine.begin() as conn:
            for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
                conn.exec_driver_sql(migration.read_text(encoding="utf-8"))
    yield


app = FastAPI(
    title="Toolkit Peptide Intelligence API",
    version="0.3.0",
    description="Source-traceable peptide research information API; not a clinical decision system.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(bioinformatics_router)
app.include_router(analytical_method_router)
app.include_router(curation_router)
app.include_router(dossier_router)
app.include_router(enrichment_router)
app.include_router(evidence_intelligence_router)
app.include_router(formulation_router)
app.include_router(interaction_router)
app.include_router(organization_router)
app.include_router(peptide_router)
app.include_router(process_knowledge_router)
app.include_router(research_router)
app.include_router(regulatory_router)
app.include_router(vendor_router)


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok", "service": "toolkit-peptide-intelligence-api", "version": "0.3.0"}


@app.get("/ready", tags=["operations"])
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    return {"status": "ready", "database": "reachable"}
