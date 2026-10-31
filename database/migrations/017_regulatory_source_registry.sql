-- Organization-scoped registry of official regulatory information sources.
CREATE TABLE IF NOT EXISTS regulatory_source_registry (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 authority TEXT NOT NULL,
 jurisdiction TEXT NOT NULL,
 source_name TEXT NOT NULL,
 source_type TEXT NOT NULL CHECK(source_type IN ('rss','api','manual')),
 feed_url TEXT NOT NULL,
 official_domain TEXT NOT NULL,
 description TEXT NOT NULL,
 polling_interval_hours INTEGER NOT NULL DEFAULT 24 CHECK(polling_interval_hours BETWEEN 1 AND 720),
 is_active BOOLEAN NOT NULL DEFAULT TRUE,
 created_by UUID NOT NULL REFERENCES user_profiles(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(organization_id,feed_url)
);
CREATE INDEX IF NOT EXISTS idx_regulatory_source_registry_org
 ON regulatory_source_registry(organization_id,is_active,authority);
