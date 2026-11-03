-- Seed one source-backed provisional dossier for BPC-157 from the FDA's
-- official compounding safety page. This is not a marketing-authorization record.
-- Keep the source observation immutable and require curator identity review.
DO $bpc157_seed$
DECLARE
    v_source_id UUID;
    v_candidate_id UUID;
    v_payload JSONB := jsonb_build_object(
        'curation_status', 'unreviewed',
        'jurisdiction', 'US',
        'retrieved_date', '2026-11-03',
        'source', 'FDA',
        'source_section', 'Bulk drug substances nominated but withdrawn',
        'source_statement',
            'Compounded drugs containing BPC-157 may pose risk for immunogenicity for certain routes of administration and may have complexities with regard to peptide-related impurities and active pharmaceutical ingredient characterization. FDA has identified no, or only limited, safety-related information for the proposed routes of administration.',
        'source_status_interpretation',
            'FDA-listed bulk drug substance nomination that was withdrawn; this is not a drug marketing authorization or an FDA approval determination.',
        'source_title',
            'Certain Bulk Drug Substances for Use in Compounding that May Present Significant Safety Risks',
        'source_url',
            'https://www.fda.gov/drugs/human-drug-compounding/certain-bulk-drug-substances-use-compounding-may-present-significant-safety-risks',
        'substance', 'BPC-157'
    );
    v_payload_hash TEXT := 'fa393e852e3cce8b833bf4dabb82ff769e568aa82d3d321a5253705f03b4dade';
BEGIN
    INSERT INTO source_records (
        source_name, source_identifier, source_url, retrieved_at,
        license_notes, raw_metadata
    ) VALUES (
        'FDA Compounding Safety Risks',
        'BPC-157',
        'https://www.fda.gov/drugs/human-drug-compounding/certain-bulk-drug-substances-use-compounding-may-present-significant-safety-risks',
        TIMESTAMPTZ '2026-11-03 00:00:00+00',
        'Official FDA public information; retain attribution and source link.',
        jsonb_build_object('provenance_kind', 'official_source_seed', 'source_title',
            'Certain Bulk Drug Substances for Use in Compounding that May Present Significant Safety Risks')
    )
    ON CONFLICT (source_name, source_identifier) DO UPDATE
       SET source_url = EXCLUDED.source_url
    RETURNING id INTO v_source_id;

    INSERT INTO source_record_versions (
        source_record_id, content_hash, raw_payload, captured_at, payload_kind
    ) VALUES (
        v_source_id, v_payload_hash, v_payload,
        TIMESTAMPTZ '2026-11-03 00:00:00+00', 'normalized_provider_record'
    )
    ON CONFLICT (source_record_id, content_hash) DO NOTHING;

    INSERT INTO peptide_discovery_candidates (
        source_record_id, source_entity_identifier, source_entity_url,
        candidate_name, candidate_kind, source_development_status,
        source_jurisdiction_code, reported_sequence, reported_sequence_type,
        reported_chemical_form, reported_target, reported_mechanism,
        identity_match_status, match_rationale, candidate_status,
        first_seen_at, last_seen_at, last_observed_at, raw_metadata
    ) VALUES (
        v_source_id, 'BPC-157',
        'https://www.fda.gov/drugs/human-drug-compounding/certain-bulk-drug-substances-use-compounding-may-present-significant-safety-risks',
        'BPC-157', 'research_peptide',
        'FDA lists BPC-157 under bulk drug substances nominated but withdrawn and describes potential immunogenicity and peptide impurity/API characterization concerns. This is a compounding safety-source status, not a drug approval status.',
        'US', NULL, NULL, NULL, NULL, NULL,
        'unresolved',
        'Provisional source observation only. Verify sequence, stereochemistry, chemical form and aliases before linking to a canonical peptide identity.',
        'needs_review',
        TIMESTAMPTZ '2026-11-03 00:00:00+00',
        TIMESTAMPTZ '2026-11-03 00:00:00+00',
        TIMESTAMPTZ '2026-11-03 00:00:00+00',
        jsonb_build_object(
            'seeded_from_official_source', true,
            'source_record', v_payload,
            'notice', 'This is an unreviewed candidate dossier. A withdrawn compounding nomination is not an FDA drug approval or disapproval determination.'
        )
    )
    ON CONFLICT (source_record_id, source_entity_identifier) DO UPDATE
       SET last_seen_at = GREATEST(peptide_discovery_candidates.last_seen_at, EXCLUDED.last_seen_at),
           last_observed_at = GREATEST(peptide_discovery_candidates.last_observed_at, EXCLUDED.last_observed_at),
           updated_at = now()
    RETURNING id INTO v_candidate_id;

    INSERT INTO peptide_discovery_observations (
        candidate_id, source_record_id, source_version, payload, payload_hash, observed_at
    ) VALUES (
        v_candidate_id, v_source_id, NULL, v_payload, v_payload_hash,
        TIMESTAMPTZ '2026-11-03 00:00:00+00'
    )
    ON CONFLICT (candidate_id, payload_hash) DO NOTHING;
END;
$bpc157_seed$;

COMMENT ON TABLE peptide_discovery_candidates IS
    'Global source-backed peptide discovery observations awaiting identity resolution and curation. A candidate is not a verified canonical peptide or a regulatory status determination.';
