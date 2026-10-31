-- Formulation and stability knowledge: evidence-linked records, not executable recipes.
CREATE TABLE IF NOT EXISTS formulation_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peptide_id UUID REFERENCES peptides(id) ON DELETE SET NULL,
    formulation_name TEXT NOT NULL,
    formulation_type TEXT NOT NULL,
    delivery_system TEXT,
    intended_research_context TEXT NOT NULL,
    formulation_rationale TEXT NOT NULL,
    physical_state TEXT,
    container_closure_context TEXT,
    storage_context TEXT,
    development_stage TEXT NOT NULL DEFAULT 'research',
    limitations TEXT NOT NULL,
    review_status review_status NOT NULL DEFAULT 'draft',
    submitted_by UUID REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS formulation_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    formulation_id UUID NOT NULL REFERENCES formulation_profiles(id) ON DELETE CASCADE,
    component_name TEXT NOT NULL,
    component_role TEXT NOT NULL,
    scientific_rationale TEXT,
    concentration_context TEXT,
    source_id UUID REFERENCES source_records(id),
    review_status review_status NOT NULL DEFAULT 'draft'
);
CREATE TABLE IF NOT EXISTS formulation_stability_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    formulation_id UUID NOT NULL REFERENCES formulation_profiles(id) ON DELETE CASCADE,
    study_context TEXT NOT NULL,
    condition_description TEXT,
    duration_description TEXT,
    analytical_method_id UUID REFERENCES analytical_methods(id),
    observed_change TEXT NOT NULL,
    measurement_type TEXT,
    result_interpretation TEXT,
    limitations TEXT NOT NULL,
    source_id UUID REFERENCES source_records(id),
    review_status review_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS formulation_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    formulation_id UUID NOT NULL REFERENCES formulation_profiles(id) ON DELETE CASCADE,
    source_record_id UUID NOT NULL REFERENCES source_records(id),
    relationship TEXT NOT NULL DEFAULT 'formulation_reference',
    evidence_scope TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(formulation_id, source_record_id, relationship)
);
CREATE TABLE IF NOT EXISTS formulation_review_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    formulation_id UUID NOT NULL REFERENCES formulation_profiles(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_formulation_profiles_review
    ON formulation_profiles(review_status, formulation_type);
CREATE INDEX IF NOT EXISTS idx_formulation_stability_profile
    ON formulation_stability_observations(formulation_id, review_status);
CREATE OR REPLACE FUNCTION prevent_formulation_review_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'formulation_review_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_formulation_review_decisions_no_update ON formulation_review_decisions;
CREATE TRIGGER trg_formulation_review_decisions_no_update
    BEFORE UPDATE OR DELETE ON formulation_review_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_formulation_review_decision_mutation();
