-- Independently curate vendor and laboratory service capability claims.
ALTER TABLE vendor_services
    ADD COLUMN IF NOT EXISTS review_status review_status NOT NULL DEFAULT 'in_review',
    ADD COLUMN IF NOT EXISTS submitted_by UUID REFERENCES user_profiles(id),
    ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES user_profiles(id),
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_vendor_services_review
    ON vendor_services(review_status, vendor_id);

CREATE TABLE IF NOT EXISTS vendor_service_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID NOT NULL REFERENCES vendor_services(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION prevent_vendor_service_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'vendor_service_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_vendor_service_decisions_no_update ON vendor_service_decisions;
CREATE TRIGGER trg_vendor_service_decisions_no_update
    BEFORE UPDATE OR DELETE ON vendor_service_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_vendor_service_decision_mutation();
