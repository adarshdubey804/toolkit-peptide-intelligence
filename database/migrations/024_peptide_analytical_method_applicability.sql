-- Peptide-specific analytical method applicability with source evidence and independent review.
CREATE TABLE IF NOT EXISTS peptide_method_applicability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    peptide_id UUID NOT NULL REFERENCES peptides(id) ON DELETE CASCADE,
    method_id UUID NOT NULL REFERENCES analytical_methods(id) ON DELETE RESTRICT,
    test_purpose TEXT NOT NULL CHECK (length(trim(test_purpose)) >= 5),
    material_form TEXT,
    sample_matrix TEXT,
    applicability_rationale TEXT NOT NULL CHECK (length(trim(applicability_rationale)) >= 20),
    evidence_scope TEXT NOT NULL CHECK (length(trim(evidence_scope)) >= 5),
    limitations TEXT NOT NULL CHECK (length(trim(limitations)) >= 10),
    source_id UUID NOT NULL REFERENCES source_records(id),
    review_status review_status NOT NULL DEFAULT 'in_review',
    submitted_by UUID NOT NULL REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(peptide_id, method_id, test_purpose, source_id)
);

CREATE TABLE IF NOT EXISTS peptide_method_applicability_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    applicability_id UUID NOT NULL REFERENCES peptide_method_applicability(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_peptide_method_applicability_review
    ON peptide_method_applicability(organization_id, review_status, peptide_id);
CREATE INDEX IF NOT EXISTS idx_peptide_method_applicability_method
    ON peptide_method_applicability(method_id, peptide_id, review_status);

CREATE OR REPLACE FUNCTION prevent_peptide_method_applicability_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'peptide_method_applicability_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_peptide_method_applicability_decisions_no_update
    ON peptide_method_applicability_decisions;
CREATE TRIGGER trg_peptide_method_applicability_decisions_no_update
    BEFORE UPDATE OR DELETE ON peptide_method_applicability_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_peptide_method_applicability_decision_mutation();
