-- Scheduling state and durable execution history for controlled regulatory RSS polling.
ALTER TABLE regulatory_source_registry
 ADD COLUMN IF NOT EXISTS last_polled_at TIMESTAMPTZ,
 ADD COLUMN IF NOT EXISTS next_poll_at TIMESTAMPTZ,
 ADD COLUMN IF NOT EXISTS last_poll_status TEXT CHECK(last_poll_status IN ('success','error'));
CREATE INDEX IF NOT EXISTS idx_regulatory_source_registry_due
 ON regulatory_source_registry(is_active,next_poll_at)
 WHERE source_type='rss';
CREATE TABLE IF NOT EXISTS regulatory_source_poll_runs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 source_id UUID NOT NULL REFERENCES regulatory_source_registry(id) ON DELETE CASCADE,
 trigger_type TEXT NOT NULL CHECK(trigger_type IN ('manual','scheduled')),
 status TEXT NOT NULL CHECK(status IN ('running','success','error')),
 items_seen INTEGER NOT NULL DEFAULT 0 CHECK(items_seen>=0),
 items_added INTEGER NOT NULL DEFAULT 0 CHECK(items_added>=0),
 error_code TEXT,
 started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 finished_at TIMESTAMPTZ,
 CHECK((status='running' AND finished_at IS NULL) OR (status<>'running' AND finished_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_regulatory_poll_runs_source
 ON regulatory_source_poll_runs(source_id,started_at DESC);
