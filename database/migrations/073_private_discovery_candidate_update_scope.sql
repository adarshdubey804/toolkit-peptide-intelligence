-- Restrict updates to private discovery candidates to their owning organization.
-- Shared/global candidates remain readable but cannot be mutated through the
-- organization-scoped discovery workspace.
DROP POLICY IF EXISTS peptide_discovery_candidates_update_scope
    ON peptide_discovery_candidates;

CREATE POLICY peptide_discovery_candidates_update_scope
    ON peptide_discovery_candidates
    FOR UPDATE
    USING (
        owner_organization_id IS NOT NULL
        AND owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
    WITH CHECK (
        owner_organization_id IS NOT NULL
        AND owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

COMMENT ON POLICY peptide_discovery_candidates_update_scope
    ON peptide_discovery_candidates IS
    'Only the owning organization may update its private discovery candidates; global candidates are read-only in this workspace.';
