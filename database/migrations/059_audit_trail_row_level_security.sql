-- Tenant isolation for organization audit events and their tamper-evident chain heads.
-- Global ('global') chain entries are reserved for a privileged system database role.

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS audit_events_select_scope ON audit_events;
CREATE POLICY audit_events_select_scope ON audit_events
    FOR SELECT USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
DROP POLICY IF EXISTS audit_events_insert_scope ON audit_events;
CREATE POLICY audit_events_insert_scope ON audit_events
    FOR INSERT WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

ALTER TABLE audit_chain_heads ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_chain_heads FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS audit_chain_heads_select_scope ON audit_chain_heads;
CREATE POLICY audit_chain_heads_select_scope ON audit_chain_heads
    FOR SELECT USING (
        chain_scope = NULLIF(current_setting('app.organization_id', true), '')
    );
DROP POLICY IF EXISTS audit_chain_heads_insert_scope ON audit_chain_heads;
CREATE POLICY audit_chain_heads_insert_scope ON audit_chain_heads
    FOR INSERT WITH CHECK (
        chain_scope = NULLIF(current_setting('app.organization_id', true), '')
    );
DROP POLICY IF EXISTS audit_chain_heads_update_scope ON audit_chain_heads;
CREATE POLICY audit_chain_heads_update_scope ON audit_chain_heads
    FOR UPDATE USING (
        chain_scope = NULLIF(current_setting('app.organization_id', true), '')
    )
    WITH CHECK (
        chain_scope = NULLIF(current_setting('app.organization_id', true), '')
    );

COMMENT ON POLICY audit_events_select_scope ON audit_events IS
    'An organization can read only its own append-only audit events; global system events are not tenant-readable.';
COMMENT ON POLICY audit_chain_heads_select_scope ON audit_chain_heads IS
    'An organization can inspect only its own tamper-evident audit-chain head.';
