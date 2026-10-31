-- Structured evidence appraisal, preserving evidence class separately from methodological quality.
CREATE TABLE IF NOT EXISTS evidence_appraisals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    claim_id UUID NOT NULL REFERENCES evidence_claims(id) ON DELETE CASCADE,
    study_design TEXT NOT NULL CHECK (study_design IN ('systematic_review','meta_analysis','randomized_trial','observational_human','animal','in_vitro','computational','case_report','other','unknown')),
    evidence_level TEXT NOT NULL CHECK (evidence_level IN ('clinical_human','preclinical_animal','in_vitro','computational','secondary_research','unknown')),
    population_or_model TEXT,
    sample_size INTEGER CHECK (sample_size IS NULL OR sample_size >= 0),
    endpoint TEXT,
    risk_of_bias TEXT NOT NULL CHECK (risk_of_bias IN ('low_concern','some_concerns','high_concern','not_assessed')),
    replication_status TEXT NOT NULL CHECK (replication_status IN ('independently_replicated','single_study','not_applicable','unknown')),
    methodological_domains JSONB NOT NULL DEFAULT '{}'::jsonb,
    limitations TEXT NOT NULL,
    appraisal_rationale TEXT NOT NULL,
    appraisal_status TEXT NOT NULL DEFAULT 'in_review' CHECK (appraisal_status IN ('in_review','accepted','rejected','superseded')),
    reviewer_id UUID NOT NULL REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_evidence_appraisals_claim
    ON evidence_appraisals(claim_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_appraisals_org
    ON evidence_appraisals(organization_id, appraisal_status, created_at DESC);
CREATE TABLE IF NOT EXISTS publication_duplicate_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    publication_a UUID NOT NULL REFERENCES publications(id) ON DELETE CASCADE,
    publication_b UUID NOT NULL REFERENCES publications(id) ON DELETE CASCADE,
    match_basis TEXT NOT NULL CHECK (match_basis IN ('doi','pmid','title_year_author','manual')),
    match_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'needs_review' CHECK (status IN ('needs_review','confirmed_duplicate','not_duplicate')),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (publication_a <> publication_b),
    UNIQUE (organization_id, publication_a, publication_b)
);
CREATE INDEX IF NOT EXISTS idx_publication_duplicates_queue
    ON publication_duplicate_candidates(organization_id, status, created_at DESC);
COMMENT ON TABLE evidence_appraisals IS
    'Human-authored structured appraisal. Evidence level is not a quality score and no aggregate grade is inferred.';
COMMENT ON TABLE publication_duplicate_candidates IS
    'Candidate duplicate pairs for human review; matching does not merge or delete publication records.';
