-- Chemical forms are organization-owned submissions until an explicit review
-- decision promotes a verified form to the shared public catalogue.
ALTER TABLE peptide_chemical_forms
    ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS submitted_by UUID REFERENCES user_profiles(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS visibility_scope TEXT NOT NULL DEFAULT 'restricted',
    ADD COLUMN IF NOT EXISTS evidence_scope TEXT;

ALTER TABLE peptide_chemical_forms
    ADD CONSTRAINT peptide_chemical_forms_visibility_scope_check
    CHECK (visibility_scope IN ('organization','public','restricted'));

CREATE INDEX IF NOT EXISTS idx_peptide_chemical_forms_owner_review
    ON peptide_chemical_forms(owner_organization_id, review_status);

CREATE TABLE IF NOT EXISTS peptide_chemical_form_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chemical_form_id UUID NOT NULL REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE RESTRICT,
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes')),
    visibility_scope TEXT NOT NULL DEFAULT 'organization'
        CHECK (visibility_scope IN ('organization','public')),
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (decision='verified' OR visibility_scope='organization')
);

CREATE INDEX IF NOT EXISTS idx_peptide_chemical_form_decisions_form
    ON peptide_chemical_form_decisions(chemical_form_id, created_at DESC);

CREATE OR REPLACE FUNCTION prevent_peptide_chemical_form_decision_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Chemical-form decisions are append-only; create a new decision instead';
END
$$;

CREATE TRIGGER trg_peptide_chemical_form_decisions_immutable
BEFORE UPDATE OR DELETE ON peptide_chemical_form_decisions
FOR EACH ROW
EXECUTE FUNCTION prevent_peptide_chemical_form_decision_mutation();

CREATE OR REPLACE FUNCTION require_review_for_public_peptide_chemical_form()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.visibility_scope='public' AND (
        NEW.review_status <> 'verified'
        OR NEW.owner_organization_id IS NULL
        OR NOT EXISTS (
            SELECT 1
            FROM peptide_chemical_form_decisions decision
            WHERE decision.chemical_form_id=NEW.id
              AND decision.organization_id=NEW.owner_organization_id
              AND decision.decision='verified'
              AND decision.visibility_scope='public'
        )
    ) THEN
        RAISE EXCEPTION 'A peptide chemical form requires an explicit public verification decision before publication';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER trg_peptide_chemical_form_publication_review
BEFORE INSERT OR UPDATE OF visibility_scope, review_status ON peptide_chemical_forms
FOR EACH ROW
EXECUTE FUNCTION require_review_for_public_peptide_chemical_form();

ALTER TABLE peptide_chemical_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_chemical_forms FORCE ROW LEVEL SECURITY;

CREATE POLICY peptide_chemical_forms_select_scope
ON peptide_chemical_forms FOR SELECT
USING (
    owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    OR (visibility_scope='public' AND review_status='verified')
);

CREATE POLICY peptide_chemical_forms_insert_scope
ON peptide_chemical_forms FOR INSERT
WITH CHECK (
    owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND submitted_by = NULLIF(current_setting('app.user_id', true), '')::uuid
    AND visibility_scope='organization'
);

CREATE POLICY peptide_chemical_forms_update_scope
ON peptide_chemical_forms FOR UPDATE
USING (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
WITH CHECK (owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE peptide_chemical_form_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_chemical_form_decisions FORCE ROW LEVEL SECURITY;

CREATE POLICY peptide_chemical_form_decisions_select_scope
ON peptide_chemical_form_decisions FOR SELECT
USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

CREATE POLICY peptide_chemical_form_decisions_insert_scope
ON peptide_chemical_form_decisions FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND reviewer_id = NULLIF(current_setting('app.user_id', true), '')::uuid
    AND EXISTS (
        SELECT 1 FROM peptide_chemical_forms form
        WHERE form.id=peptide_chemical_form_decisions.chemical_form_id
          AND form.owner_organization_id=peptide_chemical_form_decisions.organization_id
    )
);

COMMENT ON TABLE peptide_chemical_forms IS
    'Organization-owned chemical-form submissions; only explicitly verified public forms are shared in the scientific catalogue.';
COMMENT ON COLUMN peptide_chemical_forms.identity_fingerprint IS
    'Optional versioned chemical identity fingerprint. Do not populate from sequence-only or unreviewed notation; not unique.';
COMMENT ON POLICY peptide_chemical_forms_select_scope ON peptide_chemical_forms IS
    'Owners can read their submissions; other users can read only verified forms explicitly promoted to public.';
COMMENT ON POLICY peptide_chemical_form_decisions_insert_scope ON peptide_chemical_form_decisions IS
    'A reviewer can append a decision only for a chemical form owned by the same organization and authenticated reviewer.';
