-- Separate peptide sequence records from fully specified chemical/material forms.
-- Fingerprints are indexed but deliberately not unique until canonicalization rules
-- have been validated against stereochemical and noncanonical-residue collision cases.
ALTER TABLE peptide_sequences
    ADD COLUMN IF NOT EXISTS raw_notation TEXT,
    ADD COLUMN IF NOT EXISTS normalized_sequence TEXT,
    ADD COLUMN IF NOT EXISTS notation_format TEXT NOT NULL DEFAULT 'one_letter',
    ADD COLUMN IF NOT EXISTS canonicalization_method TEXT,
    ADD COLUMN IF NOT EXISTS canonicalization_version TEXT,
    ADD COLUMN IF NOT EXISTS identity_fingerprint TEXT;

UPDATE peptide_sequences
SET raw_notation = sequence
WHERE raw_notation IS NULL;

CREATE INDEX IF NOT EXISTS idx_peptide_sequences_identity_fingerprint
    ON peptide_sequences(identity_fingerprint)
    WHERE identity_fingerprint IS NOT NULL;

CREATE TABLE IF NOT EXISTS peptide_chemical_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peptide_id UUID NOT NULL REFERENCES peptides(id) ON DELETE CASCADE,
    peptide_sequence_id UUID REFERENCES peptide_sequences(id) ON DELETE RESTRICT,
    form_name TEXT NOT NULL,
    form_type TEXT NOT NULL DEFAULT 'unspecified',
    raw_chemical_notation TEXT,
    normalized_sequence TEXT,
    residue_encoding JSONB NOT NULL DEFAULT '[]'::jsonb,
    stereochemistry JSONB NOT NULL DEFAULT '{}'::jsonb,
    noncanonical_residues JSONB NOT NULL DEFAULT '[]'::jsonb,
    terminal_chemistry JSONB NOT NULL DEFAULT '{}'::jsonb,
    post_translational_modifications JSONB NOT NULL DEFAULT '[]'::jsonb,
    cyclization JSONB NOT NULL DEFAULT '{}'::jsonb,
    conjugation JSONB NOT NULL DEFAULT '{}'::jsonb,
    salt_and_counterions JSONB NOT NULL DEFAULT '{}'::jsonb,
    chemical_formula TEXT,
    average_molecular_mass NUMERIC(16,6),
    monoisotopic_mass NUMERIC(16,6),
    canonical_smiles TEXT,
    inchi TEXT,
    inchikey TEXT,
    identity_fingerprint TEXT,
    canonicalization_method TEXT,
    canonicalization_version TEXT,
    source_id UUID REFERENCES source_records(id),
    review_status review_status NOT NULL DEFAULT 'draft',
    supersedes_form_id UUID REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT peptide_chemical_forms_type_check CHECK (
        form_type IN ('unspecified','linear_peptide','cyclic_peptide','branched_peptide',
                      'conjugate','modified_peptide','salt_form','other')
    ),
    CONSTRAINT peptide_chemical_forms_mass_check CHECK (
        (average_molecular_mass IS NULL OR average_molecular_mass > 0)
        AND (monoisotopic_mass IS NULL OR monoisotopic_mass > 0)
    ),
    CONSTRAINT peptide_chemical_forms_not_self_superseding CHECK (
        supersedes_form_id IS NULL OR supersedes_form_id <> id
    )
);

CREATE INDEX IF NOT EXISTS idx_peptide_chemical_forms_peptide_review
    ON peptide_chemical_forms(peptide_id, review_status);
CREATE INDEX IF NOT EXISTS idx_peptide_chemical_forms_sequence
    ON peptide_chemical_forms(peptide_sequence_id);
CREATE INDEX IF NOT EXISTS idx_peptide_chemical_forms_fingerprint
    ON peptide_chemical_forms(identity_fingerprint)
    WHERE identity_fingerprint IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_peptide_chemical_forms_inchikey
    ON peptide_chemical_forms(inchikey)
    WHERE inchikey IS NOT NULL;

COMMENT ON TABLE peptide_chemical_forms IS
    'Distinct chemically specified forms linked to a peptide entity and optional sequence record. Does not imply equivalence between forms.';
COMMENT ON COLUMN peptide_chemical_forms.identity_fingerprint IS
    'Versioned deterministic fingerprint; intentionally non-unique until canonicalization collision testing is complete.';
COMMENT ON COLUMN peptide_chemical_forms.stereochemistry IS
    'Residue-level stereochemistry representation; do not assume all residues are L.';
COMMENT ON COLUMN peptide_chemical_forms.terminal_chemistry IS
    'Explicit N- and C-terminal chemistry, including caps and amidation where applicable.';
COMMENT ON COLUMN peptide_chemical_forms.cyclization IS
    'Cyclization type and bond endpoints; preserve topology rather than relying on sequence text alone.';
COMMENT ON COLUMN peptide_chemical_forms.conjugation IS
    'Conjugate payload, linker and attachment-site representation.';
COMMENT ON COLUMN peptide_chemical_forms.salt_and_counterions IS
    'Salt stoichiometry and counterion metadata, distinct from peptide covalent identity.';
