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
