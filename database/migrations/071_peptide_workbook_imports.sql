-- Preserve each workbook row as an independently traceable discovery dossier seed.
-- This does not create or verify canonical peptide entities, mechanisms or regulatory claims.
CREATE TABLE IF NOT EXISTS peptide_workbook_import_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL,
    source_sha256 CHAR(64) NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    uploaded_filename TEXT NOT NULL,
    uploaded_by UUID REFERENCES user_profiles(id),
    organization_id UUID REFERENCES organizations(id),
    imported_row_count INTEGER NOT NULL DEFAULT 0 CHECK (imported_row_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_sha256, organization_id)
);

CREATE TABLE IF NOT EXISTS peptide_workbook_import_rows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES peptide_workbook_import_batches(id) ON DELETE RESTRICT,
    worksheet_name TEXT NOT NULL,
    worksheet_row_number INTEGER NOT NULL CHECK (worksheet_row_number >= 2),
    candidate_id UUID NOT NULL REFERENCES peptide_discovery_candidates(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    source_row JSONB NOT NULL CHECK (jsonb_typeof(source_row) = 'object'),
    row_sha256 CHAR(64) NOT NULL CHECK (row_sha256 ~ '^[0-9a-f]{64}$'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (batch_id, worksheet_name, worksheet_row_number),
    UNIQUE (candidate_id, batch_id)
);
CREATE INDEX IF NOT EXISTS idx_peptide_workbook_rows_candidate
    ON peptide_workbook_import_rows(candidate_id);

COMMENT ON TABLE peptide_workbook_import_batches IS
    'Tracks idempotent user workbook imports. Workbook content is a source observation, not a verified scientific or regulatory conclusion.';
COMMENT ON TABLE peptide_workbook_import_rows IS
    'Preserves each workbook row verbatim and links it to one independently navigable discovery candidate.';


-- Workbook imports belong to the uploading organization. Existing externally
-- sourced discovery candidates/observations remain shared; private workbook rows
-- are visible only within their owning organization.
ALTER TABLE peptide_discovery_candidates
    ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;
ALTER TABLE peptide_discovery_observations
    ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_peptide_discovery_candidates_owner
    ON peptide_discovery_candidates(owner_organization_id, candidate_status)
    WHERE owner_organization_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_peptide_discovery_observations_owner
    ON peptide_discovery_observations(owner_organization_id, candidate_id)
    WHERE owner_organization_id IS NOT NULL;

ALTER TABLE peptide_workbook_import_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_workbook_import_rows FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_workbook_import_rows_select_scope ON peptide_workbook_import_rows FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY peptide_workbook_import_rows_insert_scope ON peptide_workbook_import_rows FOR INSERT
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);

ALTER TABLE peptide_discovery_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_discovery_candidates FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_discovery_candidates_select_scope ON peptide_discovery_candidates FOR SELECT
    USING (
        owner_organization_id IS NULL
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY peptide_discovery_candidates_insert_scope ON peptide_discovery_candidates FOR INSERT
    WITH CHECK (
        owner_organization_id IS NULL
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY peptide_discovery_candidates_update_scope ON peptide_discovery_candidates FOR UPDATE
    USING (
        owner_organization_id IS NULL
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
    WITH CHECK (
        owner_organization_id IS NULL
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

ALTER TABLE peptide_discovery_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_discovery_observations FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_discovery_observations_select_scope ON peptide_discovery_observations FOR SELECT
    USING (
        owner_organization_id IS NULL
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
CREATE POLICY peptide_discovery_observations_insert_scope ON peptide_discovery_observations FOR INSERT
    WITH CHECK (
        owner_organization_id IS NULL
        OR owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

ALTER TABLE peptide_workbook_import_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_workbook_import_batches FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_workbook_import_batches_select_scope ON peptide_workbook_import_batches FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY peptide_workbook_import_batches_insert_scope ON peptide_workbook_import_batches FOR INSERT
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY peptide_workbook_import_batches_update_scope ON peptide_workbook_import_batches FOR UPDATE
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
