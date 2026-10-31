-- Persistent, organization-scoped peptide enrichment suggestions.
DO $$ BEGIN
    CREATE TYPE enrichment_candidate_status AS ENUM ('pending','accepted','rejected','duplicate','needs_review');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS enrichment_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    peptide_id UUID NOT NULL REFERENCES peptides(id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    source_identifier TEXT NOT NULL,
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    match_basis TEXT NOT NULL,
    raw_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    content_hash CHAR(64),
    candidate_status enrichment_candidate_status NOT NULL DEFAULT 'pending',
    submitted_by UUID NOT NULL REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    review_rationale TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, peptide_id, source_name, source_identifier)
);
CREATE INDEX IF NOT EXISTS idx_enrichment_candidates_queue
    ON enrichment_candidates(organization_id, candidate_status, created_at DESC);

CREATE TABLE IF NOT EXISTS enrichment_candidate_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES enrichment_candidates(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision enrichment_candidate_status NOT NULL CHECK (decision IN ('accepted','rejected','duplicate','needs_review')),
    rationale TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_enrichment_candidate_decisions_candidate
    ON enrichment_candidate_decisions(candidate_id, decided_at);

CREATE OR REPLACE FUNCTION prevent_enrichment_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'enrichment_candidate_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_enrichment_decisions_no_update ON enrichment_candidate_decisions;
CREATE TRIGGER trg_enrichment_decisions_no_update
    BEFORE UPDATE OR DELETE ON enrichment_candidate_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_enrichment_decision_mutation();
