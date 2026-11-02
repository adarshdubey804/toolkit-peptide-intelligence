-- Explicit tenant ownership for organization-contributed scientific submissions.
-- Audit events provide the strongest historical attribution. Rows that cannot be
-- attributed unambiguously remain NULL and must be manually resolved; never guess
-- ownership from a user's current multi-organization memberships.

ALTER TABLE curation_reviews
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;
ALTER TABLE curation_decisions
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;
ALTER TABLE analytical_methods
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;
ALTER TABLE formulation_profiles
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;
ALTER TABLE process_knowledge_profiles
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;
ALTER TABLE molecular_interaction_assessments
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;

-- Recover review ownership from immutable audit provenance.
UPDATE curation_reviews cr
SET organization_id = ae.organization_id
FROM audit_events ae
WHERE cr.organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'curation_review_submitted'
  AND ae.entity_type = 'curation_review'
  AND ae.entity_id = cr.id;

UPDATE curation_reviews cr
SET organization_id = ae.organization_id
FROM audit_events ae
WHERE cr.organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'peptide_dossier_created'
  AND ae.entity_type = 'peptide'
  AND ae.event_metadata ->> 'review_id' = cr.id::text;

UPDATE analytical_methods am
SET organization_id = ae.organization_id
FROM audit_events ae
WHERE am.organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'analytical_method_submitted'
  AND ae.entity_type = 'analytical_method'
  AND ae.entity_id = am.id;

UPDATE formulation_profiles fp
SET organization_id = ae.organization_id
FROM audit_events ae
WHERE fp.organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'formulation_submitted'
  AND ae.entity_type = 'formulation_profile'
  AND ae.entity_id = fp.id;

UPDATE process_knowledge_profiles pk
SET organization_id = ae.organization_id
FROM audit_events ae
WHERE pk.organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'process_knowledge_submitted'
  AND ae.entity_type = 'process_knowledge_profile'
  AND ae.entity_id = pk.id;

UPDATE molecular_interaction_assessments a
SET organization_id = ae.organization_id
FROM audit_events ae
WHERE a.organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'molecular_interaction_submitted'
  AND ae.entity_type = 'molecular_interaction_assessment'
  AND ae.entity_id = a.id;

-- Conservative fallback for legacy rows without an attributable audit event:
-- backfill only when the submitter has exactly one membership row, regardless
-- of active/suspended status. Ambiguous rows remain unassigned and are hidden
-- from organization-scoped review queues until manually resolved.
WITH sole_membership AS (
    SELECT user_id, min(organization_id::text)::uuid AS organization_id
    FROM organization_memberships
    GROUP BY user_id
    HAVING count(DISTINCT organization_id) = 1
)
UPDATE curation_reviews cr
SET organization_id = sm.organization_id
FROM sole_membership sm
WHERE cr.organization_id IS NULL AND cr.submitted_by = sm.user_id;

WITH sole_membership AS (
    SELECT user_id, min(organization_id) AS organization_id
    FROM organization_memberships
    GROUP BY user_id
    HAVING count(DISTINCT organization_id) = 1
)
UPDATE analytical_methods am
SET organization_id = sm.organization_id
FROM sole_membership sm
WHERE am.organization_id IS NULL AND am.submitted_by = sm.user_id;

WITH sole_membership AS (
    SELECT user_id, min(organization_id) AS organization_id
    FROM organization_memberships
    GROUP BY user_id
    HAVING count(DISTINCT organization_id) = 1
)
UPDATE formulation_profiles fp
SET organization_id = sm.organization_id
FROM sole_membership sm
WHERE fp.organization_id IS NULL AND fp.submitted_by = sm.user_id;

WITH sole_membership AS (
    SELECT user_id, min(organization_id) AS organization_id
    FROM organization_memberships
    GROUP BY user_id
    HAVING count(DISTINCT organization_id) = 1
)
UPDATE process_knowledge_profiles pk
SET organization_id = sm.organization_id
FROM sole_membership sm
WHERE pk.organization_id IS NULL AND pk.submitted_by = sm.user_id;

WITH sole_membership AS (
    SELECT user_id, min(organization_id) AS organization_id
    FROM organization_memberships
    GROUP BY user_id
    HAVING count(DISTINCT organization_id) = 1
)
UPDATE molecular_interaction_assessments a
SET organization_id = sm.organization_id
FROM sole_membership sm
WHERE a.organization_id IS NULL AND a.submitted_by = sm.user_id;

-- Decision history inherits the immutable owner of its parent review.
UPDATE curation_decisions cd
SET organization_id = cr.organization_id
FROM curation_reviews cr
WHERE cd.organization_id IS NULL
  AND cd.review_id = cr.id
  AND cr.organization_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_curation_reviews_org_queue
    ON curation_reviews (organization_id, review_status, priority, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_curation_decisions_org_review
    ON curation_decisions (organization_id, review_id, decided_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytical_methods_org_review
    ON analytical_methods (organization_id, review_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_formulation_profiles_org_review
    ON formulation_profiles (organization_id, review_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_process_knowledge_profiles_org_review
    ON process_knowledge_profiles (organization_id, review_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interaction_assessments_org_review
    ON molecular_interaction_assessments (organization_id, review_status, created_at DESC);

COMMENT ON COLUMN curation_reviews.organization_id IS
    'Immutable owner organization for this review request. NULL is reserved for legacy rows whose owner could not be attributed safely.';
COMMENT ON COLUMN analytical_methods.organization_id IS
    'Submitting organization owner. NULL is reserved for legacy or globally curated rows without safe historical attribution.';
COMMENT ON COLUMN formulation_profiles.organization_id IS
    'Submitting organization owner. NULL is reserved for legacy or globally curated rows without safe historical attribution.';
COMMENT ON COLUMN process_knowledge_profiles.organization_id IS
    'Submitting organization owner. NULL is reserved for legacy or globally curated rows without safe historical attribution.';
COMMENT ON COLUMN molecular_interaction_assessments.organization_id IS
    'Submitting organization owner. NULL is reserved for legacy or globally curated rows without safe historical attribution.';
