-- Complete tenant ownership and visibility enforcement for interaction
-- submissions and curation decisions, and recover owner IDs from audit provenance.

ALTER TABLE curation_decisions
    ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;

ALTER TABLE molecular_interaction_assessments
    ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS visibility_scope TEXT NOT NULL DEFAULT 'restricted';

-- Audit events are the preferred historical ownership source because they record
-- the organization active when the submission occurred.
UPDATE curation_reviews review
SET owner_organization_id = ae.organization_id
FROM audit_events ae
WHERE review.owner_organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'curation_review_submitted'
  AND ae.entity_type = 'curation_review'
  AND ae.entity_id = review.id;

UPDATE curation_reviews review
SET owner_organization_id = ae.organization_id
FROM audit_events ae
WHERE review.owner_organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'peptide_dossier_created'
  AND ae.entity_type = 'peptide'
  AND ae.event_metadata ->> 'review_id' = review.id::text;

UPDATE analytical_methods record
SET owner_organization_id = ae.organization_id,
    visibility_scope = 'organization'
FROM audit_events ae
WHERE record.owner_organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'analytical_method_submitted'
  AND ae.entity_type = 'analytical_method'
  AND ae.entity_id = record.id;

UPDATE formulation_profiles record
SET owner_organization_id = ae.organization_id,
    visibility_scope = 'organization'
FROM audit_events ae
WHERE record.owner_organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'formulation_submitted'
  AND ae.entity_type = 'formulation_profile'
  AND ae.entity_id = record.id;

UPDATE process_knowledge_profiles record
SET owner_organization_id = ae.organization_id,
    visibility_scope = 'organization'
FROM audit_events ae
WHERE record.owner_organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'process_knowledge_submitted'
  AND ae.entity_type = 'process_knowledge_profile'
  AND ae.entity_id = record.id;

UPDATE molecular_interaction_assessments record
SET owner_organization_id = ae.organization_id,
    visibility_scope = 'organization'
FROM audit_events ae
WHERE record.owner_organization_id IS NULL
  AND ae.organization_id IS NOT NULL
  AND ae.action = 'molecular_interaction_submitted'
  AND ae.entity_type = 'molecular_interaction_assessment'
  AND ae.entity_id = record.id;

-- Conservative fallback for interaction submissions without an attributable
-- audit event. Do not assign an owner when a submitter has multiple memberships.
WITH sole_membership AS (
    SELECT user_id, min(organization_id::text)::uuid AS organization_id
    FROM organization_memberships
    GROUP BY user_id
    HAVING count(DISTINCT organization_id) = 1
)
UPDATE molecular_interaction_assessments record
SET owner_organization_id = membership.organization_id,
    visibility_scope = 'organization'
FROM sole_membership membership
WHERE record.owner_organization_id IS NULL
  AND record.submitted_by = membership.user_id;

-- Preserve legacy shared master interaction records, but keep ambiguous
-- organization submissions restricted until a human resolves their owner.
UPDATE molecular_interaction_assessments
SET visibility_scope = 'public'
WHERE submitted_by IS NULL AND owner_organization_id IS NULL;

UPDATE molecular_interaction_assessments
SET visibility_scope = 'restricted'
WHERE submitted_by IS NOT NULL AND owner_organization_id IS NULL;

UPDATE curation_decisions decision
SET owner_organization_id = review.owner_organization_id
FROM curation_reviews review
WHERE decision.owner_organization_id IS NULL
  AND decision.review_id = review.id
  AND review.owner_organization_id IS NOT NULL;

ALTER TABLE molecular_interaction_assessments
    ADD CONSTRAINT interaction_visibility_scope_check
    CHECK (visibility_scope IN ('public','organization','restricted'));
ALTER TABLE molecular_interaction_assessments
    ADD CONSTRAINT interaction_owner_scope_check
    CHECK (visibility_scope <> 'organization' OR owner_organization_id IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_curation_decisions_owner_review
    ON curation_decisions(owner_organization_id, review_id, decided_at DESC);
CREATE INDEX IF NOT EXISTS idx_interaction_assessments_owner_visibility
    ON molecular_interaction_assessments(owner_organization_id, visibility_scope, review_status);

COMMENT ON COLUMN curation_decisions.owner_organization_id IS
    'Organization owner inherited from the parent curation review.';
COMMENT ON COLUMN molecular_interaction_assessments.owner_organization_id IS
    'Organization that submitted this interaction assessment; NULL is reserved for shared master data or unresolved legacy ownership.';
COMMENT ON COLUMN molecular_interaction_assessments.visibility_scope IS
    'Verified organization submissions remain private unless separately promoted to public.';
