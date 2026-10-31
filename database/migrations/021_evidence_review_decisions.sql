-- Append-only independent review decisions for appraisals and duplicate candidates.
CREATE TABLE IF NOT EXISTS evidence_appraisal_decisions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 appraisal_id UUID NOT NULL REFERENCES evidence_appraisals(id) ON DELETE CASCADE,
 decision TEXT NOT NULL CHECK(decision IN ('accepted','rejected','superseded')),
 rationale TEXT NOT NULL CHECK(length(trim(rationale))>=20),
 reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_appraisal_decisions_history
 ON evidence_appraisal_decisions(appraisal_id,created_at DESC);
CREATE TABLE IF NOT EXISTS publication_duplicate_decisions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 candidate_id UUID NOT NULL REFERENCES publication_duplicate_candidates(id) ON DELETE CASCADE,
 decision TEXT NOT NULL CHECK(decision IN ('confirmed_duplicate','not_duplicate')),
 rationale TEXT NOT NULL CHECK(length(trim(rationale))>=20),
 reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_duplicate_decisions_history
 ON publication_duplicate_decisions(candidate_id,created_at DESC);
CREATE OR REPLACE FUNCTION reject_evidence_decision_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 RAISE EXCEPTION 'Evidence review decisions are append-only';
END;
$$;
DROP TRIGGER IF EXISTS trg_appraisal_decisions_append_only ON evidence_appraisal_decisions;
CREATE TRIGGER trg_appraisal_decisions_append_only
 BEFORE UPDATE OR DELETE ON evidence_appraisal_decisions
 FOR EACH ROW EXECUTE FUNCTION reject_evidence_decision_mutation();
DROP TRIGGER IF EXISTS trg_duplicate_decisions_append_only ON publication_duplicate_decisions;
CREATE TRIGGER trg_duplicate_decisions_append_only
 BEFORE UPDATE OR DELETE ON publication_duplicate_decisions
 FOR EACH ROW EXECUTE FUNCTION reject_evidence_decision_mutation();
