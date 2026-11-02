import pytest

from app.services.peptide_identity import (
    CANONICALIZATION_METHOD,
    CANONICALIZATION_VERSION,
    canonicalize_one_letter_sequence,
)


def test_sequence_canonicalization_normalizes_case_and_whitespace():
    result = canonicalize_one_letter_sequence(" acdE\nFG ")
    assert result.raw_notation == " acdE\nFG "
    assert result.normalized_sequence == "ACDEFG"
    assert result.residue_count == 6
    assert result.canonicalization_method == CANONICALIZATION_METHOD
    assert result.canonicalization_version == CANONICALIZATION_VERSION
    assert len(result.identity_fingerprint) == 64


def test_equivalent_formatting_has_same_versioned_fingerprint():
    compact = canonicalize_one_letter_sequence("ACDEFG")
    formatted = canonicalize_one_letter_sequence("ac de\nf g")
    assert compact.identity_fingerprint == formatted.identity_fingerprint


def test_distinct_primary_sequences_have_distinct_fingerprints():
    first = canonicalize_one_letter_sequence("ACDEFG")
    substitution = canonicalize_one_letter_sequence("ACDEFA")
    assert first.identity_fingerprint != substitution.identity_fingerprint


@pytest.mark.parametrize("notation", [
    "",
    "   ",
    "ACDB",
    "ACDX",
    "ACDU",
    "ACDO",
    "ACD*",
    "A-C-D",
    "H-[D-Ala]-OH",
    "cyclo(ACDE)",
    "C[C@H](N)C(=O)O",
])
def test_rejects_ambiguous_modified_or_non_sequence_notation(notation):
    with pytest.raises(ValueError):
        canonicalize_one_letter_sequence(notation)


def test_rejects_non_string_input_without_coercion():
    with pytest.raises(TypeError):
        canonicalize_one_letter_sequence(None)


def test_raw_notation_is_preserved_for_provenance():
    raw = "  acd EFG  "
    result = canonicalize_one_letter_sequence(raw)
    assert result.raw_notation == raw
    assert result.normalized_sequence == "ACDEFG"


def test_fingerprint_is_not_declared_as_chemical_equivalence():
    # The sequence-only parser has no representation for stereochemistry,
    # terminal chemistry, PTMs, cyclization, conjugation, or counterions.
    result = canonicalize_one_letter_sequence("ACDEFG")
    assert result.notation_format == "one_letter_amino_acid_sequence"
    assert result.canonicalization_method == "standard_l_amino_acid_one_letter_v1"
