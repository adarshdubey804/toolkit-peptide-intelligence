-- Protect peptide-specific method and test applicability assessments.
-- Organization review never silently promotes an assessment into the shared catalogue.

ALTER TABLE peptide_method_applicability ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_method_applicability FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_method_applicability_select_scope
    ON peptide_method_applicability FOR SELECT
    USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        OR (
            visibility_scope='public'
            AND review_status='verified'
            AND EXISTS (
                SELECT 1 FROM peptides peptide
                WHERE peptide.id=peptide_method_applicability.peptide_id
                  AND peptide.review_status='verified'
            )
            AND EXISTS (
                SELECT 1 FROM analytical_methods method
                WHERE method.id=peptide_method_applicability.method_id
                  AND method.review_status='verified'
                  AND method.visibility_scope='public'
            )
            AND (
                peptide_method_applicability.chemical_form_id IS NULL
                OR EXISTS (
                    SELECT 1 FROM peptide_chemical_forms form
                    WHERE form.id=peptide_method_applicability.chemical_form_id
                      AND form.peptide_id=peptide_method_applicability.peptide_id
                      AND form.review_status='verified'
                )
            )
        )
    );
CREATE POLICY peptide_method_applicability_insert_scope
    ON peptide_method_applicability FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM peptides peptide
            WHERE peptide.id=peptide_method_applicability.peptide_id
              AND peptide.review_status='verified'
        )
        AND EXISTS (
            SELECT 1 FROM analytical_methods method
            WHERE method.id=peptide_method_applicability.method_id
              AND method.review_status='verified'
              AND (
                  method.visibility_scope='public'
                  OR method.owner_organization_id=peptide_method_applicability.organization_id
              )
        )
        AND (
            peptide_method_applicability.chemical_form_id IS NULL
            OR EXISTS (
                SELECT 1 FROM peptide_chemical_forms form
                WHERE form.id=peptide_method_applicability.chemical_form_id
                  AND form.peptide_id=peptide_method_applicability.peptide_id
                  AND form.review_status='verified'
            )
        )
    );
CREATE POLICY peptide_method_applicability_update_scope
    ON peptide_method_applicability FOR UPDATE
    USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM peptides peptide
            WHERE peptide.id=peptide_method_applicability.peptide_id
              AND peptide.review_status='verified'
        )
        AND EXISTS (
            SELECT 1 FROM analytical_methods method
            WHERE method.id=peptide_method_applicability.method_id
              AND method.review_status='verified'
              AND (
                  method.visibility_scope='public'
                  OR method.owner_organization_id=peptide_method_applicability.organization_id
              )
        )
    );

ALTER TABLE peptide_method_applicability_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_method_applicability_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_method_applicability_decisions_select_scope
    ON peptide_method_applicability_decisions FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY peptide_method_applicability_decisions_insert_scope
    ON peptide_method_applicability_decisions FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM peptide_method_applicability applicability
            WHERE applicability.id=peptide_method_applicability_decisions.applicability_id
              AND applicability.organization_id=peptide_method_applicability_decisions.organization_id
        )
    );

ALTER TABLE peptide_test_applicability ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_test_applicability FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_test_applicability_select_scope
    ON peptide_test_applicability FOR SELECT
    USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        OR (
            visibility_scope='public'
            AND review_status='verified'
            AND EXISTS (
                SELECT 1 FROM peptides peptide
                WHERE peptide.id=peptide_test_applicability.peptide_id
                  AND peptide.review_status='verified'
            )
            AND EXISTS (
                SELECT 1 FROM analytical_test_catalogue test
                WHERE test.id=peptide_test_applicability.test_id
                  AND test.review_status='verified'
            )
            AND (
                peptide_test_applicability.chemical_form_id IS NULL
                OR EXISTS (
                    SELECT 1 FROM peptide_chemical_forms form
                    WHERE form.id=peptide_test_applicability.chemical_form_id
                      AND form.peptide_id=peptide_test_applicability.peptide_id
                      AND form.review_status='verified'
                )
            )
        )
    );
CREATE POLICY peptide_test_applicability_insert_scope
    ON peptide_test_applicability FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM peptides peptide
            WHERE peptide.id=peptide_test_applicability.peptide_id
              AND peptide.review_status='verified'
        )
        AND EXISTS (
            SELECT 1 FROM analytical_test_catalogue test
            WHERE test.id=peptide_test_applicability.test_id
        )
        AND (
            peptide_test_applicability.chemical_form_id IS NULL
            OR EXISTS (
                SELECT 1 FROM peptide_chemical_forms form
                WHERE form.id=peptide_test_applicability.chemical_form_id
                  AND form.peptide_id=peptide_test_applicability.peptide_id
                  AND form.review_status='verified'
            )
        )
    );
CREATE POLICY peptide_test_applicability_update_scope
    ON peptide_test_applicability FOR UPDATE
    USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM peptides peptide
            WHERE peptide.id=peptide_test_applicability.peptide_id
              AND peptide.review_status='verified'
        )
        AND EXISTS (
            SELECT 1 FROM analytical_test_catalogue test
            WHERE test.id=peptide_test_applicability.test_id
        )
    );

ALTER TABLE peptide_test_applicability_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_test_applicability_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_test_applicability_decisions_select_scope
    ON peptide_test_applicability_decisions FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY peptide_test_applicability_decisions_insert_scope
    ON peptide_test_applicability_decisions FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM peptide_test_applicability applicability
            WHERE applicability.id=peptide_test_applicability_decisions.applicability_id
              AND applicability.organization_id=peptide_test_applicability_decisions.organization_id
        )
    );

CREATE OR REPLACE FUNCTION enforce_peptide_method_applicability_scope()
RETURNS trigger AS $method_applicability_guard$
DECLARE
    form_peptide UUID;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM peptides
        WHERE id=NEW.peptide_id AND review_status='verified'
    ) THEN
        RAISE EXCEPTION 'Method applicability requires a verified peptide identity';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM analytical_methods method
        WHERE method.id=NEW.method_id
          AND method.review_status='verified'
          AND (
              method.visibility_scope='public'
              OR method.owner_organization_id=NEW.organization_id
          )
    ) THEN
        RAISE EXCEPTION 'Method applicability requires a verified public or organization-owned method';
    END IF;
    IF NEW.chemical_form_id IS NOT NULL THEN
        SELECT peptide_id INTO form_peptide
        FROM peptide_chemical_forms
        WHERE id=NEW.chemical_form_id AND review_status='verified';
        IF form_peptide IS NULL OR form_peptide IS DISTINCT FROM NEW.peptide_id THEN
            RAISE EXCEPTION 'Method applicability chemical form must be verified and belong to its peptide';
        END IF;
    END IF;
    RETURN NEW;
END;
$method_applicability_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_method_applicability_scope_guard ON peptide_method_applicability;
CREATE TRIGGER peptide_method_applicability_scope_guard
    BEFORE INSERT OR UPDATE OF organization_id, peptide_id, method_id, chemical_form_id
    ON peptide_method_applicability
    FOR EACH ROW EXECUTE FUNCTION enforce_peptide_method_applicability_scope();

CREATE OR REPLACE FUNCTION enforce_peptide_test_applicability_scope()
RETURNS trigger AS $test_applicability_guard$
DECLARE
    form_peptide UUID;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM peptides
        WHERE id=NEW.peptide_id AND review_status='verified'
    ) THEN
        RAISE EXCEPTION 'Test applicability requires a verified peptide identity';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM analytical_test_catalogue
        WHERE id=NEW.test_id
    ) THEN
        RAISE EXCEPTION 'Test applicability references an unknown catalogue test';
    END IF;
    IF NEW.chemical_form_id IS NOT NULL THEN
        SELECT peptide_id INTO form_peptide
        FROM peptide_chemical_forms
        WHERE id=NEW.chemical_form_id AND review_status='verified';
        IF form_peptide IS NULL OR form_peptide IS DISTINCT FROM NEW.peptide_id THEN
            RAISE EXCEPTION 'Test applicability chemical form must be verified and belong to its peptide';
        END IF;
    END IF;
    RETURN NEW;
END;
$test_applicability_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_test_applicability_scope_guard ON peptide_test_applicability;
CREATE TRIGGER peptide_test_applicability_scope_guard
    BEFORE INSERT OR UPDATE OF organization_id, peptide_id, test_id, chemical_form_id
    ON peptide_test_applicability
    FOR EACH ROW EXECUTE FUNCTION enforce_peptide_test_applicability_scope();

CREATE OR REPLACE FUNCTION enforce_peptide_method_applicability_decision_owner()
RETURNS trigger AS $method_applicability_decision_guard$
DECLARE
    claim_organization UUID;
BEGIN
    SELECT organization_id INTO claim_organization
    FROM peptide_method_applicability WHERE id=NEW.applicability_id;
    IF claim_organization IS NULL OR claim_organization IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Method applicability decision organization must match its assessment owner';
    END IF;
    RETURN NEW;
END;
$method_applicability_decision_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_method_applicability_decision_owner_guard
    ON peptide_method_applicability_decisions;
CREATE TRIGGER peptide_method_applicability_decision_owner_guard
    BEFORE INSERT OR UPDATE OF applicability_id, organization_id
    ON peptide_method_applicability_decisions
    FOR EACH ROW EXECUTE FUNCTION enforce_peptide_method_applicability_decision_owner();

CREATE OR REPLACE FUNCTION enforce_peptide_test_applicability_decision_owner()
RETURNS trigger AS $test_applicability_decision_guard$
DECLARE
    claim_organization UUID;
BEGIN
    SELECT organization_id INTO claim_organization
    FROM peptide_test_applicability WHERE id=NEW.applicability_id;
    IF claim_organization IS NULL OR claim_organization IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Test applicability decision organization must match its assessment owner';
    END IF;
    RETURN NEW;
END;
$test_applicability_decision_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_test_applicability_decision_owner_guard
    ON peptide_test_applicability_decisions;
CREATE TRIGGER peptide_test_applicability_decision_owner_guard
    BEFORE INSERT OR UPDATE OF applicability_id, organization_id
    ON peptide_test_applicability_decisions
    FOR EACH ROW EXECUTE FUNCTION enforce_peptide_test_applicability_decision_owner();

COMMENT ON POLICY peptide_method_applicability_select_scope ON peptide_method_applicability IS
    'Method applicability is organization-private by default; public reads require explicit public scope and verified peptide, method and optional chemical form.';
COMMENT ON POLICY peptide_test_applicability_select_scope ON peptide_test_applicability IS
    'Test applicability is organization-private by default; public reads require explicit public scope and verified peptide, test and optional chemical form.';
