-- Protect organization-owned curation reviews and their append-only decisions.
-- Legacy reviews/decisions without a recoverable owner remain inaccessible until curated.

ALTER TABLE curation_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE curation_reviews FORCE ROW LEVEL SECURITY;
CREATE POLICY curation_reviews_select_scope ON curation_reviews FOR SELECT
USING (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY curation_reviews_insert_scope ON curation_reviews FOR INSERT
WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY curation_reviews_update_scope ON curation_reviews FOR UPDATE
USING (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE curation_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE curation_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY curation_decisions_select_scope ON curation_decisions FOR SELECT
USING (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY curation_decisions_insert_scope ON curation_decisions FOR INSERT
WITH CHECK (
    owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM curation_reviews review
        WHERE review.id=curation_decisions.review_id
          AND review.owner_organization_id=curation_decisions.owner_organization_id
    )
);

COMMENT ON POLICY curation_reviews_select_scope ON curation_reviews IS
    'Curation queues and assignments are private to the organization that owns the review.';
COMMENT ON POLICY curation_decisions_select_scope ON curation_decisions IS
    'Decision history inherits the immutable organization owner of its parent review.';
