-- Process-development literature intelligence; descriptive records, not manufacturing instructions.
CREATE TABLE IF NOT EXISTS process_knowledge_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peptide_id UUID REFERENCES peptides(id) ON DELETE SET NULL,
    profile_title TEXT NOT NULL,
    process_platform TEXT NOT NULL,
    development_context TEXT NOT NULL,
    process_overview TEXT NOT NULL,
    critical_quality_attributes JSONB NOT NULL DEFAULT '[]'::jsonb,
    process_impurity_context JSONB NOT NULL DEFAULT '[]'::jsonb,
    scale_up_considerations TEXT,
    limitations TEXT NOT NULL,
    review_status review_status NOT NULL DEFAULT 'draft',
    submitted_by UUID REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS process_knowledge_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES process_knowledge_profiles(id) ON DELETE CASCADE,
    stage_name TEXT NOT NULL,
    stage_category TEXT NOT NULL,
    scientific_purpose TEXT NOT NULL,
    analytical_readouts JSONB NOT NULL DEFAULT '[]'::jsonb,
    process_risks TEXT,
    source_id UUID REFERENCES source_records(id),
    review_status review_status NOT NULL DEFAULT 'draft'
);
CREATE TABLE IF NOT EXISTS process_knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES process_knowledge_profiles(id) ON DELETE CASCADE,
    source_record_id UUID NOT NULL REFERENCES source_records(id),
    evidence_scope TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(profile_id, source_record_id)
);
CREATE TABLE IF NOT EXISTS process_knowledge_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES process_knowledge_profiles(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_process_knowledge_review
    ON process_knowledge_profiles(review_status, process_platform);
CREATE OR REPLACE FUNCTION prevent_process_knowledge_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'process_knowledge_decisions is append-only';
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_process_knowledge_decisions_no_update ON process_knowledge_decisions;
CREATE TRIGGER trg_process_knowledge_decisions_no_update
    BEFORE UPDATE OR DELETE ON process_knowledge_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_process_knowledge_decision_mutation();
