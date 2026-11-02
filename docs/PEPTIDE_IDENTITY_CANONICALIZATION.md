# Peptide sequence canonicalization contract

## Supported input

The initial canonicalizer accepts only a linear, unmodified sequence expressed
with the 20 standard one-letter amino-acid codes (ACDEFGHIKLMNPQRSTVWY). It
normalizes case and removes whitespace. It preserves the exact original input
as `raw_notation`.

## Explicitly unsupported

The function rejects ambiguous residue symbols (including B, Z, J, X, U and O),
gap/stop markers, FASTA headers, bracketed residue labels, D-residue notation,
terminal modifications, post-translational modifications, cyclization,
conjugation, salts/counterions, SMILES, and InChI. Rejection is intentional:
unsupported notation must never be silently converted into an apparently
canonical sequence.

## Fingerprint semantics

The SHA-256 fingerprint is calculated over the canonicalization method,
version, and normalized sequence. It is a deterministic lookup aid for this
narrow input grammar. It is not a unique database key, a structure identifier,
or proof that two chemical materials are equivalent.

A future chemical-form canonicalizer must separately model stereochemistry,
noncanonical residues, termini, PTMs, cyclization, conjugation, and
salt/counterion state, and must have collision/round-trip tests before it is
used for equivalence decisions.

## Persistence boundary

This module is pure and does not write to the database, modify curator review
status, merge records, or supersede chemical forms. Callers must retain raw
notation and source provenance and must treat generated values as unreviewed
until the normal curation workflow approves them.
