-- Keep organization-specific editorial decisions on the shared analytical test catalogue private.
-- A decision never changes the shared catalogue entry's global review status.

ALTER TABLE analytical_test_catalogue_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytical_test_catalogue_decisions FORCE ROW LEVEL SECURITY;

CREATE POLICY analytical_test_catalogue_decisions_select_scope
    ON analytical_test_catalogue_decisions FOR SELECT
    USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

CREATE POLICY analytical_test_catalogue_decisions_insert_scope
    ON analytical_test_catalogue_decisions FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM analytical_test_catalogue test
            WHERE test.id=analytical_test_catalogue_decisions.test_id
        )
    );

COMMENT ON POLICY analytical_test_catalogue_decisions_select_scope
    ON analytical_test_catalogue_decisions IS
    'Editorial decisions on the shared test catalogue are visible only to the organization that recorded them.';
COMMENT ON POLICY analytical_test_catalogue_decisions_insert_scope
    ON analytical_test_catalogue_decisions IS
    'Organizations may record decisions about shared catalogue entries only within their transaction-scoped tenant context.';
