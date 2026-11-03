-- Evidence-graded mechanism-of-action records for each peptide and chemical form.
-- Mechanistic hypotheses remain distinct from clinically demonstrated effects.
CREATE TABLE IF NOT EXISTS peptide_mechanisms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peptide_id UUID NOT NULL REFERENCES peptides(id) ON DELETE RESTRICT,
    chemical_form_id UUID REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT,
    mechanism_title TEXT NOT NULL CHECK (length(trim(mechanism_title)) >= 5),
    mechanism_statement TEXT NOT NULL CHECK (length(trim(mechanism_statement)) >= 20),
    mechanism_class TEXT NOT NULL CHECK (
        mechanism_class IN (
            'receptor_agonism', 'receptor_antagonism', 'partial_agonism',
            'inverse_agonism', 'enzyme_inhibition', 'enzyme_activation',
            'ligand_binding', 'ion_channel_modulation', 'transporter_modulation',
            'immunomodulation', 'membrane_interaction', 'gene_expression_modulation',
            'multitarget', 'other', 'unknown'
        )
    ),
    target_id UUID REFERENCES targets(id) ON DELETE RESTRICT,
    target_name TEXT,
    target_identifier TEXT,
    target_action TEXT,
    binding_or_interaction TEXT,
    downstream_signaling TEXT,
    pathway_context TEXT,
    biological_effect TEXT,
    tissue_or_cell_context TEXT,
    species_or_population TEXT,
    evidence_level TEXT NOT NULL CHECK (
        evidence_level IN (
            'regulatory_label', 'human_mechanistic', 'human_clinical',
            'in_vivo_animal', 'in_vitro', 'ex_vivo',
            'computational', 'source_asserted', 'ai_extracted', 'curator_interpreted',
            'unknown'
        )
    ),
    evidence_type evidence_type NOT NULL DEFAULT 'unknown',
    confidence_score NUMERIC(4,3) CHECK (
        confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1
    ),
    limitations TEXT,
    source_record_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    source_locator TEXT,
    source_excerpt TEXT,
    model_or_method TEXT,
    review_status review_status NOT NULL DEFAULT 'draft',
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT peptide_mechanisms_form_parent_check
        CHECK (chemical_form_id IS NULL OR peptide_id IS NOT NULL),
    CONSTRAINT peptide_mechanisms_verified_review_check
        CHECK (review_status <> 'verified' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)),
    CONSTRAINT peptide_mechanisms_target_check
        CHECK (target_id IS NOT NULL OR (target_name IS NOT NULL AND length(trim(target_name)) > 0))
);

CREATE INDEX IF NOT EXISTS idx_peptide_mechanisms_peptide_review
    ON peptide_mechanisms(peptide_id, review_status, evidence_level);
CREATE INDEX IF NOT EXISTS idx_peptide_mechanisms_form_review
    ON peptide_mechanisms(chemical_form_id, review_status)
    WHERE chemical_form_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_peptide_mechanisms_target
    ON peptide_mechanisms(target_id) WHERE target_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_peptide_mechanisms_source
    ON peptide_mechanisms(source_record_id);

CREATE OR REPLACE FUNCTION enforce_peptide_mechanism_form_parent()
RETURNS trigger AS $mechanism_form_parent$
BEGIN
    IF NEW.chemical_form_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM peptide_chemical_forms form
        WHERE form.id = NEW.chemical_form_id AND form.peptide_id = NEW.peptide_id
    ) THEN
        RAISE EXCEPTION 'Mechanism chemical form must belong to the same peptide';
    END IF;
    RETURN NEW;
END;
$mechanism_form_parent$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_mechanisms_form_parent
    ON peptide_mechanisms;
CREATE TRIGGER peptide_mechanisms_form_parent
    BEFORE INSERT OR UPDATE OF peptide_id, chemical_form_id ON peptide_mechanisms
    FOR EACH ROW EXECUTE FUNCTION enforce_peptide_mechanism_form_parent();

-- Append-only, content-addressed revision history for mechanistic assertions.
CREATE TABLE IF NOT EXISTS peptide_mechanism_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mechanism_id UUID NOT NULL REFERENCES peptide_mechanisms(id) ON DELETE RESTRICT,
    revision_number INTEGER NOT NULL CHECK (revision_number > 0),
    snapshot JSONB NOT NULL CHECK (jsonb_typeof(snapshot) = 'object'),
    content_hash CHAR(64) NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    revision_reason TEXT NOT NULL CHECK (revision_reason IN ('record_created','record_updated')),
    supersedes_revision_id UUID REFERENCES peptide_mechanism_revisions(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (mechanism_id, revision_number),
    CHECK (supersedes_revision_id IS NULL OR supersedes_revision_id <> id)
);
CREATE INDEX IF NOT EXISTS idx_peptide_mechanism_revisions_latest
    ON peptide_mechanism_revisions(mechanism_id, revision_number DESC);

CREATE OR REPLACE FUNCTION prevent_peptide_mechanism_revision_mutation()
RETURNS trigger AS $mechanism_revision_immutable$
BEGIN
    RAISE EXCEPTION 'Mechanism revisions are immutable; update the mechanism record to create a new revision';
END;
$mechanism_revision_immutable$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_mechanism_revisions_append_only
    ON peptide_mechanism_revisions;
CREATE TRIGGER peptide_mechanism_revisions_append_only
    BEFORE UPDATE OR DELETE ON peptide_mechanism_revisions
    FOR EACH ROW EXECUTE FUNCTION prevent_peptide_mechanism_revision_mutation();

CREATE OR REPLACE FUNCTION capture_peptide_mechanism_revision()
RETURNS trigger AS $mechanism_revision_capture$
DECLARE
    previous_revision_id UUID;
    previous_revision_number INTEGER;
    record_snapshot JSONB;
    latest_snapshot JSONB;
BEGIN
    record_snapshot := to_jsonb(NEW) - 'id' - 'created_at' - 'updated_at';
    SELECT id, revision_number, snapshot
      INTO previous_revision_id, previous_revision_number, latest_snapshot
      FROM peptide_mechanism_revisions
     WHERE mechanism_id = NEW.id
     ORDER BY revision_number DESC LIMIT 1;

    IF TG_OP = 'UPDATE' AND latest_snapshot = record_snapshot THEN
        RETURN NEW;
    END IF;

    INSERT INTO peptide_mechanism_revisions (
        mechanism_id, revision_number, snapshot, content_hash,
        revision_reason, supersedes_revision_id
    ) VALUES (
        NEW.id, COALESCE(previous_revision_number, 0) + 1, record_snapshot,
        encode(digest(convert_to(record_snapshot::text, 'UTF8'), 'sha256'), 'hex'),
        CASE WHEN TG_OP = 'INSERT' THEN 'record_created' ELSE 'record_updated' END,
        previous_revision_id
    );
    RETURN NEW;
END;
$mechanism_revision_capture$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_mechanism_revision_capture ON peptide_mechanisms;
CREATE TRIGGER peptide_mechanism_revision_capture
    AFTER INSERT OR UPDATE ON peptide_mechanisms
    FOR EACH ROW EXECUTE FUNCTION capture_peptide_mechanism_revision();

COMMENT ON TABLE peptide_mechanisms IS
    'Source-linked mechanism-of-action assertions for peptide identities and optional exact chemical forms. Evidence level is explicit; mechanistic plausibility is not proof of clinical effect.';
COMMENT ON COLUMN peptide_mechanisms.evidence_level IS
    'Regulatory-label, human, animal, in-vitro, computational and extracted/curator-interpreted evidence are intentionally separate.';
COMMENT ON TABLE peptide_mechanism_revisions IS
    'Immutable content-addressed history for mechanistic assertions, preserving changes in evidence and interpretation.';
