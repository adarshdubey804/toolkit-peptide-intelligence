-- Scope regulatory guidance, version observations and change decisions by owning organization.
-- Verified guidance and accepted version history are shared read-only; submissions and decisions stay private.

ALTER TABLE regulatory_guidance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_guidance_records FORCE ROW LEVEL SECURITY;
CREATE POLICY regulatory_guidance_records_select_scope ON regulatory_guidance_records FOR SELECT
USING (
    review_status='verified'
    OR organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
);
CREATE POLICY regulatory_guidance_records_insert_scope ON regulatory_guidance_records FOR INSERT
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY regulatory_guidance_records_update_scope ON regulatory_guidance_records FOR UPDATE
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE regulatory_guidance_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_guidance_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY regulatory_guidance_decisions_select_scope ON regulatory_guidance_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY regulatory_guidance_decisions_insert_scope ON regulatory_guidance_decisions FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM regulatory_guidance_records guidance
        WHERE guidance.id=regulatory_guidance_decisions.guidance_id
          AND guidance.organization_id=regulatory_guidance_decisions.organization_id
    )
);

ALTER TABLE regulatory_guidance_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_guidance_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY regulatory_guidance_versions_select_scope ON regulatory_guidance_versions FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM regulatory_guidance_records guidance
        WHERE guidance.id=regulatory_guidance_versions.guidance_id
          AND (
              (guidance.review_status='verified' AND regulatory_guidance_versions.review_status='accepted')
              OR guidance.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
          )
    )
);
CREATE POLICY regulatory_guidance_versions_insert_scope ON regulatory_guidance_versions FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM regulatory_guidance_records guidance
        WHERE guidance.id=regulatory_guidance_versions.guidance_id
          AND guidance.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
);
CREATE POLICY regulatory_guidance_versions_update_scope ON regulatory_guidance_versions FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM regulatory_guidance_records guidance
        WHERE guidance.id=regulatory_guidance_versions.guidance_id
          AND guidance.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM regulatory_guidance_records guidance
        WHERE guidance.id=regulatory_guidance_versions.guidance_id
          AND guidance.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
);

ALTER TABLE regulatory_change_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_change_events FORCE ROW LEVEL SECURITY;
CREATE POLICY regulatory_change_events_select_scope ON regulatory_change_events FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM regulatory_guidance_records guidance
        JOIN regulatory_guidance_versions version ON version.id=regulatory_change_events.new_version_id
        WHERE guidance.id=regulatory_change_events.guidance_id
          AND (
              (guidance.review_status='verified' AND version.review_status='accepted')
              OR guidance.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
          )
    )
);
CREATE POLICY regulatory_change_events_insert_scope ON regulatory_change_events FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM regulatory_guidance_records guidance
        WHERE guidance.id=regulatory_change_events.guidance_id
          AND guidance.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
);
CREATE POLICY regulatory_change_events_update_scope ON regulatory_change_events FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM regulatory_guidance_records guidance
        WHERE guidance.id=regulatory_change_events.guidance_id
          AND guidance.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM regulatory_guidance_records guidance
        WHERE guidance.id=regulatory_change_events.guidance_id
          AND guidance.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
);

ALTER TABLE regulatory_change_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_change_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY regulatory_change_decisions_select_scope ON regulatory_change_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY regulatory_change_decisions_insert_scope ON regulatory_change_decisions FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM regulatory_change_events event
        JOIN regulatory_guidance_records guidance ON guidance.id=event.guidance_id
        WHERE event.id=regulatory_change_decisions.event_id
          AND guidance.organization_id=regulatory_change_decisions.organization_id
    )
);

COMMENT ON POLICY regulatory_guidance_records_select_scope ON regulatory_guidance_records IS
    'Verified regulatory guidance is shared for reference; unverified submissions remain organization-private.';
COMMENT ON POLICY regulatory_guidance_versions_select_scope ON regulatory_guidance_versions IS
    'Accepted versions of verified guidance are shared; pending/rejected observations remain organization-private.';
