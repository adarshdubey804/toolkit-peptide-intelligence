-- Shared fixed-window API rate limits across all backend instances.
-- One row is retained per scope/identity bucket; each new window resets its count.
CREATE TABLE IF NOT EXISTS api_rate_limit_buckets (
    bucket_key TEXT PRIMARY KEY,
    window_started_at TIMESTAMPTZ NOT NULL,
    request_count INTEGER NOT NULL CHECK (request_count >= 1),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_api_rate_limit_buckets_updated_at
    ON api_rate_limit_buckets(updated_at);

COMMENT ON TABLE api_rate_limit_buckets IS
    'Atomic shared fixed-window counters for API abuse protection; bucket keys contain endpoint scope and a client or account identifier, never credentials.';

-- Serialize retention maintenance and ensure it runs no more than once per hour.
CREATE TABLE IF NOT EXISTS api_rate_limit_maintenance (
    singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    last_cleanup_at TIMESTAMPTZ NOT NULL DEFAULT '-infinity'
);
INSERT INTO api_rate_limit_maintenance (singleton)
VALUES (TRUE)
ON CONFLICT (singleton) DO NOTHING;
