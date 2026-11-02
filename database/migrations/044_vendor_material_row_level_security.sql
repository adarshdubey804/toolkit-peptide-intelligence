-- Limited row-level-security pilot for vendor material and batch traceability.
-- Application requests bind app.organization_id transaction-locally after JWT membership validation.
-- Public reads are restricted to explicitly public, verified offerings; physical lots and reports remain private.

ALTER TABLE vendor_material_offerings ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_material_offerings FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_material_offerings_select_scope
    ON vendor_material_offerings FOR SELECT
    USING (
        (visibility_scope='public' AND review_status='verified')
        OR organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY vendor_material_offerings_insert_scope
    ON vendor_material_offerings FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY vendor_material_offerings_update_scope
    ON vendor_material_offerings FOR UPDATE
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE vendor_material_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_material_batches FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_material_batches_select_scope
    ON vendor_material_batches FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY vendor_material_batches_insert_scope
    ON vendor_material_batches FOR INSERT
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY vendor_material_batches_update_scope
    ON vendor_material_batches FOR UPDATE
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE batch_analytical_test_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_analytical_test_results FORCE ROW LEVEL SECURITY;
CREATE POLICY batch_analytical_test_results_select_scope
    ON batch_analytical_test_results FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY batch_analytical_test_results_insert_scope
    ON batch_analytical_test_results FOR INSERT
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY batch_analytical_test_results_update_scope
    ON batch_analytical_test_results FOR UPDATE
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE batch_analytical_test_result_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_analytical_test_result_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY batch_analytical_test_result_decisions_select_scope
    ON batch_analytical_test_result_decisions FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY batch_analytical_test_result_decisions_insert_scope
    ON batch_analytical_test_result_decisions FOR INSERT
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

COMMENT ON POLICY vendor_material_offerings_select_scope ON vendor_material_offerings IS
    'Public reads are limited to verified public offerings; authenticated organization reads use transaction-local app.organization_id.';
COMMENT ON POLICY vendor_material_batches_select_scope ON vendor_material_batches IS
    'Physical lots are visible only to the organization bound to the current database transaction.';
COMMENT ON POLICY batch_analytical_test_results_select_scope ON batch_analytical_test_results IS
    'Batch analytical reports are visible only to the organization bound to the current database transaction.';
