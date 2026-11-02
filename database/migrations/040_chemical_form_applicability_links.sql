-- Bind applicability and facility capability claims to an explicit peptide chemical form.
-- NULL remains valid for legacy sequence-level or unspecified-form records.
-- A supplied form must belong to the same peptide entity as the parent claim.

ALTER TABLE peptide_method_applicability
    ADD COLUMN IF NOT EXISTS chemical_form_id UUID
        REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT;
ALTER TABLE peptide_test_applicability
    ADD COLUMN IF NOT EXISTS chemical_form_id UUID
        REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT;
ALTER TABLE laboratory_capability_claims
    ADD COLUMN IF NOT EXISTS chemical_form_id UUID
        REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_peptide_method_applicability_form
    ON peptide_method_applicability(chemical_form_id)
    WHERE chemical_form_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_peptide_test_applicability_form
    ON peptide_test_applicability(chemical_form_id)
    WHERE chemical_form_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_laboratory_capability_form
    ON laboratory_capability_claims(chemical_form_id)
    WHERE chemical_form_id IS NOT NULL;

CREATE OR REPLACE FUNCTION enforce_peptide_chemical_form_parent()
RETURNS trigger AS $$
DECLARE
    v_form_id UUID;
    v_record_peptide_id UUID;
    v_form_peptide_id UUID;
BEGIN
    v_form_id := NULLIF(to_jsonb(NEW)->>TG_ARGV[0], '')::uuid;
    IF v_form_id IS NULL THEN
        RETURN NEW;
    END IF;

    v_record_peptide_id := NULLIF(to_jsonb(NEW)->>TG_ARGV[1], '')::uuid;
    SELECT peptide_id INTO v_form_peptide_id
    FROM peptide_chemical_forms
    WHERE id = v_form_id;

    IF v_form_peptide_id IS NULL THEN
        RAISE EXCEPTION 'Chemical form % does not exist or has no peptide owner', v_form_id
            USING ERRCODE = '23503';
    END IF;

    IF v_record_peptide_id IS DISTINCT FROM v_form_peptide_id THEN
        RAISE EXCEPTION
            'Chemical form % belongs to peptide %, not parent record peptide %',
            v_form_id, v_form_peptide_id, v_record_peptide_id
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_peptide_method_applicability_form_parent
    ON peptide_method_applicability;
CREATE TRIGGER trg_peptide_method_applicability_form_parent
    BEFORE INSERT OR UPDATE OF chemical_form_id, peptide_id
    ON peptide_method_applicability
    FOR EACH ROW
    EXECUTE FUNCTION enforce_peptide_chemical_form_parent('chemical_form_id', 'peptide_id');

DROP TRIGGER IF EXISTS trg_peptide_test_applicability_form_parent
    ON peptide_test_applicability;
CREATE TRIGGER trg_peptide_test_applicability_form_parent
    BEFORE INSERT OR UPDATE OF chemical_form_id, peptide_id
    ON peptide_test_applicability
    FOR EACH ROW
    EXECUTE FUNCTION enforce_peptide_chemical_form_parent('chemical_form_id', 'peptide_id');

DROP TRIGGER IF EXISTS trg_laboratory_capability_form_parent
    ON laboratory_capability_claims;
CREATE TRIGGER trg_laboratory_capability_form_parent
    BEFORE INSERT OR UPDATE OF chemical_form_id, peptide_id
    ON laboratory_capability_claims
    FOR EACH ROW
    EXECUTE FUNCTION enforce_peptide_chemical_form_parent('chemical_form_id', 'peptide_id');

COMMENT ON COLUMN peptide_method_applicability.chemical_form_id IS
    'Optional explicit form scope; NULL preserves legacy or sequence-level applicability and must not be read as all forms.';
COMMENT ON COLUMN peptide_test_applicability.chemical_form_id IS
    'Optional explicit form scope; NULL preserves legacy or sequence-level applicability and must not be read as all forms.';
COMMENT ON COLUMN laboratory_capability_claims.chemical_form_id IS
    'Optional explicit form scope for the claimed facility capability; does not establish current capacity or validation.';
