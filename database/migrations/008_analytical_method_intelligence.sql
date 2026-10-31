-- Analytical method intelligence: source provenance, structured applicability and review.
ALTER TABLE analytical_methods
    ADD COLUMN IF NOT EXISTS sample_requirements TEXT,
    ADD COLUMN IF NOT EXISTS instrument_platform TEXT,
    ADD COLUMN IF NOT EXISTS method_scope TEXT,
    ADD COLUMN IF NOT EXISTS method_version TEXT,
    ADD COLUMN IF NOT EXISTS submitted_by UUID REFERENCES user_profiles(id),
    ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES user_profiles(id),
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS analytical_method_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_id UUID NOT NULL REFERENCES analytical_methods(id) ON DELETE CASCADE,
    source_record_id UUID NOT NULL REFERENCES source_records(id),
    relationship TEXT NOT NULL DEFAULT 'method_reference',
    evidence_scope TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(method_id, source_record_id, relationship)
);
CREATE TABLE IF NOT EXISTS analytical_method_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_id UUID NOT NULL REFERENCES analytical_methods(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_analytical_methods_review_queue
    ON analytical_methods(review_status, method_category);
CREATE OR REPLACE FUNCTION prevent_analytical_method_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'analytical_method_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_analytical_method_decisions_no_update ON analytical_method_decisions;
CREATE TRIGGER trg_analytical_method_decisions_no_update
    BEFORE UPDATE OR DELETE ON analytical_method_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_analytical_method_decision_mutation();
