-- Isolate vendor ownership and independently verify certification claims.
ALTER TABLE vendors
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;

-- Existing rows intentionally remain unassigned: submitter membership history is not
-- sufficient to infer which organization owns a record when users have multiple memberships.
CREATE INDEX IF NOT EXISTS idx_vendors_organization_review
    ON vendors(organization_id, review_status, created_at);

ALTER TABLE vendor_certifications
    ADD COLUMN IF NOT EXISTS verified_by UUID REFERENCES user_profiles(id),
    ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS vendor_certification_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certification_id UUID NOT NULL REFERENCES vendor_certifications(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vendor_certification_review
    ON vendor_certifications(verification_status, vendor_id);

CREATE OR REPLACE FUNCTION prevent_vendor_certification_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'vendor_certification_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_vendor_certification_decisions_no_update
    ON vendor_certification_decisions;
CREATE TRIGGER trg_vendor_certification_decisions_no_update
    BEFORE UPDATE OR DELETE ON vendor_certification_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_vendor_certification_decision_mutation();
