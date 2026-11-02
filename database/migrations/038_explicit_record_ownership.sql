-- Persist tenant ownership on contributed records rather than deriving it from
-- the submitter's current organization memberships. Shared master records remain public;
-- organization submissions remain private even after review until explicitly promoted.
ALTER TABLE curation_reviews
    ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;
ALTER TABLE formulation_profiles
    ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS visibility_scope TEXT NOT NULL DEFAULT 'public';
ALTER TABLE process_knowledge_profiles
    ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS visibility_scope TEXT NOT NULL DEFAULT 'public';
ALTER TABLE analytical_methods
    ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS visibility_scope TEXT NOT NULL DEFAULT 'public';

-- Backfill only when a submitter has exactly one historical membership.
-- Ambiguous legacy records are restricted rather than assigned to an arbitrary tenant.
DO $$
DECLARE v_table TEXT;
BEGIN
    FOREACH v_table IN ARRAY ARRAY['formulation_profiles','process_knowledge_profiles','analytical_methods'] LOOP
        EXECUTE format($sql$
            UPDATE %I AS record
            SET owner_organization_id = membership.organization_id,
                visibility_scope = 'organization'
            FROM (
                SELECT user_id, min(organization_id::text)::uuid AS organization_id
                FROM organization_memberships GROUP BY user_id HAVING count(*) = 1
            ) AS membership
            WHERE record.submitted_by = membership.user_id
              AND record.owner_organization_id IS NULL
        $sql$, v_table);
        EXECUTE format($sql$
            UPDATE %I AS record SET visibility_scope = 'restricted'
            WHERE record.submitted_by IS NOT NULL AND record.owner_organization_id IS NULL
        $sql$, v_table);
    END LOOP;
END
$$;

UPDATE curation_reviews AS review
SET owner_organization_id = membership.organization_id
FROM (
    SELECT user_id, min(organization_id::text)::uuid AS organization_id
    FROM organization_memberships GROUP BY user_id HAVING count(*) = 1
) AS membership
WHERE review.submitted_by = membership.user_id
  AND review.owner_organization_id IS NULL;

COMMENT ON COLUMN curation_reviews.owner_organization_id IS
    'Immutable tenant owner of this review; do not infer ownership from current membership.';
COMMENT ON COLUMN formulation_profiles.owner_organization_id IS
    'Organization that submitted this record. NULL is reserved for shared master records or unresolved legacy ownership.';
COMMENT ON COLUMN process_knowledge_profiles.owner_organization_id IS
    'Organization that submitted this record. NULL is reserved for shared master records or unresolved legacy ownership.';
COMMENT ON COLUMN analytical_methods.owner_organization_id IS
    'Organization that submitted this method. NULL is reserved for shared master records or unresolved legacy ownership.';

ALTER TABLE formulation_profiles ADD CONSTRAINT formulation_visibility_scope_check
    CHECK (visibility_scope IN ('public','organization','restricted'));
ALTER TABLE process_knowledge_profiles ADD CONSTRAINT process_knowledge_visibility_scope_check
    CHECK (visibility_scope IN ('public','organization','restricted'));
ALTER TABLE analytical_methods ADD CONSTRAINT analytical_method_visibility_scope_check
    CHECK (visibility_scope IN ('public','organization','restricted'));

CREATE INDEX IF NOT EXISTS idx_curation_reviews_owner_queue
    ON curation_reviews(owner_organization_id, review_status, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_formulation_profiles_owner_visibility
    ON formulation_profiles(owner_organization_id, visibility_scope, review_status);
CREATE INDEX IF NOT EXISTS idx_process_knowledge_owner_visibility
    ON process_knowledge_profiles(owner_organization_id, visibility_scope, review_status);
CREATE INDEX IF NOT EXISTS idx_analytical_methods_owner_visibility
    ON analytical_methods(owner_organization_id, visibility_scope, review_status);


-- Organization-specific applicability and facility capability submissions must not
-- become globally discoverable merely because a reviewer marks them verified.
ALTER TABLE peptide_method_applicability
    ADD COLUMN IF NOT EXISTS visibility_scope TEXT NOT NULL DEFAULT 'organization';
ALTER TABLE peptide_test_applicability
    ADD COLUMN IF NOT EXISTS visibility_scope TEXT NOT NULL DEFAULT 'organization';
ALTER TABLE laboratory_capability_claims
    ADD COLUMN IF NOT EXISTS visibility_scope TEXT NOT NULL DEFAULT 'organization';

ALTER TABLE peptide_method_applicability
    ADD CONSTRAINT peptide_method_applicability_visibility_check
    CHECK (visibility_scope IN ('public','organization','restricted'));
ALTER TABLE peptide_test_applicability
    ADD CONSTRAINT peptide_test_applicability_visibility_check
    CHECK (visibility_scope IN ('public','organization','restricted'));
ALTER TABLE laboratory_capability_claims
    ADD CONSTRAINT laboratory_capability_visibility_check
    CHECK (visibility_scope IN ('public','organization','restricted'));

CREATE INDEX IF NOT EXISTS idx_peptide_method_applicability_visibility
    ON peptide_method_applicability(visibility_scope, review_status);
CREATE INDEX IF NOT EXISTS idx_peptide_test_applicability_visibility
    ON peptide_test_applicability(visibility_scope, review_status);
CREATE INDEX IF NOT EXISTS idx_lab_capability_visibility
    ON laboratory_capability_claims(visibility_scope, review_status);

COMMENT ON COLUMN peptide_method_applicability.visibility_scope IS
    'Organization submissions remain private after verification unless separately promoted.';
COMMENT ON COLUMN peptide_test_applicability.visibility_scope IS
    'Organization submissions remain private after verification unless separately promoted.';
COMMENT ON COLUMN laboratory_capability_claims.visibility_scope IS
    'Facility capability claims remain private after verification unless separately promoted.';
