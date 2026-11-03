-- Add a peer-reviewed literature source for the BPC-157 dossier.
-- The described pathways are literature-reported proposals, not a validated
-- human mechanism. Keep the source snapshot and discovery observation immutable.
DO $bpc157_literature$
DECLARE
    v_candidate_id UUID;
    v_source_id UUID;
    v_payload JSONB := jsonb_build_object(
        'source', 'PubMed',
        'source_title', 'Multifunctionality and Possible Medical Application of the BPC 157 Peptide-Literature and Patent Review',
        'pmid', '40005999',
        'pmcid', 'PMC11859134',
        'doi', '10.3390/ph18020185',
        'publication_date', '2025-01-30',
        'publication_type', 'Review',
        'mechanism_of_action_summary',
            'A 2025 literature review describes proposed interactions with nitric oxide synthase (NOS), increased expression of antioxidant enzymes including heme oxygenase-1 (HO-1), and possible stimulation or modulation of VEGF receptors. These are literature-summarized proposed pathways, not an established clinical mechanism.',
        'source_excerpt',
            'The BPC 157 pentadecapeptide positively interacts with nitric oxide synthase to increase expression of several antioxidants, including heme oxygenase (HO-1). The review also states that the peptide may stimulate VEGF receptors.',
        'evidence_scope',
            'Narrative literature review; the summarized biological activity is predominantly preclinical and does not establish a validated human mechanism.',
        'curation_status', 'not_reviewed',
        'source_url', 'https://pubmed.ncbi.nlm.nih.gov/40005999/'
    );
    v_payload_hash TEXT := 'c97130e5f8cdef11d075c1ea139d396ee0ff2ec40c61dca8d35868450f4c7868';
BEGIN
    SELECT candidate.id INTO v_candidate_id
    FROM peptide_discovery_candidates candidate
    JOIN source_records source ON source.id=candidate.source_record_id
    WHERE source.source_name='FDA Compounding Safety Risks'
      AND source.source_identifier='BPC-157'
      AND candidate.source_entity_identifier='BPC-157';

    IF v_candidate_id IS NULL THEN
        RAISE EXCEPTION 'BPC-157 FDA provisional dossier must exist before adding literature evidence';
    END IF;

    INSERT INTO source_records (
        source_name, source_identifier, source_url, retrieved_at,
        license_notes, raw_metadata
    ) VALUES (
        'PubMed',
        '40005999',
        'https://pubmed.ncbi.nlm.nih.gov/40005999/',
        TIMESTAMPTZ '2026-11-03 00:00:00+00',
        'PubMed bibliographic metadata and abstract; retain PMID, DOI, PMCID and original publication link.',
        jsonb_build_object('provenance_kind', 'normalized_provider_record',
                           'record_title', 'Multifunctionality and Possible Medical Application of the BPC 157 Peptide-Literature and Patent Review')
    )
    ON CONFLICT (source_name, source_identifier) DO UPDATE
       SET source_url=EXCLUDED.source_url
    RETURNING id INTO v_source_id;

    INSERT INTO source_record_versions (
        source_record_id, content_hash, raw_payload, captured_at, payload_kind
    ) VALUES (
        v_source_id, v_payload_hash, v_payload,
        TIMESTAMPTZ '2026-11-03 00:00:00+00', 'normalized_provider_record'
    )
    ON CONFLICT (source_record_id, content_hash) DO NOTHING;

    UPDATE peptide_discovery_candidates
    SET reported_mechanism = COALESCE(reported_mechanism, v_payload->>'mechanism_of_action_summary'),
        raw_metadata = jsonb_set(
            raw_metadata,
            '{literature_sources}',
            COALESCE(raw_metadata->'literature_sources', '[]'::jsonb) ||
                jsonb_build_array(jsonb_build_object(
                    'source_name', 'PubMed',
                    'source_identifier', '40005999',
                    'source_url', 'https://pubmed.ncbi.nlm.nih.gov/40005999/',
                    'title', v_payload->>'source_title',
                    'publication_date', v_payload->>'publication_date',
                    'publication_type', 'Review',
                    'doi', '10.3390/ph18020185',
                    'pmcid', 'PMC11859134',
                    'evidence_scope', v_payload->>'evidence_scope',
                    'source_excerpt', v_payload->>'source_excerpt',
                    'mechanism_of_action_summary', v_payload->>'mechanism_of_action_summary',
                    'curation_status', 'not_reviewed'
                )),
            true
        ),
        last_seen_at = GREATEST(last_seen_at, TIMESTAMPTZ '2026-11-03 00:00:00+00'),
        last_observed_at = GREATEST(last_observed_at, TIMESTAMPTZ '2026-11-03 00:00:00+00'),
        updated_at = now()
    WHERE id=v_candidate_id;

    INSERT INTO peptide_discovery_observations (
        candidate_id, source_record_id, source_version, payload, payload_hash, observed_at
    ) VALUES (
        v_candidate_id, v_source_id, NULL, v_payload, v_payload_hash,
        TIMESTAMPTZ '2026-11-03 00:00:00+00'
    )
    ON CONFLICT (candidate_id, payload_hash) DO NOTHING;
END;
$bpc157_literature$;
