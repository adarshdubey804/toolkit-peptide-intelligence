CREATE TABLE IF NOT EXISTS extracted_evidence_field_decisions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 record_id UUID NOT NULL REFERENCES extracted_evidence_records(id) ON DELETE CASCADE,
 field_name TEXT NOT NULL CHECK(field_name IN (
  'study_design','evidence_level','peptide_identity','sequence','modifications',
  'target','mechanism','model_or_population','sample_size','methods','endpoints',
  'findings','limitations','conflicts','extraction_notes'
 )),
 decision TEXT NOT NULL CHECK(decision IN ('accepted','corrected','rejected')),
 reviewed_value JSONB,
 rationale TEXT NOT NULL CHECK(length(trim(rationale))>=20),
 reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 CHECK((decision='corrected' AND reviewed_value IS NOT NULL) OR
       (decision<>'corrected' AND reviewed_value IS NULL))
);
CREATE INDEX IF NOT EXISTS idx_extracted_field_decisions_history
 ON extracted_evidence_field_decisions(organization_id,record_id,field_name,created_at DESC);
CREATE OR REPLACE FUNCTION prevent_extracted_field_decision_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 RAISE EXCEPTION 'Scientific extraction field decisions are append-only';
END;
$$;
DROP TRIGGER IF EXISTS trg_extracted_field_decisions_append_only ON extracted_evidence_field_decisions;
CREATE TRIGGER trg_extracted_field_decisions_append_only
 BEFORE UPDATE OR DELETE ON extracted_evidence_field_decisions
 FOR EACH ROW EXECUTE FUNCTION prevent_extracted_field_decision_mutation();
