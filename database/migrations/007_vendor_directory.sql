-- Vendor and laboratory directory provenance and review controls.
ALTER TABLE vendors
    ADD COLUMN IF NOT EXISTS review_status review_status NOT NULL DEFAULT 'draft',
    ADD COLUMN IF NOT EXISTS submitted_by UUID REFERENCES user_profiles(id),
    ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES user_profiles(id),
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS vendor_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    source_record_id UUID NOT NULL REFERENCES source_records(id),
    relationship TEXT NOT NULL DEFAULT 'vendor_identity_or_capability',
    evidence_scope TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(vendor_id, source_record_id, relationship)
);
CREATE TABLE IF NOT EXISTS vendor_review_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_vendors_review_queue
    ON vendors(review_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vendor_sources_vendor
    ON vendor_sources(vendor_id);
CREATE OR REPLACE FUNCTION prevent_vendor_review_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'vendor_review_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_vendor_review_decisions_no_update ON vendor_review_decisions;
CREATE TRIGGER trg_vendor_review_decisions_no_update
    BEFORE UPDATE OR DELETE ON vendor_review_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_vendor_review_decision_mutation();
