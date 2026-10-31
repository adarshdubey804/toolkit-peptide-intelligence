-- Source-linked peptide-target interaction evidence and analysis records.
CREATE TABLE IF NOT EXISTS molecular_interaction_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peptide_id UUID NOT NULL REFERENCES peptides(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES targets(id) ON DELETE RESTRICT,
    structure_identifier TEXT,
    structure_source_url TEXT,
    interaction_method TEXT NOT NULL CHECK (interaction_method IN (
        'experimental_complex', 'computational_docking', 'molecular_dynamics',
        'interface_analysis', 'literature_report', 'other'
    )),
    evidence_type evidence_type NOT NULL DEFAULT 'unknown',
    analysis_tool TEXT,
    analysis_version TEXT,
    interface_summary TEXT NOT NULL,
    interacting_residues JSONB NOT NULL DEFAULT '[]'::jsonb,
    interaction_features JSONB NOT NULL DEFAULT '[]'::jsonb,
    score_name TEXT,
    score_value NUMERIC,
    score_unit TEXT,
    score_interpretation TEXT,
    limitations TEXT NOT NULL,
    source_id UUID NOT NULL REFERENCES source_records(id),
    review_status review_status NOT NULL DEFAULT 'draft',
    submitted_by UUID REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (structure_source_url IS NULL OR structure_source_url LIKE 'https://%')
);
CREATE INDEX IF NOT EXISTS idx_interaction_assessments_peptide
    ON molecular_interaction_assessments(peptide_id, review_status);
CREATE INDEX IF NOT EXISTS idx_interaction_assessments_target
    ON molecular_interaction_assessments(target_id, review_status);
CREATE TABLE IF NOT EXISTS molecular_interaction_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES molecular_interaction_assessments(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION prevent_molecular_interaction_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'molecular_interaction_decisions is append-only';
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_molecular_interaction_decisions_no_update ON molecular_interaction_decisions;
CREATE TRIGGER trg_molecular_interaction_decisions_no_update
    BEFORE UPDATE OR DELETE ON molecular_interaction_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_molecular_interaction_decision_mutation();
