-- Protect organization-owned regulatory source registrations while allowing a
-- separately provisioned scheduler role to reserve due feeds across organizations.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='toolkit_regulatory_scheduler') THEN
        CREATE ROLE toolkit_regulatory_scheduler NOLOGIN NOBYPASSRLS;
    END IF;
END
$$;

ALTER TABLE regulatory_source_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_source_registry FORCE ROW LEVEL SECURITY;

CREATE POLICY regulatory_source_registry_select_scope
ON regulatory_source_registry FOR SELECT
USING (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    OR current_user = 'toolkit_regulatory_scheduler'
);
CREATE POLICY regulatory_source_registry_insert_scope
ON regulatory_source_registry FOR INSERT
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY regulatory_source_registry_update_scope
ON regulatory_source_registry FOR UPDATE
USING (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    OR current_user = 'toolkit_regulatory_scheduler'
)
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    OR current_user = 'toolkit_regulatory_scheduler'
);

-- Scheduler can inspect due feeds but can only change polling metadata.
GRANT USAGE ON SCHEMA public TO toolkit_regulatory_scheduler;
GRANT SELECT ON regulatory_source_registry TO toolkit_regulatory_scheduler;
GRANT UPDATE (last_polled_at, next_poll_at, last_poll_status)
ON regulatory_source_registry TO toolkit_regulatory_scheduler;
GRANT SELECT, INSERT, UPDATE ON regulatory_source_poll_runs TO toolkit_regulatory_scheduler;
GRANT INSERT ON regulatory_source_observations TO toolkit_regulatory_scheduler;
GRANT INSERT ON audit_events TO toolkit_regulatory_scheduler;

-- Audit trigger executes with invoker rights; chain heads remain tenant-scoped.
ALTER TABLE audit_chain_heads ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_chain_heads FORCE ROW LEVEL SECURITY;
CREATE POLICY audit_chain_heads_select_scope ON audit_chain_heads FOR SELECT
USING (chain_scope = NULLIF(current_setting('app.organization_id', true), ''));
CREATE POLICY audit_chain_heads_insert_scope ON audit_chain_heads FOR INSERT
WITH CHECK (chain_scope = NULLIF(current_setting('app.organization_id', true), ''));
CREATE POLICY audit_chain_heads_update_scope ON audit_chain_heads FOR UPDATE
USING (chain_scope = NULLIF(current_setting('app.organization_id', true), ''))
WITH CHECK (chain_scope = NULLIF(current_setting('app.organization_id', true), ''));
GRANT SELECT, INSERT, UPDATE ON audit_chain_heads TO toolkit_regulatory_scheduler;

COMMENT ON POLICY regulatory_source_registry_select_scope ON regulatory_source_registry IS
    'Registrations are organization-private; only the dedicated scheduler role may enumerate due feeds across organizations.';
COMMENT ON POLICY regulatory_source_registry_update_scope ON regulatory_source_registry IS
    'The scheduler role is column-limited to polling metadata; organization users may update only their own registrations.';
