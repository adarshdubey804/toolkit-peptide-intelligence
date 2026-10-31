-- Durable, organization-scoped audit trail for source ingestion runs.
CREATE TABLE IF NOT EXISTS enrichment_ingestion_runs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 peptide_id UUID NOT NULL REFERENCES peptides(id) ON DELETE CASCADE,
 started_by UUID NOT NULL REFERENCES user_profiles(id),
 search_query TEXT NOT NULL,
 requested_sources JSONB NOT NULL DEFAULT '[]'::jsonb,
 status TEXT NOT NULL CHECK(status IN ('running','completed','completed_with_errors','failed')),
 candidate_count INTEGER NOT NULL DEFAULT 0 CHECK(candidate_count >= 0),
 duplicate_count INTEGER NOT NULL DEFAULT 0 CHECK(duplicate_count >= 0),
 source_results JSONB NOT NULL DEFAULT '{}'::jsonb,
 errors JSONB NOT NULL DEFAULT '[]'::jsonb,
 started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 finished_at TIMESTAMPTZ,
 CHECK ((status='running' AND finished_at IS NULL) OR (status<>'running' AND finished_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_enrichment_ingestion_runs_org
 ON enrichment_ingestion_runs(organization_id,started_at DESC);
CREATE INDEX IF NOT EXISTS idx_enrichment_ingestion_runs_peptide
 ON enrichment_ingestion_runs(peptide_id,started_at DESC);
