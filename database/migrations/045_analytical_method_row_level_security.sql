-- Extend the transaction-scoped RLS pilot to organization-owned analytical methods.
-- Shared method master records remain readable only when explicitly public and verified.

ALTER TABLE analytical_methods ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytical_methods FORCE ROW LEVEL SECURITY;
CREATE POLICY analytical_methods_select_scope
    ON analytical_methods FOR SELECT
    USING (
        (visibility_scope='public' AND review_status='verified')
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY analytical_methods_insert_scope
    ON analytical_methods FOR INSERT
    WITH CHECK (
        owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY analytical_methods_update_scope
    ON analytical_methods FOR UPDATE
    USING (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
    WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE analytical_method_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytical_method_sources FORCE ROW LEVEL SECURITY;
CREATE POLICY analytical_method_sources_select_scope
    ON analytical_method_sources FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM analytical_methods am
            WHERE am.id=method_id
              AND (
                  (am.visibility_scope='public' AND am.review_status='verified')
                  OR am.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
              )
        )
    );
CREATE POLICY analytical_method_sources_insert_scope
    ON analytical_method_sources FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM analytical_methods am
            WHERE am.id=method_id
              AND am.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );

ALTER TABLE analytical_method_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytical_method_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY analytical_method_decisions_select_scope
    ON analytical_method_decisions FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY analytical_method_decisions_insert_scope
    ON analytical_method_decisions FOR INSERT
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);


-- A decision must be filed under the organization that owns its method.
-- Shared master methods (owner_organization_id IS NULL) may receive
-- organization-scoped independent appraisals.
CREATE OR REPLACE FUNCTION enforce_analytical_method_decision_owner()
RETURNS trigger AS $
DECLARE
    method_owner UUID;
BEGIN
    SELECT owner_organization_id INTO method_owner
    FROM analytical_methods
    WHERE id = NEW.method_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Analytical method decision references an unknown method';
    END IF;
    IF method_owner IS NOT NULL AND method_owner IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Analytical method decision organization must match the method owner';
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS analytical_method_decision_owner_guard ON analytical_method_decisions;
CREATE TRIGGER analytical_method_decision_owner_guard
    BEFORE INSERT OR UPDATE OF method_id, organization_id ON analytical_method_decisions
    FOR EACH ROW EXECUTE FUNCTION enforce_analytical_method_decision_owner();

COMMENT ON POLICY analytical_methods_select_scope ON analytical_methods IS
    'Public reads require verified public scope; organization-owned methods are visible only in their owner transaction context.';
COMMENT ON POLICY analytical_method_sources_select_scope ON analytical_method_sources IS
    'Method source links inherit the visibility of their parent method.';
COMMENT ON POLICY analytical_method_decisions_select_scope ON analytical_method_decisions IS
    'Method review decisions are visible only to the organization that owns the review workflow.';
