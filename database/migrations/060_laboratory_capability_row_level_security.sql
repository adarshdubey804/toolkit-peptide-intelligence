-- Protect facility-specific laboratory capability claims and their review decisions.
-- A verified claim is not evidence of current capacity or analytical method validation.

ALTER TABLE laboratory_capability_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE laboratory_capability_claims FORCE ROW LEVEL SECURITY;
CREATE POLICY laboratory_capability_claims_select_scope
    ON laboratory_capability_claims FOR SELECT
    USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        OR (
            visibility_scope='public'
            AND review_status='verified'
            AND EXISTS (
                SELECT 1
                FROM vendor_services service
                JOIN vendors vendor ON vendor.id=service.vendor_id
                JOIN vendor_sites site ON site.id=service.site_id
                WHERE service.id=laboratory_capability_claims.service_id
                  AND service.review_status='verified'
                  AND vendor.review_status='verified'
                  AND vendor.verification_status='verified'
                  AND site.review_status='verified'
                  AND site.organization_id=vendor.organization_id
            )
            AND EXISTS (
                SELECT 1 FROM analytical_methods method
                WHERE method.id=laboratory_capability_claims.method_id
                  AND method.review_status='verified'
                  AND method.visibility_scope='public'
            )
            AND (
                laboratory_capability_claims.peptide_id IS NULL
                OR EXISTS (
                    SELECT 1 FROM peptides peptide
                    WHERE peptide.id=laboratory_capability_claims.peptide_id
                      AND peptide.review_status='verified'
                )
            )
            AND (
                laboratory_capability_claims.chemical_form_id IS NULL
                OR EXISTS (
                    SELECT 1 FROM peptide_chemical_forms form
                    WHERE form.id=laboratory_capability_claims.chemical_form_id
                      AND form.peptide_id=laboratory_capability_claims.peptide_id
                      AND form.review_status='verified'
                )
            )
        )
    );

CREATE POLICY laboratory_capability_claims_insert_scope
    ON laboratory_capability_claims FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1
            FROM vendor_services service
            JOIN vendors vendor ON vendor.id=service.vendor_id
            JOIN vendor_sites site ON site.id=service.site_id
            WHERE service.id=laboratory_capability_claims.service_id
              AND vendor.organization_id=laboratory_capability_claims.organization_id
              AND service.review_status='verified'
              AND vendor.review_status='verified'
              AND vendor.verification_status='verified'
              AND site.review_status='verified'
              AND site.organization_id=vendor.organization_id
        )
        AND EXISTS (
            SELECT 1 FROM analytical_methods method
            WHERE method.id=laboratory_capability_claims.method_id
              AND method.review_status='verified'
              AND (
                  (method.visibility_scope='public')
                  OR method.owner_organization_id=laboratory_capability_claims.organization_id
              )
        )
        AND (
            laboratory_capability_claims.peptide_id IS NULL
            OR EXISTS (
                SELECT 1 FROM peptides peptide
                WHERE peptide.id=laboratory_capability_claims.peptide_id
                  AND peptide.review_status='verified'
            )
        )
        AND (
            laboratory_capability_claims.chemical_form_id IS NULL
            OR EXISTS (
                SELECT 1 FROM peptide_chemical_forms form
                WHERE form.id=laboratory_capability_claims.chemical_form_id
                  AND form.peptide_id=laboratory_capability_claims.peptide_id
                  AND form.review_status='verified'
            )
        )
    );

CREATE POLICY laboratory_capability_claims_update_scope
    ON laboratory_capability_claims FOR UPDATE
    USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1
            FROM vendor_services service
            JOIN vendors vendor ON vendor.id=service.vendor_id
            JOIN vendor_sites site ON site.id=service.site_id
            WHERE service.id=laboratory_capability_claims.service_id
              AND vendor.organization_id=laboratory_capability_claims.organization_id
              AND service.review_status='verified'
              AND vendor.review_status='verified'
              AND vendor.verification_status='verified'
              AND site.review_status='verified'
              AND site.organization_id=vendor.organization_id
        )
    );

ALTER TABLE laboratory_capability_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE laboratory_capability_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY laboratory_capability_decisions_select_scope
    ON laboratory_capability_decisions FOR SELECT
    USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY laboratory_capability_decisions_insert_scope
    ON laboratory_capability_decisions FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM laboratory_capability_claims claim
            WHERE claim.id=laboratory_capability_decisions.claim_id
              AND claim.organization_id=laboratory_capability_decisions.organization_id
        )
    );

CREATE OR REPLACE FUNCTION enforce_laboratory_capability_parent_scope()
RETURNS trigger AS $lab_capability_parent_guard$
DECLARE
    vendor_organization UUID;
    method_owner UUID;
    method_visibility TEXT;
    form_peptide UUID;
BEGIN
    SELECT vendor.organization_id
      INTO vendor_organization
    FROM vendor_services service
    JOIN vendors vendor ON vendor.id=service.vendor_id
    JOIN vendor_sites site ON site.id=service.site_id
    WHERE service.id=NEW.service_id
      AND service.review_status='verified'
      AND vendor.review_status='verified'
      AND vendor.verification_status='verified'
      AND site.review_status='verified'
      AND site.organization_id=vendor.organization_id;

    IF vendor_organization IS NULL OR vendor_organization IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Laboratory capability claim must reference a verified service and facility owned by the same organization';
    END IF;

    SELECT owner_organization_id, visibility_scope
      INTO method_owner, method_visibility
    FROM analytical_methods
    WHERE id=NEW.method_id
      AND review_status='verified';

    IF NOT FOUND OR NOT (
        method_visibility='public'
        OR method_owner=NEW.organization_id
    ) THEN
        RAISE EXCEPTION 'Laboratory capability claim must reference a verified public or organization-owned method';
    END IF;

    IF NEW.peptide_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM peptides
        WHERE id=NEW.peptide_id AND review_status='verified'
    ) THEN
        RAISE EXCEPTION 'Laboratory capability claim peptide must be verified';
    END IF;

    IF NEW.chemical_form_id IS NOT NULL THEN
        SELECT peptide_id INTO form_peptide
        FROM peptide_chemical_forms
        WHERE id=NEW.chemical_form_id AND review_status='verified';

        IF form_peptide IS NULL OR form_peptide IS DISTINCT FROM NEW.peptide_id THEN
            RAISE EXCEPTION 'Laboratory capability chemical form must be verified and belong to the selected peptide';
        END IF;
    END IF;

    RETURN NEW;
END;
$lab_capability_parent_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS laboratory_capability_parent_scope_guard ON laboratory_capability_claims;
CREATE TRIGGER laboratory_capability_parent_scope_guard
    BEFORE INSERT OR UPDATE OF organization_id, service_id, method_id, peptide_id, chemical_form_id
    ON laboratory_capability_claims
    FOR EACH ROW EXECUTE FUNCTION enforce_laboratory_capability_parent_scope();

CREATE OR REPLACE FUNCTION enforce_laboratory_capability_decision_owner()
RETURNS trigger AS $lab_capability_decision_guard$
DECLARE
    claim_organization UUID;
BEGIN
    SELECT organization_id INTO claim_organization
    FROM laboratory_capability_claims
    WHERE id=NEW.claim_id;

    IF claim_organization IS NULL OR claim_organization IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Laboratory capability decision organization must match its claim owner';
    END IF;
    RETURN NEW;
END;
$lab_capability_decision_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS laboratory_capability_decision_owner_guard ON laboratory_capability_decisions;
CREATE TRIGGER laboratory_capability_decision_owner_guard
    BEFORE INSERT OR UPDATE OF claim_id, organization_id
    ON laboratory_capability_decisions
    FOR EACH ROW EXECUTE FUNCTION enforce_laboratory_capability_decision_owner();

COMMENT ON POLICY laboratory_capability_claims_select_scope ON laboratory_capability_claims IS
    'Claims are owner-private by default; public reads require explicit public scope and verified vendor, facility, service, method and optional peptide/form identity.';
COMMENT ON POLICY laboratory_capability_decisions_select_scope ON laboratory_capability_decisions IS
    'Laboratory capability review decisions are visible only to the organization that owns the review.';
