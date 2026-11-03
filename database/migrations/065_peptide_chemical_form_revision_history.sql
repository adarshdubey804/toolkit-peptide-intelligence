-- Immutable, content-addressed snapshots for peptide chemical forms.
-- A review or applicability decision can now be tied to the exact chemistry
-- that existed at the time; changing a form never rewrites its prior revision.

CREATE TABLE IF NOT EXISTS peptide_chemical_form_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chemical_form_id UUID NOT NULL
        REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT,
    revision_number INTEGER NOT NULL CHECK (revision_number > 0),
    snapshot JSONB NOT NULL CHECK (jsonb_typeof(snapshot) = 'object'),
    content_hash CHAR(64) NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    revision_origin TEXT NOT NULL CHECK (
        revision_origin IN ('legacy_snapshot', 'chemical_form_created', 'chemical_form_updated')
    ),
    supersedes_revision_id UUID
        REFERENCES peptide_chemical_form_revisions(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (chemical_form_id, revision_number),
    CHECK (supersedes_revision_id IS NULL OR supersedes_revision_id <> id)
);

CREATE INDEX IF NOT EXISTS idx_peptide_chemical_form_revisions_latest
    ON peptide_chemical_form_revisions(chemical_form_id, revision_number DESC);

-- Establish a baseline before installing the capture trigger. Exclude only
-- database identity/timestamps; all scientific, provenance and review fields
-- are retained in the immutable snapshot.
INSERT INTO peptide_chemical_form_revisions (
    chemical_form_id, revision_number, snapshot, content_hash, revision_origin
)
SELECT
    form.id,
    1,
    to_jsonb(form) - 'id' - 'created_at' - 'updated_at',
    encode(digest(convert_to(
        (to_jsonb(form) - 'id' - 'created_at' - 'updated_at')::text, 'UTF8'
    ), 'sha256'), 'hex'),
    'legacy_snapshot'
FROM peptide_chemical_forms AS form
ON CONFLICT (chemical_form_id, revision_number) DO NOTHING;

CREATE OR REPLACE FUNCTION prevent_peptide_chemical_form_revision_mutation()
RETURNS trigger AS $form_revision_immutable$
BEGIN
    RAISE EXCEPTION
        'Peptide chemical-form revisions are immutable; update the form to create a new revision';
END;
$form_revision_immutable$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_chemical_form_revisions_append_only
    ON peptide_chemical_form_revisions;
CREATE TRIGGER peptide_chemical_form_revisions_append_only
    BEFORE UPDATE OR DELETE ON peptide_chemical_form_revisions
    FOR EACH ROW EXECUTE FUNCTION prevent_peptide_chemical_form_revision_mutation();

CREATE OR REPLACE FUNCTION capture_peptide_chemical_form_revision()
RETURNS trigger AS $form_revision_capture$
DECLARE
    previous_revision_id UUID;
    previous_revision_number INTEGER;
    form_snapshot JSONB;
    latest_snapshot JSONB;
BEGIN
    form_snapshot := to_jsonb(NEW) - 'id' - 'created_at' - 'updated_at';

    -- Avoid creating a new scientific revision for timestamp-only or
    -- otherwise content-neutral updates.
    -- The parent row is locked by the INSERT/UPDATE that invoked this AFTER
    -- trigger, serializing revision-number allocation for this form.
    SELECT id, revision_number, snapshot
      INTO previous_revision_id, previous_revision_number, latest_snapshot
      FROM peptide_chemical_form_revisions
     WHERE chemical_form_id = NEW.id
     ORDER BY revision_number DESC
     LIMIT 1;

    -- Compare only with the immediately preceding revision. Reverting to an
    -- older snapshot is still a material change and must create a new revision.
    IF TG_OP = 'UPDATE' AND latest_snapshot = form_snapshot THEN
        RETURN NEW;
    END IF;

    INSERT INTO peptide_chemical_form_revisions (
        chemical_form_id, revision_number, snapshot, content_hash,
        revision_origin, supersedes_revision_id
    ) VALUES (
        NEW.id,
        COALESCE(previous_revision_number, 0) + 1,
        form_snapshot,
        encode(digest(convert_to(form_snapshot::text, 'UTF8'), 'sha256'), 'hex'),
        CASE WHEN TG_OP = 'INSERT'
             THEN 'chemical_form_created'
             ELSE 'chemical_form_updated'
        END,
        previous_revision_id
    );

    RETURN NEW;
END;
$form_revision_capture$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_chemical_form_revision_capture
    ON peptide_chemical_forms;
CREATE TRIGGER peptide_chemical_form_revision_capture
    AFTER INSERT OR UPDATE ON peptide_chemical_forms
    FOR EACH ROW EXECUTE FUNCTION capture_peptide_chemical_form_revision();

COMMENT ON TABLE peptide_chemical_form_revisions IS
    'Append-only, content-addressed snapshots of peptide chemical-form records. Revisions preserve scientific and provenance fields and do not assert chemical equivalence.';
COMMENT ON COLUMN peptide_chemical_form_revisions.content_hash IS
    'SHA-256 of the canonical PostgreSQL JSONB text representation of snapshot; a change detector, not a digital signature.';
COMMENT ON COLUMN peptide_chemical_form_revisions.revision_origin IS
    'legacy_snapshot captures pre-existing rows; created/updated values are generated by the form revision trigger.';
