-- Product- and jurisdiction-specific peptide regulatory authorizations.
-- A peptide identity is never globally labelled "FDA approved"; authorization is
-- represented against a specific product/presentation and authority/jurisdiction.
CREATE TABLE IF NOT EXISTS regulatory_product_authorizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peptide_id UUID NOT NULL REFERENCES peptides(id) ON DELETE RESTRICT,
    chemical_form_id UUID REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT,
    product_name TEXT,
    active_ingredient_name TEXT NOT NULL,
    application_identifier TEXT,
    authorization_identifier TEXT,
    jurisdiction_code TEXT NOT NULL,
    jurisdiction_name TEXT NOT NULL,
    authority_name TEXT NOT NULL,
    regulatory_status TEXT NOT NULL CHECK (
        regulatory_status IN (
            'approved',
            'conditionally_authorized',
            'emergency_authorized',
            'under_review',
            'refused',
            'withdrawn',
            'discontinued',
            'suspended',
            'not_found_in_checked_sources',
            'unknown'
        )
    ),
    indication_text TEXT,
    route_of_administration TEXT,
    dosage_form TEXT,
    strength_text TEXT,
    marketing_authorization_holder TEXT,
    original_approval_date DATE,
    effective_date DATE,
    status_end_date DATE,
    status_reason TEXT,
    label_version TEXT,
    label_url TEXT,
    source_record_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    source_locator TEXT,
    source_checked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    review_status review_status NOT NULL DEFAULT 'draft',
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT regulatory_authorization_jurisdiction_code_check
        CHECK (jurisdiction_code ~ '^[A-Z]{2}(-[A-Z0-9]{1,3})?$'),
    CONSTRAINT regulatory_authorization_dates_check
        CHECK (
            (effective_date IS NULL OR original_approval_date IS NULL
             OR effective_date >= original_approval_date)
            AND (status_end_date IS NULL OR effective_date IS NULL
                 OR status_end_date >= effective_date)
        ),
    CONSTRAINT regulatory_authorization_review_fields_check
        CHECK (
            (review_status <> 'verified' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
        )
);

CREATE INDEX IF NOT EXISTS idx_reg_product_auth_peptide_jurisdiction
    ON regulatory_product_authorizations(peptide_id, jurisdiction_code, authority_name);
CREATE INDEX IF NOT EXISTS idx_reg_product_auth_status
    ON regulatory_product_authorizations(regulatory_status, review_status);
CREATE INDEX IF NOT EXISTS idx_reg_product_auth_application
    ON regulatory_product_authorizations(application_identifier)
    WHERE application_identifier IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reg_product_auth_form
    ON regulatory_product_authorizations(chemical_form_id)
    WHERE chemical_form_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reg_product_auth_source
    ON regulatory_product_authorizations(source_record_id);

-- Preserve every material authorization change as an immutable content-addressed
-- revision. This captures corrections and status transitions without erasing history.
CREATE TABLE IF NOT EXISTS regulatory_product_authorization_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    authorization_id UUID NOT NULL
        REFERENCES regulatory_product_authorizations(id) ON DELETE RESTRICT,
    revision_number INTEGER NOT NULL CHECK (revision_number > 0),
    snapshot JSONB NOT NULL CHECK (jsonb_typeof(snapshot) = 'object'),
    content_hash CHAR(64) NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    revision_reason TEXT NOT NULL CHECK (
        revision_reason IN ('record_created', 'record_updated')
    ),
    supersedes_revision_id UUID
        REFERENCES regulatory_product_authorization_revisions(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (authorization_id, revision_number),
    CHECK (supersedes_revision_id IS NULL OR supersedes_revision_id <> id)
);

CREATE INDEX IF NOT EXISTS idx_reg_product_auth_revisions_latest
    ON regulatory_product_authorization_revisions(authorization_id, revision_number DESC);

CREATE OR REPLACE FUNCTION prevent_reg_product_authorization_revision_mutation()
RETURNS trigger AS $revision_immutable$
BEGIN
    RAISE EXCEPTION
        'Regulatory authorization revisions are immutable; update the authorization to create a new revision';
END;
$revision_immutable$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS regulatory_product_authorization_revisions_append_only
    ON regulatory_product_authorization_revisions;
CREATE TRIGGER regulatory_product_authorization_revisions_append_only
    BEFORE UPDATE OR DELETE ON regulatory_product_authorization_revisions
    FOR EACH ROW EXECUTE FUNCTION prevent_reg_product_authorization_revision_mutation();

CREATE OR REPLACE FUNCTION capture_reg_product_authorization_revision()
RETURNS trigger AS $revision_capture$
DECLARE
    previous_revision_id UUID;
    previous_revision_number INTEGER;
    record_snapshot JSONB;
    latest_snapshot JSONB;
BEGIN
    record_snapshot := to_jsonb(NEW) - 'id' - 'created_at' - 'updated_at';

    SELECT id, revision_number, snapshot
      INTO previous_revision_id, previous_revision_number, latest_snapshot
      FROM regulatory_product_authorization_revisions
     WHERE authorization_id = NEW.id
     ORDER BY revision_number DESC
     LIMIT 1;

    IF TG_OP = 'UPDATE' AND latest_snapshot = record_snapshot THEN
        RETURN NEW;
    END IF;

    INSERT INTO regulatory_product_authorization_revisions (
        authorization_id, revision_number, snapshot, content_hash,
        revision_reason, supersedes_revision_id
    ) VALUES (
        NEW.id,
        COALESCE(previous_revision_number, 0) + 1,
        record_snapshot,
        encode(digest(convert_to(record_snapshot::text, 'UTF8'), 'sha256'), 'hex'),
        CASE WHEN TG_OP = 'INSERT' THEN 'record_created' ELSE 'record_updated' END,
        previous_revision_id
    );
    RETURN NEW;
END;
$revision_capture$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS regulatory_product_authorization_revision_capture
    ON regulatory_product_authorizations;
CREATE TRIGGER regulatory_product_authorization_revision_capture
    AFTER INSERT OR UPDATE ON regulatory_product_authorizations
    FOR EACH ROW EXECUTE FUNCTION capture_reg_product_authorization_revision();

COMMENT ON TABLE regulatory_product_authorizations IS
    'Product/presentation- and jurisdiction-specific regulatory status for peptide entities. A row is not a global approval flag; absence from checked sources is represented explicitly.';
COMMENT ON COLUMN regulatory_product_authorizations.regulatory_status IS
    'Authority-specific status. not_found_in_checked_sources is limited to the documented source search and must never be interpreted as proof of non-approval.';
COMMENT ON COLUMN regulatory_product_authorizations.review_status IS
    'Only curator-verified rows should be exposed as authoritative public regulatory facts.';
COMMENT ON TABLE regulatory_product_authorization_revisions IS
    'Append-only content-addressed revision history for product-level regulatory authorization records.';
