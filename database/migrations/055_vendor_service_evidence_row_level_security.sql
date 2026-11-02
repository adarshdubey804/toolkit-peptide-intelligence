-- Protect vendor service claims and source-backed service-to-peptide/method links.
-- Public reads require verified vendor, facility, service and evidence relationships.

ALTER TABLE vendor_services ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_services FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_services_select_scope ON vendor_services FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_services.vendor_id
          AND (
              vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
              OR (
                  vendor.verification_status='verified'
                  AND vendor.review_status='verified'
                  AND EXISTS (
                      SELECT 1 FROM vendor_sites site
                      WHERE site.id=vendor_services.site_id
                        AND site.vendor_id=vendor_services.vendor_id
                        AND site.organization_id=vendor.organization_id
                        AND site.review_status='verified'
                  )
                  AND vendor_services.review_status='verified'
              )
          )
    )
);
CREATE POLICY vendor_services_insert_scope ON vendor_services FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_services.vendor_id
          AND vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
          AND (
              vendor_services.site_id IS NULL
              OR EXISTS (
                  SELECT 1 FROM vendor_sites site
                  WHERE site.id=vendor_services.site_id
                    AND site.vendor_id=vendor_services.vendor_id
                    AND site.organization_id=vendor.organization_id
              )
          )
    )
);
CREATE POLICY vendor_services_update_scope ON vendor_services FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_services.vendor_id
          AND vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM vendors vendor
        WHERE vendor.id=vendor_services.vendor_id
          AND vendor.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
          AND (
              vendor_services.site_id IS NULL
              OR EXISTS (
                  SELECT 1 FROM vendor_sites site
                  WHERE site.id=vendor_services.site_id
                    AND site.vendor_id=vendor_services.vendor_id
                    AND site.organization_id=vendor.organization_id
              )
          )
    )
);

ALTER TABLE vendor_service_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_service_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_service_decisions_select_scope ON vendor_service_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY vendor_service_decisions_insert_scope ON vendor_service_decisions FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM vendor_services service
        JOIN vendors vendor ON vendor.id=service.vendor_id
        WHERE service.id=vendor_service_decisions.service_id
          AND vendor.organization_id=vendor_service_decisions.organization_id
    )
);

ALTER TABLE vendor_service_evidence_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_service_evidence_links FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_service_evidence_links_select_scope ON vendor_service_evidence_links FOR SELECT
USING (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    OR (
        review_status='verified'
        AND EXISTS (
            SELECT 1 FROM vendor_services service
            JOIN vendors vendor ON vendor.id=service.vendor_id
            JOIN vendor_sites site ON site.id=service.site_id
            WHERE service.id=vendor_service_evidence_links.service_id
              AND service.review_status='verified'
              AND vendor.verification_status='verified'
              AND vendor.review_status='verified'
              AND site.review_status='verified'
              AND site.organization_id=vendor.organization_id
              AND (vendor_service_evidence_links.peptide_id IS NULL OR EXISTS (
                  SELECT 1 FROM peptides peptide
                  WHERE peptide.id=vendor_service_evidence_links.peptide_id
                    AND peptide.review_status='verified'
              ))
              AND (vendor_service_evidence_links.method_id IS NULL OR EXISTS (
                  SELECT 1 FROM analytical_methods method
                  WHERE method.id=vendor_service_evidence_links.method_id
                    AND method.review_status='verified'
              ))
        )
    )
);
CREATE POLICY vendor_service_evidence_links_insert_scope ON vendor_service_evidence_links FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM vendor_services service
        JOIN vendors vendor ON vendor.id=service.vendor_id
        WHERE service.id=vendor_service_evidence_links.service_id
          AND vendor.organization_id=vendor_service_evidence_links.organization_id
    )
);
CREATE POLICY vendor_service_evidence_links_update_scope ON vendor_service_evidence_links FOR UPDATE
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM vendor_services service
        JOIN vendors vendor ON vendor.id=service.vendor_id
        WHERE service.id=vendor_service_evidence_links.service_id
          AND vendor.organization_id=vendor_service_evidence_links.organization_id
    )
);

ALTER TABLE vendor_service_evidence_link_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_service_evidence_link_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY vendor_service_evidence_link_decisions_select_scope ON vendor_service_evidence_link_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY vendor_service_evidence_link_decisions_insert_scope ON vendor_service_evidence_link_decisions FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM vendor_service_evidence_links link
        WHERE link.id=vendor_service_evidence_link_decisions.link_id
          AND link.organization_id=vendor_service_evidence_link_decisions.organization_id
    )
);

COMMENT ON POLICY vendor_services_select_scope ON vendor_services IS
    'Service claims are public only when their vendor, facility and service review are verified.';
COMMENT ON POLICY vendor_service_evidence_links_select_scope ON vendor_service_evidence_links IS
    'Service-to-peptide/method evidence is public only when the service, vendor, facility and linked scientific identity are verified.';
