-- Organization-scoped review decisions for globally shared test-catalogue reference entries.
-- Decisions are append-only and do not globally promote a draft entry to verified.
CREATE TABLE IF NOT EXISTS analytical_test_catalogue_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID NOT NULL REFERENCES analytical_test_catalogue(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_analytical_test_catalogue_decisions_org_test
    ON analytical_test_catalogue_decisions(organization_id, test_id, decided_at DESC);

CREATE OR REPLACE FUNCTION prevent_analytical_test_catalogue_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'analytical_test_catalogue_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_analytical_test_catalogue_decisions_no_update
    ON analytical_test_catalogue_decisions;
CREATE TRIGGER trg_analytical_test_catalogue_decisions_no_update
    BEFORE UPDATE OR DELETE ON analytical_test_catalogue_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_analytical_test_catalogue_decision_mutation();
