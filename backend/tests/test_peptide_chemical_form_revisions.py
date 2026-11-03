import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db import engine
from app.main import apply_development_migrations


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
    reason="PostgreSQL migration integration test is enabled in CI only.",
)
def test_peptide_chemical_form_revisions_are_immutable_and_content_sensitive():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            peptide_id = connection.execute(
                text("""
                    INSERT INTO peptides (preferred_name, review_status)
                    VALUES (:name, 'draft')
                    RETURNING id
                """),
                {"name": f"revision-test-{uuid4()}"},
            ).scalar_one()
            form_id = connection.execute(
                text("""
                    INSERT INTO peptide_chemical_forms (
                        peptide_id, form_name, form_type, normalized_sequence
                    ) VALUES (:peptide_id, 'Initial form', 'linear_peptide', 'ACDE')
                    RETURNING id
                """),
                {"peptide_id": peptide_id},
            ).scalar_one()

            revisions = connection.execute(
                text("""
                    SELECT revision_number, revision_origin, snapshot, content_hash,
                           supersedes_revision_id
                    FROM peptide_chemical_form_revisions
                    WHERE chemical_form_id=:form_id
                    ORDER BY revision_number
                """),
                {"form_id": form_id},
            ).mappings().all()
            assert len(revisions) == 1
            assert revisions[0]["revision_number"] == 1
            assert revisions[0]["revision_origin"] == "chemical_form_created"
            assert revisions[0]["snapshot"]["form_name"] == "Initial form"
            assert len(revisions[0]["content_hash"].strip()) == 64
            assert revisions[0]["supersedes_revision_id"] is None

            connection.execute(
                text("""
                    UPDATE peptide_chemical_forms
                    SET form_name='Revised form'
                    WHERE id=:form_id
                """),
                {"form_id": form_id},
            )
            connection.execute(
                text("""
                    UPDATE peptide_chemical_forms
                    SET updated_at=now()
                    WHERE id=:form_id
                """),
                {"form_id": form_id},
            )

            revisions = connection.execute(
                text("""
                    SELECT revision_number, revision_origin, snapshot, content_hash,
                           supersedes_revision_id
                    FROM peptide_chemical_form_revisions
                    WHERE chemical_form_id=:form_id
                    ORDER BY revision_number
                """),
                {"form_id": form_id},
            ).mappings().all()
            assert len(revisions) == 2, "Timestamp-only updates must not create revisions"
            assert revisions[1]["revision_number"] == 2
            assert revisions[1]["revision_origin"] == "chemical_form_updated"
            assert revisions[1]["snapshot"]["form_name"] == "Revised form"
            assert revisions[1]["supersedes_revision_id"] == revisions[0]["id"]
            assert revisions[1]["content_hash"] != revisions[0]["content_hash"]

            # Reverting to an earlier snapshot is a new change, not a no-op.
            connection.execute(
                text("""
                    UPDATE peptide_chemical_forms
                    SET form_name='Initial form'
                    WHERE id=:form_id
                """),
                {"form_id": form_id},
            )
            revisions = connection.execute(
                text("""
                    SELECT revision_number, snapshot, supersedes_revision_id
                    FROM peptide_chemical_form_revisions
                    WHERE chemical_form_id=:form_id
                    ORDER BY revision_number
                """),
                {"form_id": form_id},
            ).mappings().all()
            assert len(revisions) == 3
            assert revisions[2]["revision_number"] == 3
            assert revisions[2]["snapshot"]["form_name"] == "Initial form"
            assert revisions[2]["supersedes_revision_id"] == revisions[1]["id"]

            with pytest.raises(DBAPIError):
                with connection.begin_nested():
                    connection.execute(
                        text("""
                            UPDATE peptide_chemical_form_revisions
                            SET snapshot='{}'::jsonb
                            WHERE chemical_form_id=:form_id
                        """),
                        {"form_id": form_id},
                    )
        finally:
            transaction.rollback()
