import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db import engine
from app.main import apply_development_migrations


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
    reason="PostgreSQL claim revision integration test is enabled in CI only.",
)
def test_evidence_claim_revisions_are_immutable_and_decisions_bind_exact_revision():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)
        org = connection.execute(text("""
            INSERT INTO organizations (name, organization_type)
            VALUES (:name, 'research_team') RETURNING id
        """), {"name": "claim-revision-" + str(uuid4())}).scalar_one()
        user = connection.execute(text("""
            INSERT INTO user_profiles (display_name, role)
            VALUES ('Claim revision reviewer', 'researcher') RETURNING id
        """)).scalar_one()
        peptide = connection.execute(text("""
            INSERT INTO peptides (preferred_name, review_status)
            VALUES (:name, 'in_review') RETURNING id
        """), {"name": "Revision fixture " + str(uuid4())}).scalar_one()
        claim = connection.execute(text("""
            INSERT INTO evidence_claims (peptide_id, claim_text, claim_domain)
            VALUES (:peptide, 'Initial supported claim.', 'mechanism') RETURNING id
        """), {"peptide": peptide}).scalar_one()

        revision_one = connection.execute(text("""
            SELECT id, revision_number, content_hash
            FROM evidence_claim_revisions WHERE claim_id=:claim
        """), {"claim": claim}).mappings().one()
        assert revision_one["revision_number"] == 1
        assert len(revision_one["content_hash"].strip()) == 64

        review = connection.execute(text("""
            INSERT INTO curation_reviews (
                entity_type, entity_id, review_status, submitted_by, owner_organization_id
            ) VALUES ('evidence_claim', :claim, 'in_review', :user, :org)
            RETURNING id, evidence_claim_revision_id
        """), {"claim": claim, "user": user, "org": org}).mappings().one()
        assert review["evidence_claim_revision_id"] == revision_one["id"]

        decision_one = connection.execute(text("""
            INSERT INTO curation_decisions (
                review_id, owner_organization_id, decision, rationale,
                reviewer_id, previous_status, new_status
            ) VALUES (
                :review, :org, 'verified', 'Initial revision independently reviewed.',
                :user, 'in_review', 'verified'
            ) RETURNING evidence_claim_revision_id
        """), {"review": review["id"], "org": org, "user": user}).scalar_one()
        assert decision_one == revision_one["id"]

        connection.execute(text("""
            UPDATE evidence_claims SET claim_text='Updated claim with narrower scope.'
            WHERE id=:claim
        """), {"claim": claim})
        revision_two = connection.execute(text("""
            SELECT id, revision_number, content_hash, supersedes_revision_id
            FROM evidence_claim_revisions WHERE claim_id=:claim
            ORDER BY revision_number DESC LIMIT 1
        """), {"claim": claim}).mappings().one()
        assert revision_two["revision_number"] == 2
        assert revision_two["id"] != revision_one["id"]
        assert revision_two["content_hash"] != revision_one["content_hash"]
        assert revision_two["supersedes_revision_id"] == revision_one["id"]

        # Existing review and its decision continue to describe revision one.
        still_reviewed = connection.execute(text("""
            SELECT evidence_claim_revision_id FROM curation_reviews WHERE id=:review
        """), {"review": review["id"]}).scalar_one()
        still_decided = connection.execute(text("""
            SELECT evidence_claim_revision_id FROM curation_decisions
            WHERE review_id=:review
        """), {"review": review["id"]}).scalar_one()
        assert still_reviewed == revision_one["id"]
        assert still_decided == revision_one["id"]

        connection.execute(text("""
            UPDATE curation_reviews SET review_status='verified' WHERE id=:review
        """), {"review": review["id"]})
        resubmitted = connection.execute(text("""
            UPDATE curation_reviews SET review_status='in_review'
            WHERE id=:review RETURNING evidence_claim_revision_id
        """), {"review": review["id"]}).scalar_one()
        assert resubmitted == revision_two["id"]

        decision_two = connection.execute(text("""
            INSERT INTO curation_decisions (
                review_id, owner_organization_id, decision, rationale,
                reviewer_id, previous_status, new_status
            ) VALUES (
                :review, :org, 'verified', 'Updated revision independently reviewed.',
                :user, 'in_review', 'verified'
            ) RETURNING evidence_claim_revision_id
        """), {"review": review["id"], "org": org, "user": user}).scalar_one()
        assert decision_two == revision_two["id"]

        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("""
                    UPDATE evidence_claim_revisions SET claim_text='Mutated history'
                    WHERE id=:revision
                """), {"revision": revision_one["id"]})
        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("""
                    DELETE FROM evidence_claim_revisions WHERE id=:revision
                """), {"revision": revision_one["id"]})

        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("""
                    INSERT INTO curation_decisions (
                        review_id, owner_organization_id, evidence_claim_revision_id,
                        decision, rationale, reviewer_id, previous_status, new_status
                    ) VALUES (
                        :review, :org, :wrong_revision, 'verified',
                        'A decision must not be attached to a different claim revision.',
                        :user, 'in_review', 'verified'
                    )
                """), {
                    "review": review["id"], "org": org,
                    "wrong_revision": revision_one["id"], "user": user,
                })
