-- Add stable, source-version-aware locators to claim/source relationships.
-- The locator is metadata about where evidence was found, not a scientific verdict.

CREATE TABLE IF NOT EXISTS claim_source_locators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_source_id UUID NOT NULL REFERENCES claim_sources(id) ON DELETE RESTRICT,
    source_record_version_id UUID REFERENCES source_record_versions(id) ON DELETE RESTRICT,
    locator_type TEXT NOT NULL CHECK (
        locator_type IN ('page','figure','table','section','supplementary_file',
                         'accession','url_fragment','timestamp','other')
    ),
    locator_value TEXT NOT NULL CHECK (length(btrim(locator_value)) > 0),
    quoted_text_hash CHAR(64) CHECK (
        quoted_text_hash IS NULL OR quoted_text_hash ~ '^[0-9a-f]{64}$'
    ),
    locator_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_claim_source_locators_claim_source
    ON claim_source_locators(claim_source_id, locator_type);
CREATE INDEX IF NOT EXISTS idx_claim_source_locators_source_version
    ON claim_source_locators(source_record_version_id)
    WHERE source_record_version_id IS NOT NULL;

CREATE OR REPLACE FUNCTION enforce_claim_source_locator_version()
RETURNS trigger AS $$
DECLARE
    linked_source_id UUID;
    version_source_id UUID;
BEGIN
    IF NEW.source_record_version_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT source_record_id INTO linked_source_id
    FROM claim_sources
    WHERE id = NEW.claim_source_id;

    IF linked_source_id IS NULL THEN
        RAISE EXCEPTION 'A source-record version locator requires a claim source linked to a source record';
    END IF;

    SELECT source_record_id INTO version_source_id
    FROM source_record_versions
    WHERE id = NEW.source_record_version_id;

    IF version_source_id IS DISTINCT FROM linked_source_id THEN
        RAISE EXCEPTION 'Claim source locator version must belong to the linked source record';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS claim_source_locator_version_guard ON claim_source_locators;
CREATE TRIGGER claim_source_locator_version_guard
    BEFORE INSERT ON claim_source_locators
    FOR EACH ROW EXECUTE FUNCTION enforce_claim_source_locator_version();

CREATE OR REPLACE FUNCTION prevent_claim_source_locator_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Claim source locators are append-only; create a corrective locator instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS claim_source_locators_append_only ON claim_source_locators;
CREATE TRIGGER claim_source_locators_append_only
    BEFORE UPDATE OR DELETE ON claim_source_locators
    FOR EACH ROW EXECUTE FUNCTION prevent_claim_source_locator_mutation();

COMMENT ON TABLE claim_source_locators IS
    'Append-only citation locators bound to a claim-source link and, when applicable, the exact captured source-record version. Does not itself establish evidence quality.';
COMMENT ON COLUMN claim_source_locators.quoted_text_hash IS
    'Optional SHA-256 hash of a permitted quoted span; store no restricted full text here.';
