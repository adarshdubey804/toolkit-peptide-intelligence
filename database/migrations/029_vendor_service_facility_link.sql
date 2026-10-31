-- Attach newly curated vendor services to a specific independently verified facility.
ALTER TABLE vendor_services
    ADD COLUMN IF NOT EXISTS site_id UUID REFERENCES vendor_sites(id) ON DELETE RESTRICT;

-- Existing service claims remain unassigned; they are not backfilled to an assumed site.
CREATE INDEX IF NOT EXISTS idx_vendor_services_site_review
    ON vendor_services(site_id, review_status);
