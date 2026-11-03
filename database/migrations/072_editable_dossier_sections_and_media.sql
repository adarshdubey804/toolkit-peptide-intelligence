-- Organization-scoped editable scientific dossier sections with traceable citations and media.
CREATE TABLE IF NOT EXISTS peptide_dossier_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES peptide_discovery_candidates(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    section_key TEXT NOT NULL CHECK (section_key ~ '^[a-z0-9][a-z0-9_-]{1,79}$'),
    content JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(content) = 'object'),
    citations JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(references) = 'array'),
    media JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(media) = 'array'),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision > 0),
    updated_by UUID NOT NULL REFERENCES user_profiles(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (candidate_id, organization_id, section_key)
);
CREATE INDEX IF NOT EXISTS idx_peptide_dossier_sections_owner
    ON peptide_dossier_sections(candidate_id, organization_id, section_key);

CREATE TABLE IF NOT EXISTS peptide_dossier_section_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID NOT NULL REFERENCES peptide_dossier_sections(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    revision INTEGER NOT NULL CHECK (revision > 0),
    snapshot JSONB NOT NULL CHECK (jsonb_typeof(snapshot) = 'object'),
    content_hash CHAR(64) NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    changed_by UUID NOT NULL REFERENCES user_profiles(id) ON DELETE RESTRICT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (section_id, revision)
);
CREATE INDEX IF NOT EXISTS idx_peptide_dossier_section_revisions_latest
    ON peptide_dossier_section_revisions(section_id, revision DESC);

CREATE OR REPLACE FUNCTION capture_peptide_dossier_section_revision()
RETURNS trigger AS $dossier_section_revision$
DECLARE
    next_revision INTEGER;
    snapshot_value JSONB;
BEGIN
    IF TG_OP = 'INSERT' THEN
        next_revision := 1;
    ELSE
        next_revision := OLD.revision + 1;
        NEW.revision := next_revision;
        NEW.updated_at := now();
    END IF;
    snapshot_value := jsonb_build_object(
        'section_key', NEW.section_key,
        'content', NEW.content,
        'references', NEW.citations,
        'media', NEW.media
    );
    INSERT INTO peptide_dossier_section_revisions (
        section_id, organization_id, revision, snapshot, content_hash, changed_by
    ) VALUES (
        NEW.id, NEW.organization_id, next_revision, snapshot_value,
        encode(digest(convert_to(snapshot_value::text, 'UTF8'), 'sha256'), 'hex'),
        NEW.updated_by
    );
    RETURN NEW;
END;
$dossier_section_revision$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_dossier_section_revision_capture ON peptide_dossier_sections;
CREATE TRIGGER peptide_dossier_section_revision_capture
    BEFORE INSERT OR UPDATE ON peptide_dossier_sections
    FOR EACH ROW EXECUTE FUNCTION capture_peptide_dossier_section_revision();

CREATE OR REPLACE FUNCTION prevent_peptide_dossier_section_revision_mutation()
RETURNS trigger AS $dossier_section_revision_immutable$
BEGIN
    RAISE EXCEPTION 'Dossier section revisions are immutable';
END;
$dossier_section_revision_immutable$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_dossier_section_revisions_append_only ON peptide_dossier_section_revisions;
CREATE TRIGGER peptide_dossier_section_revisions_append_only
    BEFORE UPDATE OR DELETE ON peptide_dossier_section_revisions
    FOR EACH ROW EXECUTE FUNCTION prevent_peptide_dossier_section_revision_mutation();

ALTER TABLE peptide_dossier_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_dossier_sections FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_dossier_sections_select_scope ON peptide_dossier_sections FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY peptide_dossier_sections_insert_scope ON peptide_dossier_sections FOR INSERT
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
                AND updated_by = NULLIF(current_setting('app.user_id', true), '')::uuid);
CREATE POLICY peptide_dossier_sections_update_scope ON peptide_dossier_sections FOR UPDATE
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
                AND updated_by = NULLIF(current_setting('app.user_id', true), '')::uuid);

ALTER TABLE peptide_dossier_section_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE peptide_dossier_section_revisions FORCE ROW LEVEL SECURITY;
CREATE POLICY peptide_dossier_section_revisions_select_scope ON peptide_dossier_section_revisions FOR SELECT
    USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid);
CREATE POLICY peptide_dossier_section_revisions_insert_scope ON peptide_dossier_section_revisions FOR INSERT
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
                AND changed_by = NULLIF(current_setting('app.user_id', true), '')::uuid);

COMMENT ON TABLE peptide_dossier_sections IS
    'Organization-scoped editable dossier sections. References and media are stored with each section and every save creates an immutable revision.';
COMMENT ON COLUMN peptide_dossier_sections.citations IS
    'Claim-supporting references with DOI/PMID/registry identifiers, exact URLs and source locators.';
COMMENT ON COLUMN peptide_dossier_sections.media IS
    'Source-attributed images/structures with alt text, caption, attribution and reuse/licence metadata.';
