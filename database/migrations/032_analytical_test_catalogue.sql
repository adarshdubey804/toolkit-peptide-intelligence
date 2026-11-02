-- Structured, source-linked peptide quality-test reference catalogue.
-- Seed records are deliberately draft reference candidates; citation is not semantic validation.
INSERT INTO source_records (source_name, source_identifier, source_url, retrieved_at, raw_metadata)
VALUES
 ('US FDA / ICH Q6B', 'FDA-1998-D-0003', 'https://www.fda.gov/regulatory-information/search-fda-guidance-documents/q6b-specifications-test-procedures-and-acceptance-criteria-biotechnologicalbiological-products', now(), '{"document":"Q6B Specifications: Test Procedures and Acceptance Criteria for Biotechnological/Biological Products","status":"Final guidance","issued":"1999-08"}'::jsonb),
 ('United States Pharmacopeia', 'USP-peptide-standards-2023-11-07', 'https://www.usp.org/sites/default/files/usp/document/our-work/biologics/usp-bio-peptides-standards-07112023.pdf', now(), '{"document":"Peptide-related USP-NF Documentary Standards and USP Reference Standards","effective":"2023-11-07"}'::jsonb)
ON CONFLICT (source_name, source_identifier)
DO UPDATE SET source_url=EXCLUDED.source_url, last_seen_at=now();

CREATE TABLE IF NOT EXISTS analytical_test_catalogue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalogue_code TEXT NOT NULL UNIQUE,
    test_name TEXT NOT NULL,
    quality_attribute TEXT NOT NULL,
    test_intent TEXT NOT NULL CHECK (length(trim(test_intent)) >= 20),
    candidate_method_families JSONB NOT NULL DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(candidate_method_families)='array'),
    material_considerations TEXT NOT NULL,
    interpretation_limitations TEXT NOT NULL,
    review_status review_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_analytical_test_catalogue_status
    ON analytical_test_catalogue(review_status, quality_attribute, catalogue_code);

CREATE TABLE IF NOT EXISTS analytical_test_catalogue_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID NOT NULL REFERENCES analytical_test_catalogue(id) ON DELETE CASCADE,
    source_record_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    evidence_scope TEXT NOT NULL CHECK (length(trim(evidence_scope)) >= 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(test_id, source_record_id)
);

-- Initial entries are reference candidates, not approved specifications, acceptance
-- criteria, validated methods or universal recommendations.
WITH seeds(code,name,attribute,intent,methods,materials,limitations) AS (
 VALUES
 ('IDENTITY','Molecular identity','identity',
  'Establish whether the material is consistent with the intended peptide identity using one or more appropriately specific characteristics.',
  '["mass spectrometry","chromatographic comparison","sequence or peptide mapping"]'::jsonb,
  'Consider sequence, termini, stereochemistry, disulfide connectivity, conjugation and counterion form where relevant.',
  'A matching nominal mass or single chromatographic peak alone may not establish complete sequence, stereochemistry, connectivity or modification identity.'),
 ('PURITY','Purity and related substances','purity',
  'Assess the relative presence of the desired peptide and product-related or process-related impurities using a justified separation or measurement approach.',
  '["liquid chromatography","capillary electrophoresis","mass spectrometry"]'::jsonb,
  'Consider peptide length, charge, hydrophobicity, modifications, related sequences and sample matrix.',
  'Area percent is not automatically mass purity or absolute assay. Co-elution, response-factor differences and undetected impurities may affect interpretation.'),
 ('CONTENT','Peptide content or quantity','quantity',
  'Determine the amount or content of peptide in the defined material or dosage form using an appropriate, justified measurement approach.',
  '["amino acid analysis","appropriate quantitative physicochemical assay"]'::jsonb,
  'Consider water, counterions, residual solvents, excipients and reference-standard traceability.',
  'Content, chromatographic purity and biological potency are distinct attributes and must not be substituted for one another.'),
 ('SEQUENCE','Sequence and structural characterization','structure',
  'Characterize sequence-related and other structural features that are relevant to the identity and quality understanding of the peptide.',
  '["mass spectrometry","peptide mapping","amino acid analysis","spectroscopic characterization"]'::jsonb,
  'Consider sequence length, isomerism, noncanonical residues, terminal modifications, cyclization and disulfide bonds.',
  'The suitability and resolving power of each approach depend on the structure and modification profile; no single technique is universally sufficient.'),
 ('AMINO_ACID','Amino-acid composition','composition',
  'Characterize amino-acid composition as a supporting attribute for peptide characterization or quantity assessment where scientifically justified.',
  '["amino acid analysis"]'::jsonb,
  'Consider residues with method-dependent stability or recovery and the need to interpret results with sequence information.',
  'Composition does not by itself establish residue order, stereochemistry, sequence identity or intact molecular structure.'),
 ('AGGREGATES','Aggregation and particulate matter','physical_state',
  'Assess soluble aggregate species or particulate matter when relevant to the peptide material, formulation and intended presentation.',
  '["size-exclusion chromatography","light obscuration","flow imaging","other justified particle characterization"]'::jsonb,
  'Distinguish soluble molecular aggregates from visible and subvisible particles; consider formulation and container context.',
  'Different techniques detect different size ranges and particle properties; results are not interchangeable and require matrix-specific assessment.'),
 ('COUNTERIONS','Counterions and residual peptide-associated reagents','composition',
  'Assess relevant counterions or residual peptide-associated reagents when their presence is relevant to material definition, safety or quality.',
  '["ion chromatography","appropriate specific chemical assay"]'::jsonb,
  'USP peptide-related references include specific chapters for acetic acid and trifluoroacetic acid in peptides.',
  'Do not assume a particular counterion or residual reagent is present. Select analytes from the actual material and manufacturing history.'),
 ('ENDOTOXIN','Bacterial endotoxins','microbiological_quality',
  'Assess bacterial endotoxin burden when required by the material, route, product context or applicable quality framework.',
  '["bacterial endotoxins test"]'::jsonb,
  'Consider sample matrix interference, inhibition/enhancement, product-specific suitability and the applicable compendial framework.',
  'An endotoxin result is not a sterility result. Method suitability and acceptance criteria are product- and context-dependent.'),
 ('STERILITY','Sterility','microbiological_quality',
  'Assess whether a material or finished product meets an applicable sterility testing requirement when such a requirement is relevant.',
  '["compendial sterility test"]'::jsonb,
  'Applicability depends on product presentation, intended use, applicable compendial requirements and validated test suitability.',
  'Sterility testing does not establish endotoxin control, absence of all adventitious agents or aseptic process assurance by itself.'),
 ('BIOBURDEN','Bioburden or microbial limits','microbiological_quality',
  'Characterize microbial contamination levels where appropriate for the material stage and its quality-control strategy.',
  '["microbial enumeration","microbial limits testing"]'::jsonb,
  'Distinguish raw material, in-process, bulk and finished-product context; consider antimicrobial or inhibitory matrix effects.',
  'Bioburden is not sterility and should not be interpreted as proof that a product is sterile.'),
 ('POTENCY','Biological activity or potency','potency',
  'Assess a relevant biological activity or potency attribute when the peptide mechanism and intended product context support such an assay.',
  '["functional biological assay","binding or receptor activity assay"]'::jsonb,
  'Requires a defined biological rationale, suitable reference material, controls and an appropriately qualified or validated assay strategy.',
  'Physicochemical identity or content does not establish biological potency. Assay relevance is molecule- and mechanism-specific.'),
 ('STABILITY','Stability and degradation profile','stability',
  'Monitor relevant quality attributes and degradation-related changes over time under defined study conditions.',
  '["stability-indicating chromatography","mass spectrometry","appropriate physical characterization"]'::jsonb,
  'Study design depends on formulation, container closure, storage conditions, intended shelf life and degradation pathways.',
  'A single time point or forced-degradation observation does not establish shelf life. Stability conclusions require a justified study design and data.')
)
INSERT INTO analytical_test_catalogue
 (catalogue_code,test_name,quality_attribute,test_intent,candidate_method_families,material_considerations,interpretation_limitations,review_status)
SELECT code,name,attribute,intent,methods,materials,limitations,'draft'::review_status FROM seeds
ON CONFLICT (catalogue_code) DO NOTHING;

WITH source_map(code, source_name, source_identifier, scope) AS (
 VALUES
 ('IDENTITY','US FDA / ICH Q6B','FDA-1998-D-0003','ICH Q6B identity principles for biological products and polypeptides'),
 ('PURITY','US FDA / ICH Q6B','FDA-1998-D-0003','ICH Q6B purity and impurity principles'),
 ('CONTENT','US FDA / ICH Q6B','FDA-1998-D-0003','ICH Q6B quantity principles'),
 ('SEQUENCE','US FDA / ICH Q6B','FDA-1998-D-0003','ICH Q6B characterization and identity principles'),
 ('AMINO_ACID','United States Pharmacopeia','USP-peptide-standards-2023-11-07','USP peptide-related general chapter <1052> amino acid analysis'),
 ('AGGREGATES','United States Pharmacopeia','USP-peptide-standards-2023-11-07','USP peptide-related reference lists particulate matter chapters <1788>, <1788.1> and <1788.3>'),
 ('COUNTERIONS','United States Pharmacopeia','USP-peptide-standards-2023-11-07','USP peptide-related chapters <503> acetic acid and <503.1> trifluoroacetic acid'),
 ('ENDOTOXIN','United States Pharmacopeia','USP-peptide-standards-2023-11-07','USP peptide-related reference list includes chapter <85> bacterial endotoxins test'),
 ('STERILITY','US FDA / ICH Q6B','FDA-1998-D-0003','ICH Q6B notes that relevant pharmacopoeial specifications include sterility testing'),
 ('BIOBURDEN','US FDA / ICH Q6B','FDA-1998-D-0003','ICH Q6B identifies microbial limits among typical pharmacopoeial tests for relevant drug products'),
 ('POTENCY','US FDA / ICH Q6B','FDA-1998-D-0003','ICH Q6B potency principles and relevant validated potency assay where applicable'),
 ('STABILITY','US FDA / ICH Q6B','FDA-1998-D-0003','ICH Q6B requires product-specific stability-indicating profiles and consideration of degradation')
)
INSERT INTO analytical_test_catalogue_sources (test_id,source_record_id,evidence_scope)
SELECT t.id,s.id,m.scope
FROM source_map m
JOIN analytical_test_catalogue t ON t.catalogue_code=m.code
JOIN source_records s ON s.source_name=m.source_name AND s.source_identifier=m.source_identifier
ON CONFLICT (test_id,source_record_id) DO NOTHING;
