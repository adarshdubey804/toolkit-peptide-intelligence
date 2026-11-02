-- Immutable, versioned snapshots for scientific evidence claims.
-- Curation decisions are bound to the exact claim revision that was reviewed.

CREATE TABLE IF NOT EXISTS evidence_claim_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES evidence_claims(id) ON DELETE RESTRICT,
    revision_number INTEGER NOT NULL CHECK (revision_number > 0),
    claim_text TEXT NOT NULL,
    claim_domain TEXT NOT NULL,
    evidence_type evidence_type NOT NULL,
    confidence_label TEXT NOT NULL,
    limitations TEXT,
    content_hash CHAR(64) NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    revision_origin TEXT NOT NULL CHECK (
        revision_origin IN ('legacy_snapshot', 'claim_created', 'claim_content_updated')
    ),
    supersedes_revision_id UUID REFERENCES evidence_claim_revisions(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (claim_id, revision_number)
);

CREATE INDEX IF NOT EXISTS idx_evidence_claim_revisions_latest
    ON evidence_claim_revisions(claim_id, revision_number DESC);

-- Capture a reproducible baseline for every existing claim before enabling triggers.
INSERT INTO evidence_claim_revisions (
    claim_id, revision_number, claim_text, claim_domain, evidence_type,
    confidence_label, limitations, content_hash, revision_origin
)
SELECT
    claim.id, 1, claim.claim_text, claim.claim_domain, claim.evidence_type,
    claim.confidence_label, claim.limitations,
    encode(digest(convert_to(jsonb_build_object(
        'claim_text', claim.claim_text,
        'claim_domain', claim.claim_domain,
        'evidence_type', claim.evidence_type::text,
        'confidence_label', claim.confidence_label,
        'limitations', claim.limitations
    )::text, 'UTF8'), 'sha256'), 'hex'),
    'legacy_snapshot'
FROM evidence_claims claim
ON CONFLICT (claim_id, revision_number) DO NOTHING;

ALTER TABLE curation_reviews
    ADD COLUMN IF NOT EXISTS evidence_claim_revision_id UUID
    REFERENCES evidence_claim_revisions(id) ON DELETE RESTRICT;
ALTER TABLE curation_decisions
    ADD COLUMN IF NOT EXISTS evidence_claim_revision_id UUID
    REFERENCES evidence_claim_revisions(id) ON DELETE RESTRICT;

-- Preserve historical decisions by binding them to the revision their review
-- represented when this migration was applied.
UPDATE curation_reviews review
SET evidence_claim_revision_id = revision.id
FROM evidence_claim_revisions revision
WHERE review.entity_type = 'evidence_claim'
  AND revision.claim_id = review.entity_id
  AND revision.revision_number = 1
  AND review.evidence_claim_revision_id IS NULL;

-- The earlier curation migration installed two equivalent append-only triggers.
-- Temporarily remove both so this one-time historical backfill can run.
DROP TRIGGER IF EXISTS trg_curation_decisions_no_update ON curation_decisions;
DROP TRIGGER IF EXISTS curation_decisions_append_only ON curation_decisions;

UPDATE curation_decisions decision
SET evidence_claim_revision_id = review.evidence_claim_revision_id
FROM curation_reviews review
WHERE decision.review_id = review.id
  AND review.entity_type = 'evidence_claim'
  AND decision.evidence_claim_revision_id IS NULL;

CREATE OR REPLACE FUNCTION prevent_evidence_claim_revision_mutation()
RETURNS trigger AS $claim_revision_immutable$
BEGIN
    RAISE EXCEPTION 'Evidence claim revisions are immutable; update the claim to create a new revision';
END;
$claim_revision_immutable$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS evidence_claim_revisions_append_only ON evidence_claim_revisions;
CREATE TRIGGER evidence_claim_revisions_append_only
    BEFORE UPDATE OR DELETE ON evidence_claim_revisions
    FOR EACH ROW EXECUTE FUNCTION prevent_evidence_claim_revision_mutation();

CREATE OR REPLACE FUNCTION capture_evidence_claim_revision()
RETURNS trigger AS $claim_revision_capture$
DECLARE
    prior_revision_id UUID;
    next_revision_number INTEGER;
    snapshot JSONB;
BEGIN
    IF TG_OP = 'UPDATE' AND
       ROW(NEW.claim_text, NEW.claim_domain, NEW.evidence_type, NEW.confidence_label, NEW.limitations)
       IS NOT DISTINCT FROM
       ROW(OLD.claim_text, OLD.claim_domain, OLD.evidence_type, OLD.confidence_label, OLD.limitations)
    THEN
        RETURN NEW;
    END IF;

    SELECT id, revision_number
    INTO prior_revision_id, next_revision_number
    FROM evidence_claim_revisions
    WHERE claim_id = NEW.id
    ORDER BY revision_number DESC
    LIMIT 1;

    IF prior_revision_id IS NULL THEN
        next_revision_number := 1;
    ELSE
        next_revision_number := next_revision_number + 1;
    END IF;

    snapshot := jsonb_build_object(
        'claim_text', NEW.claim_text,
        'claim_domain', NEW.claim_domain,
        'evidence_type', NEW.evidence_type::text,
        'confidence_label', NEW.confidence_label,
        'limitations', NEW.limitations
    );

    INSERT INTO evidence_claim_revisions (
        claim_id, revision_number, claim_text, claim_domain, evidence_type,
        confidence_label, limitations, content_hash, revision_origin,
        supersedes_revision_id
    ) VALUES (
        NEW.id, next_revision_number, NEW.claim_text, NEW.claim_domain, NEW.evidence_type,
        NEW.confidence_label, NEW.limitations,
        encode(digest(convert_to(snapshot::text, 'UTF8'), 'sha256'), 'hex'),
        CASE WHEN TG_OP = 'INSERT' THEN 'claim_created' ELSE 'claim_content_updated' END,
        prior_revision_id
    );

    RETURN NEW;
END;
$claim_revision_capture$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS evidence_claim_revision_capture ON evidence_claims;
CREATE TRIGGER evidence_claim_revision_capture
    AFTER INSERT OR UPDATE OF claim_text, claim_domain, evidence_type, confidence_label, limitations
    ON evidence_claims
    FOR EACH ROW EXECUTE FUNCTION capture_evidence_claim_revision();

CREATE OR REPLACE FUNCTION bind_curation_review_to_claim_revision()
RETURNS trigger AS $review_revision_binding$
DECLARE
    revision_claim_id UUID;
    should_refresh BOOLEAN := FALSE;
BEGIN
    IF NEW.entity_type <> 'evidence_claim' THEN
        IF NEW.evidence_claim_revision_id IS NOT NULL THEN
            RAISE EXCEPTION 'Only evidence-claim reviews may reference an evidence claim revision';
        END IF;
        RETURN NEW;
    END IF;

    IF TG_OP = 'INSERT' THEN
        should_refresh := TRUE;
    ELSIF NEW.review_status = 'in_review' AND OLD.review_status IS DISTINCT FROM 'in_review' THEN
        should_refresh := TRUE;
    END IF;

    IF should_refresh OR NEW.evidence_claim_revision_id IS NULL THEN
        SELECT id INTO NEW.evidence_claim_revision_id
        FROM evidence_claim_revisions
        WHERE claim_id = NEW.entity_id
        ORDER BY revision_number DESC
        LIMIT 1;
    END IF;

    IF NEW.evidence_claim_revision_id IS NULL THEN
        RAISE EXCEPTION 'Evidence-claim review requires an existing claim revision';
    END IF;

    SELECT claim_id INTO revision_claim_id
    FROM evidence_claim_revisions
    WHERE id = NEW.evidence_claim_revision_id;

    IF revision_claim_id IS DISTINCT FROM NEW.entity_id THEN
        RAISE EXCEPTION 'Curation review revision must belong to the reviewed evidence claim';
    END IF;

    RETURN NEW;
END;
$review_revision_binding$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS curation_review_claim_revision_guard ON curation_reviews;
CREATE TRIGGER curation_review_claim_revision_guard
    BEFORE INSERT OR UPDATE OF entity_type, entity_id, review_status, evidence_claim_revision_id
    ON curation_reviews
    FOR EACH ROW EXECUTE FUNCTION bind_curation_review_to_claim_revision();

CREATE OR REPLACE FUNCTION bind_curation_decision_to_claim_revision()
RETURNS trigger AS $decision_revision_binding$
DECLARE
    parent_review curation_reviews%ROWTYPE;
BEGIN
    SELECT * INTO parent_review
    FROM curation_reviews
    WHERE id = NEW.review_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Curation decision requires an existing review';
    END IF;

    IF parent_review.owner_organization_id IS DISTINCT FROM NEW.owner_organization_id THEN
        RAISE EXCEPTION 'Curation decision organization must match its review owner';
    END IF;

    IF parent_review.entity_type = 'evidence_claim' THEN
        IF NEW.evidence_claim_revision_id IS NULL THEN
            NEW.evidence_claim_revision_id := parent_review.evidence_claim_revision_id;
        END IF;
        IF NEW.evidence_claim_revision_id IS DISTINCT FROM parent_review.evidence_claim_revision_id THEN
            RAISE EXCEPTION 'Curation decision must reference the exact evidence claim revision under review';
        END IF;
    ELSIF NEW.evidence_claim_revision_id IS NOT NULL THEN
        RAISE EXCEPTION 'Only evidence-claim decisions may reference an evidence claim revision';
    END IF;

    RETURN NEW;
END;
$decision_revision_binding$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS curation_decision_claim_revision_guard ON curation_decisions;
CREATE TRIGGER curation_decision_claim_revision_guard
    BEFORE INSERT ON curation_decisions
    FOR EACH ROW EXECUTE FUNCTION bind_curation_decision_to_claim_revision();

CREATE TRIGGER curation_decisions_append_only
    BEFORE UPDATE OR DELETE ON curation_decisions
    FOR EACH ROW EXECUTE FUNCTION prevent_curation_decision_mutation();

COMMENT ON TABLE evidence_claim_revisions IS
    'Immutable, content-hashed snapshots of evidence claims. Changes to scientific claim content create a new revision; prior review decisions remain attached to the exact revision assessed.';
COMMENT ON COLUMN curation_reviews.evidence_claim_revision_id IS
    'Exact evidence claim revision currently submitted for this review. Resubmission to in_review binds to the latest revision.';
COMMENT ON COLUMN curation_decisions.evidence_claim_revision_id IS
    'Immutable evidence claim revision evaluated by this decision; populated from the parent review when omitted.';
