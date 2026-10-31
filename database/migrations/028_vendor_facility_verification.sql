-- Facility-level vendor intelligence with organization-scoped, independent review.
ALTER TABLE vendor_sites
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS review_status review_status NOT NULL DEFAULT 'draft',
    ADD COLUMN IF NOT EXISTS submitted_by UUID REFERENCES user_profiles(id),
    ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES user_profiles(id),
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Existing site rows remain unassigned and in draft; ownership is never inferred.
CREATE INDEX IF NOT EXISTS idx_vendor_sites_org_review
    ON vendor_sites(organization_id, review_status, vendor_id);

CREATE TABLE IF NOT EXISTS vendor_site_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES vendor_sites(id) ON DELETE RESTRICT,
    source_record_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    evidence_scope TEXT NOT NULL CHECK (length(trim(evidence_scope)) >= 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(site_id, source_record_id)
);

CREATE TABLE IF NOT EXISTS vendor_site_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES vendor_sites(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION prevent_vendor_site_decision_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'vendor_site_decisions is append-only; create a corrective decision instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_vendor_site_decisions_no_update ON vendor_site_decisions;
CREATE TRIGGER trg_vendor_site_decisions_no_update
    BEFORE UPDATE OR DELETE ON vendor_site_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_vendor_site_decision_mutation();
