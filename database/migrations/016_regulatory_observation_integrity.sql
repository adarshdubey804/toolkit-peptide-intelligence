-- Harden observation idempotency when optional version/hash values are NULL.
-- PostgreSQL 15+ supports NULLS NOT DISTINCT; existing deployments must use PG 15+.
CREATE UNIQUE INDEX IF NOT EXISTS uq_reg_guidance_version_observation
 ON regulatory_guidance_versions(guidance_id, source_url, version_or_revision, content_hash)
 NULLS NOT DISTINCT;
