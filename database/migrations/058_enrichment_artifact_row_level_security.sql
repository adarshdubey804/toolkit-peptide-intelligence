-- Organization isolation for enrichment candidates, decisions and ingestion runs.

ALTER TABLE enrichment_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrichment_candidates FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS enrichment_candidates_select_scope ON enrichment_candidates;
CREATE POLICY enrichment_candidates_select_scope ON enrichment_candidates
    FOR SELECT USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
DROP POLICY IF EXISTS enrichment_candidates_insert_scope ON enrichment_candidates;
CREATE POLICY enrichment_candidates_insert_scope ON enrichment_candidates
    FOR INSERT WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
DROP POLICY IF EXISTS enrichment_candidates_update_scope ON enrichment_candidates;
CREATE POLICY enrichment_candidates_update_scope ON enrichment_candidates
    FOR UPDATE USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

ALTER TABLE enrichment_candidate_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrichment_candidate_decisions FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS enrichment_candidate_decisions_select_scope ON enrichment_candidate_decisions;
CREATE POLICY enrichment_candidate_decisions_select_scope ON enrichment_candidate_decisions
    FOR SELECT USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
DROP POLICY IF EXISTS enrichment_candidate_decisions_insert_scope ON enrichment_candidate_decisions;
CREATE POLICY enrichment_candidate_decisions_insert_scope ON enrichment_candidate_decisions
    FOR INSERT WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

ALTER TABLE enrichment_ingestion_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrichment_ingestion_runs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS enrichment_ingestion_runs_select_scope ON enrichment_ingestion_runs;
CREATE POLICY enrichment_ingestion_runs_select_scope ON enrichment_ingestion_runs
    FOR SELECT USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
DROP POLICY IF EXISTS enrichment_ingestion_runs_insert_scope ON enrichment_ingestion_runs;
CREATE POLICY enrichment_ingestion_runs_insert_scope ON enrichment_ingestion_runs
    FOR INSERT WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
DROP POLICY IF EXISTS enrichment_ingestion_runs_update_scope ON enrichment_ingestion_runs;
CREATE POLICY enrichment_ingestion_runs_update_scope ON enrichment_ingestion_runs
    FOR UPDATE USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

CREATE OR REPLACE FUNCTION enforce_enrichment_decision_organization()
RETURNS trigger AS $enrichment_decision_org_guard$
DECLARE
    candidate_organization UUID;
BEGIN
    SELECT organization_id INTO candidate_organization
    FROM enrichment_candidates
    WHERE id = NEW.candidate_id;

    IF candidate_organization IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Enrichment decision must belong to the organization that owns its candidate';
    END IF;
    RETURN NEW;
END;
$enrichment_decision_org_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS enrichment_candidate_decision_org_guard ON enrichment_candidate_decisions;
CREATE TRIGGER enrichment_candidate_decision_org_guard
    BEFORE INSERT OR UPDATE OF organization_id, candidate_id
    ON enrichment_candidate_decisions
    FOR EACH ROW EXECUTE FUNCTION enforce_enrichment_decision_organization();

COMMENT ON POLICY enrichment_candidates_select_scope ON enrichment_candidates IS
    'Enrichment candidates are private to their submitting organization.';
COMMENT ON POLICY enrichment_candidate_decisions_select_scope ON enrichment_candidate_decisions IS
    'Enrichment candidate review decisions are private to their organization.';
COMMENT ON POLICY enrichment_ingestion_runs_select_scope ON enrichment_ingestion_runs IS
    'Enrichment ingestion run history is private to its organization.';
