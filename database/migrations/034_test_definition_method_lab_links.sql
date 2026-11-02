-- Connect the reference test taxonomy to peptide/method applicability and facility capability claims.
ALTER TABLE peptide_method_applicability
    ADD COLUMN IF NOT EXISTS test_definition_id UUID
        REFERENCES analytical_test_catalogue(id) ON DELETE RESTRICT;
ALTER TABLE laboratory_capability_claims
    ADD COLUMN IF NOT EXISTS test_definition_id UUID
        REFERENCES analytical_test_catalogue(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_peptide_method_applicability_test_definition
    ON peptide_method_applicability(test_definition_id, review_status);
CREATE INDEX IF NOT EXISTS idx_laboratory_capability_test_definition
    ON laboratory_capability_claims(test_definition_id, review_status);
