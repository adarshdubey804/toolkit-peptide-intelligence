-- Organization isolation for machine-extracted evidence artifacts.
-- Source records remain shared; extraction runs, extracted rows and reviewer
-- decisions are private to the organization that created them.

ALTER TABLE evidence_extraction_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_extraction_runs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS evidence_extraction_runs_select_scope ON evidence_extraction_runs;
CREATE POLICY evidence_extraction_runs_select_scope ON evidence_extraction_runs
    FOR SELECT USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
DROP POLICY IF EXISTS evidence_extraction_runs_insert_scope ON evidence_extraction_runs;
CREATE POLICY evidence_extraction_runs_insert_scope ON evidence_extraction_runs
    FOR INSERT WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

ALTER TABLE extracted_evidence_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_evidence_records FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS extracted_evidence_records_select_scope ON extracted_evidence_records;
CREATE POLICY extracted_evidence_records_select_scope ON extracted_evidence_records
    FOR SELECT USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
DROP POLICY IF EXISTS extracted_evidence_records_insert_scope ON extracted_evidence_records;
CREATE POLICY extracted_evidence_records_insert_scope ON extracted_evidence_records
    FOR INSERT WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

ALTER TABLE extracted_evidence_field_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_evidence_field_decisions FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS extracted_evidence_field_decisions_select_scope ON extracted_evidence_field_decisions;
CREATE POLICY extracted_evidence_field_decisions_select_scope ON extracted_evidence_field_decisions
    FOR SELECT USING (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );
DROP POLICY IF EXISTS extracted_evidence_field_decisions_insert_scope ON extracted_evidence_field_decisions;
CREATE POLICY extracted_evidence_field_decisions_insert_scope ON extracted_evidence_field_decisions
    FOR INSERT WITH CHECK (
        organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    );

CREATE OR REPLACE FUNCTION enforce_extraction_run_organization()
RETURNS trigger AS $extraction_run_org_guard$
DECLARE
    parent_organization UUID;
BEGIN
    SELECT organization_id INTO parent_organization
    FROM evidence_extraction_runs
    WHERE id = NEW.run_id;

    IF parent_organization IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Extracted evidence record must belong to the organization that owns its run';
    END IF;
    RETURN NEW;
END;
$extraction_run_org_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS extracted_evidence_run_org_guard ON extracted_evidence_records;
CREATE TRIGGER extracted_evidence_run_org_guard
    BEFORE INSERT OR UPDATE OF organization_id, run_id
    ON extracted_evidence_records
    FOR EACH ROW EXECUTE FUNCTION enforce_extraction_run_organization();

CREATE OR REPLACE FUNCTION enforce_extraction_decision_organization()
RETURNS trigger AS $extraction_decision_org_guard$
DECLARE
    record_organization UUID;
BEGIN
    SELECT organization_id INTO record_organization
    FROM extracted_evidence_records
    WHERE id = NEW.record_id;

    IF record_organization IS DISTINCT FROM NEW.organization_id THEN
        RAISE EXCEPTION 'Extraction field decision must belong to the organization that owns its record';
    END IF;
    RETURN NEW;
END;
$extraction_decision_org_guard$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS extracted_evidence_field_decision_org_guard ON extracted_evidence_field_decisions;
CREATE TRIGGER extracted_evidence_field_decision_org_guard
    BEFORE INSERT OR UPDATE OF organization_id, record_id
    ON extracted_evidence_field_decisions
    FOR EACH ROW EXECUTE FUNCTION enforce_extraction_decision_organization();

COMMENT ON POLICY evidence_extraction_runs_select_scope ON evidence_extraction_runs IS
    'Extraction runs are visible only inside their owning organization.';
COMMENT ON POLICY extracted_evidence_records_select_scope ON extracted_evidence_records IS
    'Machine-extracted evidence is visible only inside its owning organization.';
COMMENT ON POLICY extracted_evidence_field_decisions_select_scope ON extracted_evidence_field_decisions IS
    'Field-level review history is visible only inside its owning organization.';
