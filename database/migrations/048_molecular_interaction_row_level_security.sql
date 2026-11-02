-- Protect organization-owned molecular interaction submissions and review decisions.
-- Only explicitly public, verified interaction assessments are anonymously readable.

ALTER TABLE molecular_interaction_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE molecular_interaction_assessments FORCE ROW LEVEL SECURITY;
CREATE POLICY molecular_interaction_assessments_select_scope
    ON molecular_interaction_assessments FOR SELECT
    USING (
        (visibility_scope='public' AND review_status='verified')
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY molecular_interaction_assessments_insert_scope
    ON molecular_interaction_assessments FOR INSERT
    WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY molecular_interaction_assessments_update_scope
    ON molecular_interaction_assessments FOR UPDATE
    USING (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
    WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE molecular_interaction_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE molecular_interaction_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY molecular_interaction_decisions_select_scope
    ON molecular_interaction_decisions FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY molecular_interaction_decisions_insert_scope
    ON molecular_interaction_decisions FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM molecular_interaction_assessments assessment
            WHERE assessment.id=assessment_id
              AND assessment.owner_organization_id=organization_id
        )
    );

COMMENT ON POLICY molecular_interaction_assessments_select_scope ON molecular_interaction_assessments IS
    'Interaction assessments are public only when explicitly public and verified; unresolved and organization-owned records stay private.';
COMMENT ON POLICY molecular_interaction_decisions_select_scope ON molecular_interaction_decisions IS
    'Interaction review decisions are organization-scoped and never public.';
