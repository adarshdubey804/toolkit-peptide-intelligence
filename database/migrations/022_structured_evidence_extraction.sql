-- Persist structured, source-linked AI extraction records separately from verified claims.
CREATE TABLE IF NOT EXISTS evidence_extraction_runs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 requested_by UUID NOT NULL REFERENCES user_profiles(id),
 question TEXT NOT NULL,
 model_name TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('completed','no_sources','failed')),
 source_count INTEGER NOT NULL DEFAULT 0 CHECK(source_count>=0),
 record_count INTEGER NOT NULL DEFAULT 0 CHECK(record_count>=0),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_evidence_extraction_runs_org
 ON evidence_extraction_runs(organization_id,created_at DESC);
CREATE TABLE IF NOT EXISTS extracted_evidence_records (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 run_id UUID NOT NULL REFERENCES evidence_extraction_runs(id) ON DELETE CASCADE,
 source_citation_id TEXT NOT NULL,
 source_name TEXT NOT NULL,
 source_identifier TEXT NOT NULL,
 source_url TEXT NOT NULL,
 source_title TEXT NOT NULL,
 extraction JSONB NOT NULL,
 extraction_model TEXT NOT NULL,
 review_status TEXT NOT NULL DEFAULT 'not_reviewed'
   CHECK(review_status IN ('not_reviewed','accepted','rejected')),
 reviewed_by UUID REFERENCES user_profiles(id),
 reviewed_at TIMESTAMPTZ,
 review_rationale TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 CHECK(source_url LIKE 'https://%')
);
CREATE INDEX IF NOT EXISTS idx_extracted_evidence_org_review
 ON extracted_evidence_records(organization_id,review_status,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_extracted_evidence_run
 ON extracted_evidence_records(run_id);
