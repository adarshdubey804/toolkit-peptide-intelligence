from io import BytesIO

import pytest
from fastapi import HTTPException
from openpyxl import Workbook, load_workbook
from pydantic import ValidationError

from app.routers.workbook_import import (
    DossierMediaInput,
    DossierReferenceInput,
    _extract_peptide_rows,
    _worksheet_rows,
)


def _catalogue_workbook(row_count: int = 128, *, include_peptides: bool = True):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Peptides" if include_peptides else "Other"
    sheet.append(["Peptide catalogue — source workbook"])
    sheet.append([
        "Generic/Common Name",
        "Brand / Other Names",
        "Treatment Category",
        "Primary Use / Indication",
        "FDA Status",
        "Status Detail",
        "First US Approval",
        "Notes",
    ])
    for index in range(row_count):
        sheet.append([
            f"Peptide {index + 1}",
            None,
            "Research",
            "Source-reported indication",
            "No",
            "Not approved",
            None,
            f"Source note {index + 1}",
        ])
    # An entirely blank trailing row must not become a candidate.
    sheet.append([None] * 8)
    workbook.create_sheet("Summary").append(["Rows", row_count])
    workbook.create_sheet("Notes & Sources").append(["Source", "Workbook supplied by user"])

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return load_workbook(stream, read_only=True, data_only=True)


def test_workbook_import_extracts_all_128_rows_and_preserves_source_fields():
    workbook = _catalogue_workbook()
    try:
        rows = _extract_peptide_rows(workbook)
    finally:
        workbook.close()

    assert len(rows) == 128
    first_row_number, first_row, first_name, first_status = rows[0]
    assert first_row_number == 3
    assert first_name == "Peptide 1"
    assert first_status == "No"
    assert first_row["Treatment Category"] == "Research"
    assert first_row["Notes"] == "Source note 1"
    assert rows[-1][2] == "Peptide 128"


@pytest.mark.parametrize("row_count", [0, 1, 127, 129])
def test_workbook_import_rejects_catalogues_without_exactly_128_named_rows(row_count):
    workbook = _catalogue_workbook(row_count)
    try:
        with pytest.raises(HTTPException) as error:
            _extract_peptide_rows(workbook)
    finally:
        workbook.close()

    assert error.value.status_code == 422
    assert "Expected 128 populated peptide rows" in error.value.detail


def test_workbook_import_requires_peptides_worksheet():
    workbook = _catalogue_workbook(include_peptides=False)
    try:
        with pytest.raises(HTTPException) as error:
            _extract_peptide_rows(workbook)
    finally:
        workbook.close()

    assert error.value.status_code == 422
    assert "Peptides" in error.value.detail


def test_workbook_import_finds_header_after_title_rows_and_ignores_blank_rows():
    workbook = _catalogue_workbook()
    try:
        rows = _extract_peptide_rows(workbook)
    finally:
        workbook.close()

    assert rows[0][0] == 3
    assert rows[-1][0] == 130
    assert len(rows) == 128


def test_companion_worksheet_rows_are_retained_as_json_compatible_values():
    workbook = _catalogue_workbook()
    try:
        summary = _worksheet_rows(workbook["Summary"])
        notes = _worksheet_rows(workbook["Notes & Sources"])
    finally:
        workbook.close()

    assert summary == [["Rows", 128]]
    assert notes == [["Source", "Workbook supplied by user"]]


def test_dossier_reference_requires_https_url():
    valid = DossierReferenceInput(
        claim_text="The source supports this exact mechanistic claim.",
        title="Primary source",
        source_name="Example journal",
        url="https://example.org/article",
    )
    assert str(valid.url) == "https://example.org/article"

    with pytest.raises(ValidationError):
        DossierReferenceInput(
            claim_text="The source supports this exact mechanistic claim.",
            title="Primary source",
            source_name="Example journal",
            url="http://example.org/article",
        )


def test_dossier_media_requires_alt_text_attribution_source_and_reuse_terms():
    valid = DossierMediaInput(
        title="Experimental structure",
        image_url="https://example.org/structure.png",
        alt_text="Ribbon diagram of the experimentally resolved peptide structure.",
        source_name="RCSB PDB",
        source_identifier="PDB:1ABC",
        attribution="RCSB Protein Data Bank",
        license_or_reuse_terms="Reuse under the source entry's stated terms.",
    )
    assert valid.source_identifier == "PDB:1ABC"

    with pytest.raises(ValidationError):
        DossierMediaInput(
            title="Structure",
            image_url="https://example.org/structure.png",
            alt_text="Short",
            source_name="RCSB PDB",
            license_or_reuse_terms="Unknown",
        )
