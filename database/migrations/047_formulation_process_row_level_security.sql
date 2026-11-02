-- Extend transaction-scoped RLS to formulation and process-knowledge records.
-- Public reads require verified parent records and verified child observations.
-- Organization-owned records remain visible only in the owner's transaction context.

ALTER TABLE formulation_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE formulation_profiles FORCE ROW LEVEL SECURITY;
CREATE POLICY formulation_profiles_select_scope
    ON formulation_profiles FOR SELECT
    USING (
        (visibility_scope='public' AND review_status='verified')
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY formulation_profiles_insert_scope
    ON formulation_profiles FOR INSERT
    WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY formulation_profiles_update_scope
    ON formulation_profiles FOR UPDATE
    USING (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
    WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE formulation_components ENABLE ROW LEVEL SECURITY;
ALTER TABLE formulation_components FORCE ROW LEVEL SECURITY;
CREATE POLICY formulation_components_select_scope
    ON formulation_components FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND (
                  (fp.visibility_scope='public' AND fp.review_status='verified' AND review_status='verified')
                  OR fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
              )
        )
    );
CREATE POLICY formulation_components_insert_scope
    ON formulation_components FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );
CREATE POLICY formulation_components_update_scope
    ON formulation_components FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );

ALTER TABLE formulation_stability_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE formulation_stability_observations FORCE ROW LEVEL SECURITY;
CREATE POLICY formulation_stability_observations_select_scope
    ON formulation_stability_observations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND (
                  (fp.visibility_scope='public' AND fp.review_status='verified' AND review_status='verified')
                  OR fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
              )
        )
    );
CREATE POLICY formulation_stability_observations_insert_scope
    ON formulation_stability_observations FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );
CREATE POLICY formulation_stability_observations_update_scope
    ON formulation_stability_observations FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );

ALTER TABLE formulation_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE formulation_sources FORCE ROW LEVEL SECURITY;
CREATE POLICY formulation_sources_select_scope
    ON formulation_sources FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND (
                  (fp.visibility_scope='public' AND fp.review_status='verified')
                  OR fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
              )
        )
    );
CREATE POLICY formulation_sources_insert_scope
    ON formulation_sources FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );
CREATE POLICY formulation_sources_update_scope
    ON formulation_sources FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );

ALTER TABLE formulation_review_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE formulation_review_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY formulation_review_decisions_select_scope
    ON formulation_review_decisions FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY formulation_review_decisions_insert_scope
    ON formulation_review_decisions FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM formulation_profiles fp
            WHERE fp.id=formulation_id
              AND fp.owner_organization_id = organization_id
        )
    );

ALTER TABLE process_knowledge_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE process_knowledge_profiles FORCE ROW LEVEL SECURITY;
CREATE POLICY process_knowledge_profiles_select_scope
    ON process_knowledge_profiles FOR SELECT
    USING (
        (visibility_scope='public' AND review_status='verified')
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY process_knowledge_profiles_insert_scope
    ON process_knowledge_profiles FOR INSERT
    WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY process_knowledge_profiles_update_scope
    ON process_knowledge_profiles FOR UPDATE
    USING (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
    WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE process_knowledge_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE process_knowledge_stages FORCE ROW LEVEL SECURITY;
CREATE POLICY process_knowledge_stages_select_scope
    ON process_knowledge_stages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM process_knowledge_profiles pk
            WHERE pk.id=profile_id
              AND (
                  (pk.visibility_scope='public' AND pk.review_status='verified' AND review_status='verified')
                  OR pk.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
              )
        )
    );
CREATE POLICY process_knowledge_stages_insert_scope
    ON process_knowledge_stages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM process_knowledge_profiles pk
            WHERE pk.id=profile_id
              AND pk.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );
CREATE POLICY process_knowledge_stages_update_scope
    ON process_knowledge_stages FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM process_knowledge_profiles pk
            WHERE pk.id=profile_id
              AND pk.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM process_knowledge_profiles pk
            WHERE pk.id=profile_id
              AND pk.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );

ALTER TABLE process_knowledge_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE process_knowledge_sources FORCE ROW LEVEL SECURITY;
CREATE POLICY process_knowledge_sources_select_scope
    ON process_knowledge_sources FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM process_knowledge_profiles pk
            WHERE pk.id=profile_id
              AND (
                  (pk.visibility_scope='public' AND pk.review_status='verified')
                  OR pk.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
              )
        )
    );
CREATE POLICY process_knowledge_sources_insert_scope
    ON process_knowledge_sources FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM process_knowledge_profiles pk
            WHERE pk.id=profile_id
              AND pk.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );
CREATE POLICY process_knowledge_sources_update_scope
    ON process_knowledge_sources FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM process_knowledge_profiles pk
            WHERE pk.id=profile_id
              AND pk.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM process_knowledge_profiles pk
            WHERE pk.id=profile_id
              AND pk.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        )
    );

ALTER TABLE process_knowledge_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE process_knowledge_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY process_knowledge_decisions_select_scope
    ON process_knowledge_decisions FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY process_knowledge_decisions_insert_scope
    ON process_knowledge_decisions FOR INSERT
    WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
        AND EXISTS (
            SELECT 1 FROM process_knowledge_profiles pk
            WHERE pk.id=profile_id
              AND pk.owner_organization_id = organization_id
        )
    );

COMMENT ON POLICY formulation_profiles_select_scope ON formulation_profiles IS
    'Public formulation reads require verified parent status; private records are owner-organization scoped.';
COMMENT ON POLICY formulation_components_select_scope ON formulation_components IS
    'Public formulation components require both verified parent and child status; owner organizations retain draft visibility.';
COMMENT ON POLICY process_knowledge_profiles_select_scope ON process_knowledge_profiles IS
    'Public process-knowledge reads require verified parent status; private records are owner-organization scoped.';
COMMENT ON POLICY process_knowledge_stages_select_scope ON process_knowledge_stages IS
    'Public process stages require both verified parent and child status; owner organizations retain draft visibility.';
