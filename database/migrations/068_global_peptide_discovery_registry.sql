-- Global, source-backed discovery queue for peptide entities that are not yet
-- canonicalized or curator-verified. These records are observations, not peptide facts.
CREATE TABLE IF NOT EXISTS peptide_discovery_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_record_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    source_entity_identifier TEXT NOT NULL,
    source_entity_url TEXT,
    candidate_name TEXT NOT NULL CHECK (length(trim(candidate_name)) >= 2),
    candidate_kind TEXT NOT NULL DEFAULT 'unknown' CHECK (
        candidate_kind IN (
            'therapeutic_peptide', 'endogenous_peptide', 'peptide_conjugate',
            'peptide_fragment', 'peptide_hormone', 'research_peptide',
            'peptide_antibiotic', 'peptide_toxin', 'other', 'unknown'
        )
    ),
    source_development_status TEXT,
    source_jurisdiction_code TEXT,
    reported_sequence TEXT,
    reported_sequence_type TEXT,
    reported_chemical_form TEXT,
    reported_target TEXT,
    reported_mechanism TEXT,
    canonical_peptide_id UUID REFERENCES peptides(id) ON DELETE RESTRICT,
    identity_match_status TEXT NOT NULL DEFAULT 'unresolved' CHECK (
        identity_match_status IN ('unresolved','possible_match','matched','new_entity','ambiguous','rejected')
    ),
    match_confidence NUMERIC(4,3) CHECK (
        match_confidence IS NULL OR match_confidence BETWEEN 0 AND 1
    ),
    match_rationale TEXT,
    candidate_status TEXT NOT NULL DEFAULT 'discovered' CHECK (
        candidate_status IN ('discovered','needs_review','accepted','rejected','duplicate','superseded')
    ),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw_metadata JSONB NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(raw_metadata) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_record_id, source_entity_identifier),
    CHECK (
        canonical_peptide_id IS NULL OR identity_match_status = 'matched'
    ),
    CHECK (
        identity_match_status <> 'matched' OR canonical_peptide_id IS NOT NULL
    ),
    CHECK (
        candidate_status <> 'accepted' OR identity_match_status IN ('matched','new_entity')
    )
);

CREATE INDEX IF NOT EXISTS idx_peptide_discovery_candidates_status
    ON peptide_discovery_candidates(candidate_status, last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_peptide_discovery_candidates_name
    ON peptide_discovery_candidates USING gin(to_tsvector('english', candidate_name));
CREATE INDEX IF NOT EXISTS idx_peptide_discovery_candidates_kind
    ON peptide_discovery_candidates(candidate_kind, source_development_status);
CREATE INDEX IF NOT EXISTS idx_peptide_discovery_candidates_canonical
    ON peptide_discovery_candidates(canonical_peptide_id)
    WHERE canonical_peptide_id IS NOT NULL;

-- Every source refresh is retained as a content-addressed observation. A changed
-- source payload never overwrites the earlier observation.
CREATE TABLE IF NOT EXISTS peptide_discovery_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES peptide_discovery_candidates(id) ON DELETE RESTRICT,
    source_record_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    source_version TEXT,
    payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    payload_hash CHAR(64) NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (candidate_id, payload_hash),
    CHECK (candidate_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_peptide_discovery_observations_latest
    ON peptide_discovery_observations(candidate_id, observed_at DESC);

CREATE OR REPLACE FUNCTION prevent_peptide_discovery_observation_mutation()
RETURNS trigger AS $discovery_observation_immutable$
BEGIN
    RAISE EXCEPTION 'Peptide discovery observations are immutable; append a new source observation';
END;
$discovery_observation_immutable$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_discovery_observations_append_only
    ON peptide_discovery_observations;
CREATE TRIGGER peptide_discovery_observations_append_only
    BEFORE UPDATE OR DELETE ON peptide_discovery_observations
    FOR EACH ROW EXECUTE FUNCTION prevent_peptide_discovery_observation_mutation();

CREATE TABLE IF NOT EXISTS peptide_discovery_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES peptide_discovery_candidates(id) ON DELETE RESTRICT,
    decision TEXT NOT NULL CHECK (
        decision IN ('accepted_as_existing_peptide','accepted_as_new_peptide',
                     'rejected','duplicate','needs_more_evidence')
    ),
    canonical_peptide_id UUID REFERENCES peptides(id) ON DELETE RESTRICT,
    rationale TEXT NOT NULL CHECK (length(trim(rationale)) >= 20),
    evidence_source_record_ids UUID[] NOT NULL DEFAULT '{}',
    reviewer_id UUID REFERENCES user_profiles(id),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
        (decision = 'accepted_as_existing_peptide' AND canonical_peptide_id IS NOT NULL)
        OR (decision <> 'accepted_as_existing_peptide')
    )
);
CREATE INDEX IF NOT EXISTS idx_peptide_discovery_decisions_candidate
    ON peptide_discovery_decisions(candidate_id, decided_at DESC);

CREATE OR REPLACE FUNCTION prevent_peptide_discovery_decision_mutation()
RETURNS trigger AS $discovery_decision_immutable$
BEGIN
    RAISE EXCEPTION 'Peptide discovery decisions are immutable; append a corrective decision';
END;
$discovery_decision_immutable$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS peptide_discovery_decisions_append_only
    ON peptide_discovery_decisions;
CREATE TRIGGER peptide_discovery_decisions_append_only
    BEFORE UPDATE OR DELETE ON peptide_discovery_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_peptide_discovery_decision_mutation();

COMMENT ON TABLE peptide_discovery_candidates IS
    'Global source-backed peptide discovery observations awaiting identity resolution and curation. A candidate is not a verified canonical peptide or a regulatory status determination.';
COMMENT ON COLUMN peptide_discovery_candidates.source_development_status IS
    'Verbatim or normalized status reported by this source only; not a global lifecycle or regulatory conclusion.';
COMMENT ON COLUMN peptide_discovery_candidates.reported_mechanism IS
    'Source-reported mechanism text retained as a discovery hint only. Curated mechanism assertions belong in peptide_mechanisms with their own evidence and review.';
COMMENT ON TABLE peptide_discovery_observations IS
    'Append-only source payload history for peptide discovery candidates.';
COMMENT ON TABLE peptide_discovery_decisions IS
    'Append-only human curation decisions linking discovery observations to canonical peptide dossiers.';
