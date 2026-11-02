-- Link machine-extracted evidence to durable source records and captured provider snapshots.
-- Normalized provider payloads are explicitly distinguished from original upstream API payloads.

ALTER TABLE source_record_versions
    ADD COLUMN IF NOT EXISTS payload_kind TEXT NOT NULL DEFAULT 'unspecified'
    CHECK (payload_kind IN ('unspecified', 'normalized_provider_record', 'legacy_metadata'));

ALTER TABLE extracted_evidence_records
    ADD COLUMN IF NOT EXISTS source_record_id UUID REFERENCES source_records(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS source_record_version_id UUID REFERENCES source_record_versions(id) ON DELETE RESTRICT;

-- Existing extraction rows have normalized AI output, not the original provider response.
-- Link their stable source identity but do not fabricate a source-version snapshot.
INSERT INTO source_records (
    source_name, source_identifier, source_url, raw_metadata, retrieved_at,
    record_status
)
SELECT DISTINCT
    extracted.source_name,
    extracted.source_identifier,
    extracted.source_url,
    jsonb_build_object(
        'source_title', extracted.source_title,
        'legacy_extraction_source', true
    ),
    extracted.created_at,
    'active'
FROM extracted_evidence_records extracted
ON CONFLICT (source_name, source_identifier) DO NOTHING;

UPDATE extracted_evidence_records extracted
SET source_record_id = source.id
FROM source_records source
WHERE source.source_name = extracted.source_name
  AND source.source_identifier = extracted.source_identifier
  AND extracted.source_record_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_extracted_evidence_source_record
    ON extracted_evidence_records(source_record_id)
    WHERE source_record_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_extracted_evidence_source_version
    ON extracted_evidence_records(source_record_version_id)
    WHERE source_record_version_id IS NOT NULL;

CREATE OR REPLACE FUNCTION enforce_extracted_source_version_match()
RETURNS trigger AS $extracted_source_version_guard$
DECLARE
    version_source_id UUID;
BEGIN
    IF NEW.source_record_version_id IS NULL THEN
        RETURN NEW;
    END IF;
    IF NEW.source_record_id IS NULL THEN
        RAISE EXCEPTION 'An extracted evidence source version requires a source record';
    END IF;

    SELECT source_record_id INTO version_source_id
    FROM source_record_versions
    WHERE id = NEW.source_record_version_id;

    IF version_source_id IS DISTINCT FROM NEW.source_record_id THEN
        RAISE EXCEPTION 'Extracted evidence source version must belong to its linked source record';
    END IF;
    RETURN NEW;
END;
$extracted_source_version_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS extracted_source_version_match_guard ON extracted_evidence_records;
CREATE TRIGGER extracted_source_version_match_guard
    BEFORE INSERT OR UPDATE OF source_record_id, source_record_version_id
    ON extracted_evidence_records
    FOR EACH ROW EXECUTE FUNCTION enforce_extracted_source_version_match();

CREATE OR REPLACE FUNCTION prevent_source_record_version_mutation()
RETURNS trigger AS $source_version_immutable$
BEGIN
    RAISE EXCEPTION 'Source record versions are immutable snapshots; capture a new version instead';
END;
$source_version_immutable$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS source_record_versions_append_only ON source_record_versions;
CREATE TRIGGER source_record_versions_append_only
    BEFORE UPDATE OR DELETE ON source_record_versions
    FOR EACH ROW EXECUTE FUNCTION prevent_source_record_version_mutation();

COMMENT ON COLUMN source_record_versions.payload_kind IS
    'Distinguishes original/unspecified snapshots from normalized provider records and legacy metadata; normalized records must not be represented as raw upstream API payloads.';
COMMENT ON COLUMN extracted_evidence_records.source_record_id IS
    'Canonical source registry identity. Legacy extraction records may be linked without a captured source version.';
COMMENT ON COLUMN extracted_evidence_records.source_record_version_id IS
    'Exact normalized provider-record snapshot used by this extraction; NULL for legacy rows without a recoverable source snapshot.';
