-- Source-backed links from reviewed vendor services to verified peptide/method identities.
CREATE TABLE IF NOT EXISTS vendor_service_evidence_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES vendor_services(id) ON DELETE RESTRICT,
    peptide_id UUID REFERENCES peptides(id) ON DELETE RESTRICT,
    method_id UUID REFERENCES analytical_methods(id) ON DELETE RESTRICT,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN (
        'peptide_supply','peptide_manufacturing','peptide_specific_testing',
        'method_service','formulation_development'
    )),
    evidence_scope TEXT NOT NULL CHECK (length(trim(evidence_scope)) >= 5),
    limitations TEXT NOT NULL CHECK (length(trim(limitations)) >= 10),
    source_id UUID NOT NULL REFERENCES source_records(id),
    review_status review_status NOT NULL DEFAULT 'in_review',
    submitted_by UUID NOT NULL REFERENCES user_profiles(id),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (peptide_id IS NOT NULL OR method_id IS NOT NULL),
    CHECK (relationship_type NOT IN ('peptide_supply','peptide_manufacturing','formulation_development') OR peptide_id IS NOT NULL),
    CHECK (relationship_type <> 'method_service' OR method_id IS NOT NULL),
    CHECK (relationship_type <> 'peptide_specific_testing' OR (peptide_id IS NOT NULL AND method_id IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS vendor_service_evidence_link_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id UUID NOT NULL REFERENCES vendor_service_evidence_links(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vendor_service_evidence_link_review
    ON vendor_service_evidence_links(organization_id, review_status, service_id);
CREATE INDEX IF NOT EXISTS idx_vendor_service_evidence_link_peptide
    ON vendor_service_evidence_links(peptide_id, review_status);
CREATE INDEX IF NOT EXISTS idx_vendor_service_evidence_link_method
    ON vendor_service_evidence_links(method_id, review_status);

CREATE OR REPLACE FUNCTION prevent_vendor_service_evidence_link_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'vendor_service_evidence_link_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_vendor_service_evidence_link_decisions_no_update
    ON vendor_service_evidence_link_decisions;
CREATE TRIGGER trg_vendor_service_evidence_link_decisions_no_update
    BEFORE UPDATE OR DELETE ON vendor_service_evidence_link_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_vendor_service_evidence_link_decision_mutation();
