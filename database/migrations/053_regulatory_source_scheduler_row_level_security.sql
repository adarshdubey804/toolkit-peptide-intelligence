-- Scope regulatory RSS observations and poll-run history by organization.
-- The cross-tenant source registry remains a scheduler control plane and is intentionally not RLS-protected here.

ALTER TABLE regulatory_source_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_source_observations FORCE ROW LEVEL SECURITY;
CREATE POLICY regulatory_source_observations_select_scope ON regulatory_source_observations FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY regulatory_source_observations_insert_scope ON regulatory_source_observations FOR INSERT
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY regulatory_source_observations_update_scope ON regulatory_source_observations FOR UPDATE
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE regulatory_source_poll_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_source_poll_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY regulatory_source_poll_runs_select_scope ON regulatory_source_poll_runs FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY regulatory_source_poll_runs_insert_scope ON regulatory_source_poll_runs FOR INSERT
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY regulatory_source_poll_runs_update_scope ON regulatory_source_poll_runs FOR UPDATE
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

COMMENT ON POLICY regulatory_source_observations_select_scope ON regulatory_source_observations IS
    'Unreviewed RSS observations are private to the organization that registered the source.';
COMMENT ON POLICY regulatory_source_poll_runs_select_scope ON regulatory_source_poll_runs IS
    'Regulatory source polling history is private to the source-owning organization.';
