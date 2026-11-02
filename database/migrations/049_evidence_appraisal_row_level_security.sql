-- Organization-private evidence appraisal and publication duplicate-review records.
ALTER TABLE evidence_appraisals ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_appraisals FORCE ROW LEVEL SECURITY;
CREATE POLICY evidence_appraisals_select_scope ON evidence_appraisals FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY evidence_appraisals_insert_scope ON evidence_appraisals FOR INSERT
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY evidence_appraisals_update_scope ON evidence_appraisals FOR UPDATE
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE evidence_appraisal_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_appraisal_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY evidence_appraisal_decisions_select_scope ON evidence_appraisal_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY evidence_appraisal_decisions_insert_scope ON evidence_appraisal_decisions FOR INSERT
WITH CHECK (
 organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
 AND EXISTS (SELECT 1 FROM evidence_appraisals appraisal
             WHERE appraisal.id=appraisal_id AND appraisal.organization_id=organization_id)
);

ALTER TABLE publication_duplicate_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE publication_duplicate_candidates FORCE ROW LEVEL SECURITY;
CREATE POLICY publication_duplicate_candidates_select_scope ON publication_duplicate_candidates FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY publication_duplicate_candidates_insert_scope ON publication_duplicate_candidates FOR INSERT
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY publication_duplicate_candidates_update_scope ON publication_duplicate_candidates FOR UPDATE
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE publication_duplicate_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE publication_duplicate_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY publication_duplicate_decisions_select_scope ON publication_duplicate_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY publication_duplicate_decisions_insert_scope ON publication_duplicate_decisions FOR INSERT
WITH CHECK (
 organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
 AND EXISTS (SELECT 1 FROM publication_duplicate_candidates candidate
             WHERE candidate.id=candidate_id AND candidate.organization_id=organization_id)
);
