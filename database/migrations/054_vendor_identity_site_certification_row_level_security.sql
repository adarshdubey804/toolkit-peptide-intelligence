-- Protect vendor identity, facility and certification submissions while preserving verified public directory reads.

ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendors FORCE ROW LEVEL SECURITY;
CREATE POLICY vendors_select_scope ON vendors FOR SELECT
USING (
    (verification_status='verified' AND review_status='verified')
    OR organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
);
CREATE POLICY vendors_insert_scope ON vendors FOR INSERT
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY vendors_update_scope ON vendors FOR UPDATE
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE vendor_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_sources FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_sources_select_scope ON vendor_sources FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_sources.vendor_id
          AND (
              (vendor.verification_status='verified' AND vendor.review_status='verified')
              OR vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
          )
    )
);
CREATE POLICY vendor_sources_insert_scope ON vendor_sources FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_sources.vendor_id
          AND vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
);
CREATE POLICY vendor_sources_update_scope ON vendor_sources FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_sources.vendor_id
          AND vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_sources.vendor_id
          AND vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
);

ALTER TABLE vendor_review_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_review_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_review_decisions_select_scope ON vendor_review_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY vendor_review_decisions_insert_scope ON vendor_review_decisions FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_review_decisions.vendor_id
          AND vendor.organization_id=vendor_review_decisions.organization_id
    )
);

ALTER TABLE vendor_sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_sites FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_sites_select_scope ON vendor_sites FOR SELECT
USING (
    (
        review_status='verified'
        AND EXISTS (
            SELECT 1 FROM vendors vendor
            WHERE vendor.id=vendor_sites.vendor_id
              AND vendor.verification_status='verified'
              AND vendor.review_status='verified'
        )
    )
    OR organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
);
CREATE POLICY vendor_sites_insert_scope ON vendor_sites FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_sites.vendor_id
          AND vendor.organization_id=vendor_sites.organization_id
    )
);
CREATE POLICY vendor_sites_update_scope ON vendor_sites FOR UPDATE
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_sites.vendor_id
          AND vendor.organization_id=vendor_sites.organization_id
    )
);

ALTER TABLE vendor_site_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_site_sources FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_site_sources_select_scope ON vendor_site_sources FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM vendor_sites site
        JOIN vendors vendor ON vendor.id=site.vendor_id
        WHERE site.id=vendor_site_sources.site_id
          AND (
              (site.review_status='verified' AND vendor.review_status='verified' AND vendor.verification_status='verified')
              OR site.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
          )
    )
);
CREATE POLICY vendor_site_sources_insert_scope ON vendor_site_sources FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM vendor_sites site
        WHERE site.id=vendor_site_sources.site_id
          AND site.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
);
CREATE POLICY vendor_site_sources_update_scope ON vendor_site_sources FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM vendor_sites site
        WHERE site.id=vendor_site_sources.site_id
          AND site.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM vendor_sites site
        WHERE site.id=vendor_site_sources.site_id
          AND site.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
);

ALTER TABLE vendor_site_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_site_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_site_decisions_select_scope ON vendor_site_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY vendor_site_decisions_insert_scope ON vendor_site_decisions FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM vendor_sites site
        WHERE site.id=vendor_site_decisions.site_id
          AND site.organization_id=vendor_site_decisions.organization_id
    )
);

ALTER TABLE vendor_certifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_certifications FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_certifications_select_scope ON vendor_certifications FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_certifications.vendor_id
          AND (
              (
                  vendor.verification_status='verified'
                  AND vendor.review_status='verified'
                  AND vendor_certifications.verification_status='verified'
                  AND (
                      vendor_certifications.site_id IS NULL
                      OR EXISTS (
                          SELECT 1 FROM vendor_sites site
                          WHERE site.id=vendor_certifications.site_id AND site.review_status='verified'
                      )
                  )
              )
              OR vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
          )
    )
);
CREATE POLICY vendor_certifications_insert_scope ON vendor_certifications FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_certifications.vendor_id
          AND vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
          AND (
              vendor_certifications.site_id IS NULL
              OR EXISTS (
                  SELECT 1 FROM vendor_sites site
                  WHERE site.id=vendor_certifications.site_id
                    AND site.vendor_id=vendor_certifications.vendor_id
                    AND site.organization_id=vendor.organization_id
              )
          )
    )
);
CREATE POLICY vendor_certifications_update_scope ON vendor_certifications FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_certifications.vendor_id
          AND vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_certifications.vendor_id
          AND vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
          AND (
              vendor_certifications.site_id IS NULL
              OR EXISTS (
                  SELECT 1 FROM vendor_sites site
                  WHERE site.id=vendor_certifications.site_id
                    AND site.vendor_id=vendor_certifications.vendor_id
                    AND site.organization_id=vendor.organization_id
              )
          )
    )
);

ALTER TABLE vendor_certification_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_certification_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_certification_decisions_select_scope ON vendor_certification_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY vendor_certification_decisions_insert_scope ON vendor_certification_decisions FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM vendor_certifications certification
        JOIN vendors vendor ON vendor.id=certification.vendor_id
        WHERE certification.id=vendor_certification_decisions.certification_id
          AND vendor.organization_id=vendor_certification_decisions.organization_id
    )
);

COMMENT ON POLICY vendors_select_scope ON vendors IS
    'Only verified vendor identities are public; unverified submissions remain private to their owning organization.';
COMMENT ON POLICY vendor_sites_select_scope ON vendor_sites IS
    'Facility records are public only when both the site and vendor identity are verified.';
COMMENT ON POLICY vendor_certifications_select_scope ON vendor_certifications IS
    'Certification claims are public only when the certification, vendor and any linked facility are verified.';
