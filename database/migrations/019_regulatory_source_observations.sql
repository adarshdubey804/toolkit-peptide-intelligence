-- Organization-scoped RSS observations; feed items remain unreviewed until human review.
CREATE TABLE IF NOT EXISTS regulatory_source_observations (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 source_id UUID NOT NULL REFERENCES regulatory_source_registry(id) ON DELETE CASCADE,
 external_identifier TEXT NOT NULL,
 item_title TEXT NOT NULL,
 item_url TEXT NOT NULL,
 published_at TEXT,
 summary TEXT,
 content_hash CHAR(64) NOT NULL,
 raw_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
 review_status TEXT NOT NULL DEFAULT 'pending_review' CHECK(review_status IN ('pending_review','accepted','rejected','duplicate')),
 reviewed_by UUID REFERENCES user_profiles(id),
 review_rationale TEXT,
 reviewed_at TIMESTAMPTZ,
 observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(source_id,external_identifier)
);
CREATE INDEX IF NOT EXISTS idx_regulatory_source_observations_queue ON regulatory_source_observations(organization_id,review_status,observed_at DESC);
