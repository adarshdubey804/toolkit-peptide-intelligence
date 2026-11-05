-- Prevent organization-scoped users from creating or appending to shared/global
-- discovery records. Global records are visible for reference but only trusted
-- ingestion/migration roles may create shared data outside this workspace.
DROP POLICY IF EXISTS peptide_discovery_candidates_insert_scope
    ON peptide_discovery_candidates;

CREATE POLICY peptide_discovery_candidates_insert_scope
    ON peptide_discovery_candidates
    FOR INSERT
    WITH CHECK (
        owner_organization_id IS NOT NULL
        AND owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

DROP POLICY IF EXISTS peptide_discovery_observations_insert_scope
    ON peptide_discovery_observations;

CREATE POLICY peptide_discovery_observations_insert_scope
    ON peptide_discovery_observations
    FOR INSERT
    WITH CHECK (
        owner_organization_id IS NOT NULL
        AND owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

COMMENT ON POLICY peptide_discovery_candidates_insert_scope
    ON peptide_discovery_candidates IS
    'Organization workspace users may create only private candidates owned by their current organization; shared/global records require trusted ingestion.';

COMMENT ON POLICY peptide_discovery_observations_insert_scope
    ON peptide_discovery_observations IS
    'Organization workspace users may append observations only to their own private discovery records; shared/global observations require trusted ingestion.';
