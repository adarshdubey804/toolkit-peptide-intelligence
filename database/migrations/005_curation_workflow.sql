-- Curator/reviewer workflow hardening.
CREATE INDEX IF NOT EXISTS idx_curation_reviews_org_status
    ON curation_reviews (review_status, priority, created_at DESC);

CREATE OR REPLACE FUNCTION prevent_curation_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'curation_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_curation_decisions_no_update ON curation_decisions;
CREATE TRIGGER trg_curation_decisions_no_update
    BEFORE UPDATE OR DELETE ON curation_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_curation_decision_mutation();

COMMENT ON FUNCTION prevent_curation_decision_mutation() IS
    'Enforces append-only scientific editorial decision history.';
