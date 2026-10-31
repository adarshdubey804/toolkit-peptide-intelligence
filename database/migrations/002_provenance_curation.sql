-- Additive, idempotent provenance and editorial curation foundation.
-- External records remain unreviewed until an authorized review workflow is implemented.
ALTER TABLE source_records
    ADD COLUMN IF NOT EXISTS source_version TEXT,
    ADD COLUMN IF NOT EXISTS content_hash CHAR(64),
    ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS record_status TEXT NOT NULL DEFAULT 'active';

CREATE INDEX IF NOT EXISTS idx_source_records_identifier
    ON source_records(source_name, source_identifier);
CREATE INDEX IF NOT EXISTS idx_source_records_hash
    ON source_records(source_name, content_hash)
    WHERE content_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS external_entity_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_record_id UUID NOT NULL REFERENCES source_records(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    relationship TEXT NOT NULL DEFAULT 'same_entity_candidate',
    identity_confidence TEXT NOT NULL DEFAULT 'unassessed',
    match_method TEXT NOT NULL DEFAULT 'manual_or_imported',
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_record_id, entity_type, entity_id, relationship)
);
CREATE INDEX IF NOT EXISTS idx_external_entity_links_entity
    ON external_entity_links(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS curation_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    source_record_id UUID REFERENCES source_records(id),
    review_status review_status NOT NULL DEFAULT 'draft',
    priority TEXT NOT NULL DEFAULT 'normal',
    assigned_to UUID REFERENCES user_profiles(id),
    submitted_by UUID REFERENCES user_profiles(id),
    decision_reason TEXT,
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (review_status IN ('draft','in_review','verified','rejected','archived'))
);
CREATE INDEX IF NOT EXISTS idx_curation_reviews_queue
    ON curation_reviews(review_status, priority, created_at);

CREATE TABLE IF NOT EXISTS curation_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES curation_reviews(id) ON DELETE RESTRICT,
    decision TEXT NOT NULL CHECK (decision IN ('verified','rejected','needs_changes','archived')),
    rationale TEXT NOT NULL,
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    previous_status review_status,
    new_status review_status NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_curation_decisions_review
    ON curation_decisions(review_id, decided_at);

CREATE TABLE IF NOT EXISTS source_record_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_record_id UUID NOT NULL REFERENCES source_records(id) ON DELETE CASCADE,
    content_hash CHAR(64) NOT NULL,
    raw_payload JSONB NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_record_id, content_hash)
);
CREATE INDEX IF NOT EXISTS idx_source_record_versions_captured
    ON source_record_versions(source_record_id, captured_at DESC);

COMMENT ON TABLE external_entity_links IS
    'Candidate cross-database entity mappings. Never treat an unreviewed mapping as identity equivalence.';
COMMENT ON TABLE curation_decisions IS
    'Append-only editorial decision history; corrections should create new decisions rather than overwrite history.';
