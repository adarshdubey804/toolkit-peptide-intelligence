-- Evidence-backed applicability of a catalogue quality test to a specific peptide.
-- This is not a recommended universal panel, analytical procedure or acceptance specification.
CREATE TABLE IF NOT EXISTS peptide_test_applicability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    peptide_id UUID NOT NULL REFERENCES peptides(id) ON DELETE RESTRICT,
    test_id UUID NOT NULL REFERENCES analytical_test_catalogue(id) ON DELETE RESTRICT,
    applicability_status TEXT NOT NULL CHECK (
        applicability_status IN ('applicable','not_applicable','conditional','undetermined')
    ),
    material_form TEXT,
    sample_matrix TEXT,
    intended_use_context TEXT,
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    evidence_scope TEXT NOT NULL CHECK (length(trim(evidence_scope)) >= 5),
    limitations TEXT NOT NULL CHECK (length(trim(limitations)) >= 10),
    source_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    review_status review_status NOT NULL DEFAULT 'in_review',
    submitted_by UUID NOT NULL REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, peptide_id, test_id, applicability_status, source_id)
);

CREATE INDEX IF NOT EXISTS idx_peptide_test_applicability_org_review
    ON peptide_test_applicability(organization_id, review_status, peptide_id);
CREATE INDEX IF NOT EXISTS idx_peptide_test_applicability_test
    ON peptide_test_applicability(test_id, peptide_id, review_status);

CREATE TABLE IF NOT EXISTS peptide_test_applicability_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    applicability_id UUID NOT NULL REFERENCES peptide_test_applicability(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_peptide_test_applicability_decisions_org
    ON peptide_test_applicability_decisions(organization_id, applicability_id, decided_at DESC);

CREATE OR REPLACE FUNCTION prevent_peptide_test_applicability_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'peptide_test_applicability_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_peptide_test_applicability_decisions_no_update
    ON peptide_test_applicability_decisions;
CREATE TRIGGER trg_peptide_test_applicability_decisions_no_update
    BEFORE UPDATE OR DELETE ON peptide_test_applicability_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_peptide_test_applicability_decision_mutation();
