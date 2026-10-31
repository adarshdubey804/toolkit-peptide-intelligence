-- Regulatory guidance intelligence. Records are references, not compliance determinations.
CREATE TABLE IF NOT EXISTS regulatory_guidance_records (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id),
 authority TEXT NOT NULL,
 jurisdiction TEXT NOT NULL,
 document_type TEXT NOT NULL,
 document_title TEXT NOT NULL,
 document_identifier TEXT,
 version_or_revision TEXT,
 publication_date DATE,
 effective_date DATE,
 scope_summary TEXT NOT NULL,
 limitations TEXT,
 source_record_id UUID NOT NULL REFERENCES source_records(id),
 review_status review_status NOT NULL DEFAULT 'in_review',
 submitted_by UUID NOT NULL REFERENCES user_profiles(id),
 reviewed_by UUID REFERENCES user_profiles(id),
 reviewed_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reg_guidance_verified
 ON regulatory_guidance_records(jurisdiction, authority, document_type)
 WHERE review_status='verified';
CREATE INDEX IF NOT EXISTS idx_reg_guidance_queue
 ON regulatory_guidance_records(organization_id, review_status, created_at DESC);
CREATE TABLE IF NOT EXISTS regulatory_guidance_decisions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 guidance_id UUID NOT NULL REFERENCES regulatory_guidance_records(id) ON DELETE RESTRICT,
 organization_id UUID NOT NULL REFERENCES organizations(id),
 reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
 decision TEXT NOT NULL CHECK(decision IN ('verified','rejected','needs_changes')),
 rationale TEXT NOT NULL CHECK(length(trim(rationale))>=20),
 decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION prevent_reg_guidance_decision_mutation()
RETURNS trigger AS $$ BEGIN
 RAISE EXCEPTION 'regulatory_guidance_decisions is append-only';
END; $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_reg_guidance_decisions_no_update ON regulatory_guidance_decisions;
CREATE TRIGGER trg_reg_guidance_decisions_no_update
 BEFORE UPDATE OR DELETE ON regulatory_guidance_decisions
 FOR EACH ROW EXECUTE FUNCTION prevent_reg_guidance_decision_mutation();
