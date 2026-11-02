-- Vendor-specific peptide material catalogues, physical lots and source-backed batch test evidence.
-- These records distinguish catalogue descriptions from an actual supplied lot and its analytical report.
-- A supplier's stated availability or reported result is not independently verified by this schema.

CREATE TABLE IF NOT EXISTS vendor_material_offerings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE RESTRICT,
    site_id UUID REFERENCES vendor_sites(id) ON DELETE RESTRICT,
    service_id UUID REFERENCES vendor_services(id) ON DELETE RESTRICT,
    peptide_id UUID NOT NULL REFERENCES peptides(id) ON DELETE RESTRICT,
    chemical_form_id UUID NOT NULL REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT,
    product_name TEXT NOT NULL CHECK (length(trim(product_name)) >= 2),
    catalogue_reference TEXT,
    material_description TEXT,
    supplied_material_label TEXT,
    packaging_description TEXT,
    stated_storage_conditions TEXT,
    stated_shipping_conditions TEXT,
    source_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    review_status review_status NOT NULL DEFAULT 'in_review',
    submitted_by UUID NOT NULL REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    visibility_scope TEXT NOT NULL DEFAULT 'restricted'
        CHECK (visibility_scope IN ('public','organization','restricted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (visibility_scope <> 'organization' OR organization_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_vendor_material_offerings_org_review
    ON vendor_material_offerings(organization_id, review_status, vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_material_offerings_form
    ON vendor_material_offerings(chemical_form_id, review_status);
CREATE INDEX IF NOT EXISTS idx_vendor_material_offerings_peptide
    ON vendor_material_offerings(peptide_id, review_status);

CREATE TABLE IF NOT EXISTS vendor_material_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offering_id UUID NOT NULL REFERENCES vendor_material_offerings(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    lot_identifier TEXT NOT NULL CHECK (length(trim(lot_identifier)) >= 1),
    manufacturer_batch_identifier TEXT,
    manufactured_on DATE,
    retest_on DATE,
    expires_on DATE,
    quantity NUMERIC(18,6) CHECK (quantity IS NULL OR quantity >= 0),
    quantity_unit TEXT,
    availability_statement TEXT NOT NULL DEFAULT 'unknown'
        CHECK (availability_statement IN (
            'unknown','stated_available','stated_unavailable','discontinued',
            'quarantined','recalled','depleted'
        )),
    storage_conditions TEXT,
    shipping_conditions TEXT,
    source_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    review_status review_status NOT NULL DEFAULT 'in_review',
    submitted_by UUID NOT NULL REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (retest_on IS NULL OR manufactured_on IS NULL OR retest_on >= manufactured_on),
    CHECK (expires_on IS NULL OR manufactured_on IS NULL OR expires_on >= manufactured_on),
    UNIQUE(offering_id, lot_identifier)
);

CREATE INDEX IF NOT EXISTS idx_vendor_material_batches_org_review
    ON vendor_material_batches(organization_id, review_status, offering_id);
CREATE INDEX IF NOT EXISTS idx_vendor_material_batches_lot
    ON vendor_material_batches(lot_identifier);

CREATE TABLE IF NOT EXISTS batch_analytical_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES vendor_material_batches(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    test_id UUID NOT NULL REFERENCES analytical_test_catalogue(id) ON DELETE RESTRICT,
    method_id UUID NOT NULL REFERENCES analytical_methods(id) ON DELETE RESTRICT,
    laboratory_service_id UUID REFERENCES vendor_services(id) ON DELETE RESTRICT,
    tested_at TIMESTAMPTZ,
    sample_identifier TEXT,
    sample_matrix TEXT,
    method_version TEXT,
    instrument_platform TEXT,
    reference_standard TEXT,
    acceptance_criteria_source_id UUID REFERENCES source_records(id) ON DELETE RESTRICT,
    observed_value NUMERIC(24,10),
    observed_text TEXT,
    result_unit TEXT,
    result_status TEXT NOT NULL DEFAULT 'not_reported'
        CHECK (result_status IN ('pass','fail','inconclusive','not_reported')),
    interpretation TEXT,
    report_source_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    review_status review_status NOT NULL DEFAULT 'in_review',
    submitted_by UUID NOT NULL REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    supersedes_result_id UUID REFERENCES batch_analytical_test_results(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (observed_value IS NOT NULL OR NULLIF(trim(observed_text), '') IS NOT NULL),
    CHECK (supersedes_result_id IS NULL OR supersedes_result_id <> id)
);

CREATE INDEX IF NOT EXISTS idx_batch_test_results_batch
    ON batch_analytical_test_results(batch_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_batch_test_results_test_method
    ON batch_analytical_test_results(test_id, method_id, review_status);
CREATE INDEX IF NOT EXISTS idx_batch_test_results_org_review
    ON batch_analytical_test_results(organization_id, review_status, created_at);

CREATE TABLE IF NOT EXISTS batch_analytical_test_result_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id UUID NOT NULL REFERENCES batch_analytical_test_results(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_batch_test_result_decisions_org
    ON batch_analytical_test_result_decisions(organization_id, result_id, decided_at DESC);

CREATE OR REPLACE FUNCTION enforce_vendor_material_offering_scope()
RETURNS trigger AS $$
DECLARE
    v_vendor_org UUID;
    v_site_vendor UUID;
    v_site_org UUID;
    v_service_vendor UUID;
    v_service_site UUID;
    v_form_peptide UUID;
BEGIN
    SELECT organization_id INTO v_vendor_org FROM vendors WHERE id = NEW.vendor_id;
    IF v_vendor_org IS NULL OR v_vendor_org IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Vendor material offering organization must own the referenced vendor';
    END IF;

    IF NEW.site_id IS NOT NULL THEN
        SELECT vendor_id, organization_id INTO v_site_vendor, v_site_org
        FROM vendor_sites WHERE id = NEW.site_id;
        IF v_site_vendor IS DISTINCT FROM NEW.vendor_id
           OR v_site_org IS DISTINCT FROM NEW.organization_id THEN
            RAISE EXCEPTION 'Vendor material offering site must belong to the same vendor and organization';
        END IF;
    END IF;

    IF NEW.service_id IS NOT NULL THEN
        SELECT vendor_id, site_id INTO v_service_vendor, v_service_site
        FROM vendor_services WHERE id = NEW.service_id;
        IF v_service_vendor IS DISTINCT FROM NEW.vendor_id THEN
            RAISE EXCEPTION 'Vendor material offering service must belong to the same vendor';
        END IF;
        IF NEW.site_id IS NOT NULL AND v_service_site IS DISTINCT FROM NEW.site_id THEN
            RAISE EXCEPTION 'Vendor material offering service must belong to the selected site';
        END IF;
    END IF;

    SELECT peptide_id INTO v_form_peptide
    FROM peptide_chemical_forms WHERE id = NEW.chemical_form_id;
    IF v_form_peptide IS NULL OR v_form_peptide IS DISTINCT FROM NEW.peptide_id THEN
        RAISE EXCEPTION 'Vendor material offering chemical form must belong to its peptide';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_vendor_material_offering_scope
    BEFORE INSERT OR UPDATE OF organization_id, vendor_id, site_id, service_id, peptide_id, chemical_form_id
    ON vendor_material_offerings
    FOR EACH ROW EXECUTE FUNCTION enforce_vendor_material_offering_scope();

CREATE OR REPLACE FUNCTION enforce_vendor_material_batch_scope()
RETURNS trigger AS $$
DECLARE
    v_offering_org UUID;
BEGIN
    SELECT organization_id INTO v_offering_org
    FROM vendor_material_offerings WHERE id = NEW.offering_id;
    IF v_offering_org IS NULL OR v_offering_org IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Vendor material batch organization must match its offering';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_vendor_material_batch_scope
    BEFORE INSERT OR UPDATE OF offering_id, organization_id
    ON vendor_material_batches
    FOR EACH ROW EXECUTE FUNCTION enforce_vendor_material_batch_scope();

CREATE OR REPLACE FUNCTION enforce_batch_test_result_scope()
RETURNS trigger AS $$
DECLARE
    v_batch_org UUID;
    v_previous_batch UUID;
    v_previous_test UUID;
BEGIN
    SELECT organization_id INTO v_batch_org
    FROM vendor_material_batches WHERE id = NEW.batch_id;
    IF v_batch_org IS NULL OR v_batch_org IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Batch analytical result organization must match its batch record';
    END IF;

    IF NEW.supersedes_result_id IS NOT NULL THEN
        SELECT batch_id, test_id INTO v_previous_batch, v_previous_test
        FROM batch_analytical_test_results WHERE id = NEW.supersedes_result_id;
        IF v_previous_batch IS DISTINCT FROM NEW.batch_id
           OR v_previous_test IS DISTINCT FROM NEW.test_id THEN
            RAISE EXCEPTION 'A superseding batch result must refer to the same batch and analytical test';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_batch_test_result_scope
    BEFORE INSERT OR UPDATE OF batch_id, organization_id, test_id, supersedes_result_id
    ON batch_analytical_test_results
    FOR EACH ROW EXECUTE FUNCTION enforce_batch_test_result_scope();

CREATE OR REPLACE FUNCTION enforce_batch_test_result_decision_scope()
RETURNS trigger AS $$
DECLARE
    v_result_org UUID;
BEGIN
    SELECT organization_id INTO v_result_org
    FROM batch_analytical_test_results WHERE id = NEW.result_id;
    IF v_result_org IS NULL OR v_result_org IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Batch analytical result decision organization must match its result';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_batch_test_result_decision_scope
    BEFORE INSERT OR UPDATE OF result_id, organization_id
    ON batch_analytical_test_result_decisions
    FOR EACH ROW EXECUTE FUNCTION enforce_batch_test_result_decision_scope();

CREATE OR REPLACE FUNCTION prevent_batch_evidence_mutation()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION '% is retained as provenance; create a superseding or corrective record instead', TG_TABLE_NAME;
    END IF;
    IF (to_jsonb(NEW) - ARRAY['review_status','reviewed_by','reviewed_at'])
       IS DISTINCT FROM
       (to_jsonb(OLD) - ARRAY['review_status','reviewed_by','reviewed_at']) THEN
        RAISE EXCEPTION '% evidence fields are immutable; create a superseding record instead', TG_TABLE_NAME;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_vendor_material_offerings_immutable_evidence
    BEFORE UPDATE OR DELETE ON vendor_material_offerings
    FOR EACH ROW EXECUTE FUNCTION prevent_batch_evidence_mutation();
CREATE TRIGGER trg_vendor_material_batches_immutable_evidence
    BEFORE UPDATE OR DELETE ON vendor_material_batches
    FOR EACH ROW EXECUTE FUNCTION prevent_batch_evidence_mutation();
CREATE TRIGGER trg_batch_analytical_test_results_immutable_evidence
    BEFORE UPDATE OR DELETE ON batch_analytical_test_results
    FOR EACH ROW EXECUTE FUNCTION prevent_batch_evidence_mutation();

CREATE OR REPLACE FUNCTION prevent_batch_test_result_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'batch_analytical_test_result_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_batch_test_result_decisions_no_update
    BEFORE UPDATE OR DELETE ON batch_analytical_test_result_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_batch_test_result_decision_mutation();

COMMENT ON TABLE vendor_material_offerings IS
    'Vendor catalogue claims for a specific peptide chemical form; not proof of current inventory or independently verified identity.';
COMMENT ON TABLE vendor_material_batches IS
    'Supplier-specific physical lot records with source provenance; availability_statement records what the source states, not live inventory.';
COMMENT ON TABLE batch_analytical_test_results IS
    'Source-backed analytical results tied to a physical lot, test and method; result_status is not independently verified until reviewed.';
COMMENT ON COLUMN vendor_material_offerings.chemical_form_id IS
    'Required exact chemical-form identity for the offered material; sequence-only or unspecified-form offerings are not accepted here.';
COMMENT ON COLUMN batch_analytical_test_results.acceptance_criteria_source_id IS
    'Optional provenance for the criteria used to interpret the reported result; a pass label alone does not establish suitability or method validation.';
