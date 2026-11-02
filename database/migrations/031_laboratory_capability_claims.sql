-- Facility-specific, source-backed laboratory testing capability claims.
-- This records documented claims, not proof of present capacity or method validation.
CREATE TABLE IF NOT EXISTS laboratory_capability_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES vendor_services(id) ON DELETE RESTRICT,
    method_id UUID NOT NULL REFERENCES analytical_methods(id) ON DELETE RESTRICT,
    peptide_id UUID REFERENCES peptides(id) ON DELETE RESTRICT,
    test_purpose TEXT NOT NULL CHECK (length(trim(test_purpose)) >= 5),
    material_form TEXT,
    sample_matrix TEXT NOT NULL CHECK (length(trim(sample_matrix)) >= 2),
    instrument_platform TEXT,
    sample_requirements TEXT,
    storage_shipping_requirements TEXT,
    evidence_scope TEXT NOT NULL CHECK (length(trim(evidence_scope)) >= 5),
    limitations TEXT NOT NULL CHECK (length(trim(limitations)) >= 10),
    source_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    review_status review_status NOT NULL DEFAULT 'in_review',
    submitted_by UUID NOT NULL REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lab_capability_org_review
    ON laboratory_capability_claims(organization_id, review_status, created_at);
CREATE INDEX IF NOT EXISTS idx_lab_capability_method_review
    ON laboratory_capability_claims(method_id, review_status);
CREATE INDEX IF NOT EXISTS idx_lab_capability_peptide_review
    ON laboratory_capability_claims(peptide_id, review_status);

CREATE TABLE IF NOT EXISTS laboratory_capability_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES laboratory_capability_claims(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION prevent_laboratory_capability_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'laboratory_capability_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_laboratory_capability_decisions_no_update
    ON laboratory_capability_decisions;
CREATE TRIGGER trg_laboratory_capability_decisions_no_update
    BEFORE UPDATE OR DELETE ON laboratory_capability_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_laboratory_capability_decision_mutation();
