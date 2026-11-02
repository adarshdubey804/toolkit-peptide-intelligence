"""Conservative peptide sequence normalization and identity fingerprints.

Only unmodified, linear sequences using the 20 standard L-amino-acid one-letter
codes are accepted. This module does not parse modified-residue notation,
D-residues, cyclization, conjugates, salts, or arbitrary SMILES/InChI. Those
must be represented as reviewed chemical-form attributes by a future parser.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

CANONICALIZATION_METHOD = "standard_l_amino_acid_one_letter_v1"
CANONICALIZATION_VERSION = "1"
NOTATION_FORMAT = "one_letter_amino_acid_sequence"
_STANDARD_RESIDUES = frozenset("ACDEFGHIKLMNPQRSTVWY")
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class CanonicalPeptideSequence:
    """A normalized sequence plus a versioned, non-unique lookup fingerprint."""

    raw_notation: str
    normalized_sequence: str
    notation_format: str
    canonicalization_method: str
    canonicalization_version: str
    identity_fingerprint: str
    residue_count: int


def canonicalize_one_letter_sequence(raw_notation: str) -> CanonicalPeptideSequence:
    """Normalize a strictly standard, unmodified, linear L-peptide sequence.

    Whitespace is ignored and letter case is normalized. No residue is silently
    substituted, inferred, or stripped. Fingerprints are lookup aids, not proof
    of chemical equivalence and must not be used as unique database keys.
    """
    if not isinstance(raw_notation, str):
        raise TypeError("Peptide notation must be a string.")
    raw = raw_notation
    normalized = _WHITESPACE.sub("", raw).upper()
    if not normalized:
        raise ValueError("Peptide sequence cannot be empty.")
    unsupported = sorted(set(normalized) - _STANDARD_RESIDUES)
    if unsupported:
        raise ValueError(
            "Unsupported residue or notation symbol(s): "
            + ", ".join(unsupported)
            + ". Only the 20 standard one-letter L-amino-acid codes are accepted; "
            "modified, ambiguous, D-residue, and chemical-form notation require "
            "an explicitly supported parser."
        )

    identity_payload = (
        f"{CANONICALIZATION_METHOD}\0{CANONICALIZATION_VERSION}\0{normalized}"
    ).encode("ascii")
    fingerprint = hashlib.sha256(identity_payload).hexdigest()
    return CanonicalPeptideSequence(
        raw_notation=raw,
        normalized_sequence=normalized,
        notation_format=NOTATION_FORMAT,
        canonicalization_method=CANONICALIZATION_METHOD,
        canonicalization_version=CANONICALIZATION_VERSION,
        identity_fingerprint=fingerprint,
        residue_count=len(normalized),
    )
