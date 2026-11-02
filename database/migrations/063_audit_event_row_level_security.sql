-- Restrict tamper-evident audit history to its organization.
-- The scheduler writes actor-less events only after binding the source owner's organization.
-- User-authored events must match the authenticated transaction user context.

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;

CREATE POLICY audit_events_select_scope
    ON audit_events FOR SELECT
    USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

CREATE POLICY audit_events_insert_scope
    ON audit_events FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND actor_user_id IS NOT DISTINCT FROM
            NULLIF(current_setting('app.user_id', true), '')::uuid
    );

COMMENT ON POLICY audit_events_select_scope ON audit_events IS
    'Audit events are visible only inside their recorded organization; global events require a privileged audit operator.';
COMMENT ON POLICY audit_events_insert_scope ON audit_events IS
    'Audit events must match the active organization and authenticated actor; actor-less worker events require a worker transaction with no user context.';
