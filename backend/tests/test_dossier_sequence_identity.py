import pytest

from app.routers.dossiers import SequenceInput, _sequence_identity_fields
from app.services.peptide_identity import CANONICALIZATION_METHOD, CANONICALIZATION_VERSION


def test_dossier_sequence_identity_canonicalizes_only_standard_unmodified_l_sequences():
    raw = " acdE\nFG "
    fields = _sequence_identity_fields(SequenceInput(sequence=raw))

    assert fields["raw_notation"] == raw
    assert fields["normalized_sequence"] == "ACDEFG"
    assert fields["notation_format"] == "one_letter_amino_acid_sequence"
    assert fields["canonicalization_method"] == CANONICALIZATION_METHOD
    assert fields["canonicalization_version"] == CANONICALIZATION_VERSION
    assert len(fields["identity_fingerprint"]) == 64


@pytest.mark.parametrize("payload", [
    {"sequence": "ACDEFG", "modifications": [{"position": 2, "modification": "phosphorylation"}]},
    {"sequence": "ACDEFG", "n_terminus": "acetylated"},
    {"sequence": "ACDEFG", "c_terminus": "amidated"},
    {"sequence": "ACDEFG", "stereochemistry_notes": "Contains a D-amino acid"},
])
def test_explicit_chemical_context_is_never_collapsed_to_sequence_only_identity(payload):
    fields = _sequence_identity_fields(SequenceInput(**payload))

    assert fields["raw_notation"] == "ACDEFG"
    assert fields["normalized_sequence"] is None
    assert fields["identity_fingerprint"] is None
    assert fields["canonicalization_method"] is None
    assert fields["notation_format"] == "amino_acid_with_explicit_chemistry"


@pytest.mark.parametrize("sequence", ["ACDX", "ACDU", "H-[D-Ala]-OH", "cyclo(ACDE)"])
def test_unparsed_amino_acid_notation_is_preserved_without_fabricated_identity(sequence):
    fields = _sequence_identity_fields(SequenceInput(sequence=sequence))

    assert fields["raw_notation"] == sequence
    assert fields["normalized_sequence"] is None
    assert fields["identity_fingerprint"] is None
    assert fields["notation_format"] == "unparsed_amino_acid"


def test_non_amino_acid_sequence_is_not_sent_to_peptide_sequence_canonicalizer():
    fields = _sequence_identity_fields(SequenceInput(sequence="ATCG", sequence_type="nucleotide"))

    assert fields["raw_notation"] == "ATCG"
    assert fields["notation_format"] == "nucleotide"
    assert fields["normalized_sequence"] is None
    assert fields["identity_fingerprint"] is None
