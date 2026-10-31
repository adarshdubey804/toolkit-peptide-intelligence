-- Version snapshots and human-reviewed regulatory change events.
CREATE TABLE IF NOT EXISTS regulatory_guidance_versions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 guidance_id UUID NOT NULL REFERENCES regulatory_guidance_records(id) ON DELETE RESTRICT,
 version_or_revision TEXT,
 publication_date DATE,
 effective_date DATE,
 source_url TEXT NOT NULL,
 content_hash CHAR(64),
 observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 observed_by UUID NOT NULL REFERENCES user_profiles(id),
 observation_note TEXT,
 review_status TEXT NOT NULL DEFAULT 'pending_review'
   CHECK(review_status IN ('pending_review','accepted','rejected')),
 UNIQUE(guidance_id, source_url, version_or_revision, content_hash)
);
CREATE INDEX IF NOT EXISTS idx_reg_guidance_versions
 ON regulatory_guidance_versions(guidance_id, observed_at DESC);
CREATE TABLE IF NOT EXISTS regulatory_change_events (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 guidance_id UUID NOT NULL REFERENCES regulatory_guidance_records(id) ON DELETE RESTRICT,
 previous_version_id UUID REFERENCES regulatory_guidance_versions(id),
 new_version_id UUID NOT NULL REFERENCES regulatory_guidance_versions(id),
 change_type TEXT NOT NULL CHECK(change_type IN ('new_version','source_content_changed','effective_date_changed','metadata_changed','possible_withdrawal')),
 change_summary TEXT NOT NULL,
 impact_assessment TEXT,
 status TEXT NOT NULL DEFAULT 'needs_review'
   CHECK(status IN ('needs_review','confirmed_change','not_a_change','published')),
 submitted_by UUID NOT NULL REFERENCES user_profiles(id),
 reviewed_by UUID REFERENCES user_profiles(id),
 reviewed_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reg_change_events_queue
 ON regulatory_change_events(status, created_at DESC);
CREATE TABLE IF NOT EXISTS regulatory_change_decisions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 event_id UUID NOT NULL REFERENCES regulatory_change_events(id) ON DELETE RESTRICT,
 organization_id UUID NOT NULL REFERENCES organizations(id),
 reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
 decision TEXT NOT NULL CHECK(decision IN ('confirmed_change','not_a_change','published')),
 rationale TEXT NOT NULL CHECK(length(trim(rationale))>=20),
 decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION prevent_reg_change_decision_mutation()
RETURNS trigger AS $$ BEGIN
 RAISE EXCEPTION 'regulatory_change_decisions is append-only';
END; $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_reg_change_decisions_no_update ON regulatory_change_decisions;
CREATE TRIGGER trg_reg_change_decisions_no_update
 BEFORE UPDATE OR DELETE ON regulatory_change_decisions
 FOR EACH ROW EXECUTE FUNCTION prevent_reg_change_decision_mutation();
