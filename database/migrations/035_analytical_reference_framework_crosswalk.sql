-- Reference-framework crosswalk for analytical test catalogue entries.
-- These links provide context only; they do not declare legal applicability or mandatory requirements.
INSERT INTO source_records (source_name, source_identifier, source_url, retrieved_at, raw_metadata)
VALUES
 ('European Medicines Agency / ICH','ICH-Q6B-STEP5','https://www.ema.europa.eu/en/scientific-guidelines/ich-q6b-specifications-test-procedures-acceptance-criteria-biotechnological-biological-products',now(),'{"document":"ICH Q6B","status":"Step 5","effective_date":"1999-09-01"}'::jsonb),
 ('European Medicines Agency / ICH','ICH-Q2-R2-STEP5','https://www.ema.europa.eu/en/scientific-guidelines/ich-q2r2-validation-analytical-procedures',now(),'{"document":"ICH Q2(R2)","status":"Step 5","effective_date":"2024-06-14"}'::jsonb),
 ('European Medicines Agency / ICH','ICH-Q14-STEP5','https://www.ema.europa.eu/en/scientific-guidelines/ich-q14-analytical-procedure-development',now(),'{"document":"ICH Q14","status":"Step 5","effective_date":"2024-06-14"}'::jsonb),
 ('United States Pharmacopeia','USP-PEPTIDE-STANDARDS-2023-12-22','https://www.usp.org/sites/default/files/usp/document/our-work/biologics/usp-bio_peptides-standards-22122023.pdf',now(),'{"document":"Peptide-related USP-NF Documentary Standards and USP Reference Standards","effective_date":"2023-12-22"}'::jsonb),
 ('United States Pharmacopeia','USP-503-1-TFA-PEPTIDES','https://doi.usp.org/USPNF/USPNF_M9393_01_01.html',now(),'{"document":"USP General Chapter <503.1> Trifluoroacetic Acid (TFA) in Peptides","document_type":"procedural_general_chapter"}'::jsonb)
ON CONFLICT (source_name, source_identifier)
DO UPDATE SET source_url=EXCLUDED.source_url,last_seen_at=now();

CREATE TABLE IF NOT EXISTS analytical_reference_frameworks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_code TEXT NOT NULL UNIQUE,
    issuing_body TEXT NOT NULL,
    document_title TEXT NOT NULL,
    reference_identifier TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (document_type IN (
        'guideline','informational_general_chapter','procedural_general_chapter','compendial_documentary_standard'
    )),
    jurisdiction_or_system TEXT NOT NULL,
    version_or_edition TEXT,
    effective_date DATE,
    official_status TEXT NOT NULL,
    scope_summary TEXT NOT NULL CHECK (length(trim(scope_summary)) >= 20),
    applicability_limitations TEXT NOT NULL CHECK (length(trim(applicability_limitations)) >= 20),
    source_id UUID NOT NULL REFERENCES source_records(id) ON DELETE RESTRICT,
    review_status review_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_analytical_reference_frameworks_status
    ON analytical_reference_frameworks(review_status, document_type, framework_code);

CREATE TABLE IF NOT EXISTS analytical_test_framework_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID NOT NULL REFERENCES analytical_test_catalogue(id) ON DELETE RESTRICT,
    framework_id UUID NOT NULL REFERENCES analytical_reference_frameworks(id) ON DELETE RESTRICT,
    relationship TEXT NOT NULL CHECK (relationship IN (
        'quality_attribute_context','analytical_development_context','analytical_validation_context',
        'informational_chapter','procedural_chapter'
    )),
    evidence_scope TEXT NOT NULL CHECK (length(trim(evidence_scope)) >= 10),
    applicability_limitations TEXT NOT NULL CHECK (length(trim(applicability_limitations)) >= 20),
    review_status review_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(test_id, framework_id, relationship)
);
CREATE INDEX IF NOT EXISTS idx_analytical_test_framework_links_test
    ON analytical_test_framework_links(test_id, review_status);
CREATE INDEX IF NOT EXISTS idx_analytical_test_framework_links_framework
    ON analytical_test_framework_links(framework_id, review_status);

WITH docs(code,issuer,title,ref,kind,jurisdiction,version,effective,status,scope,limits,source_name,source_identifier) AS (
 VALUES
 ('ICH_Q6B','ICH / EMA','Specifications: Test Procedures and Acceptance Criteria for Biotechnological/Biological Products','ICH Q6B','guideline','ICH member jurisdictions','Step 5','1999-09-01'::date,'Current Step 5 guideline',
  'Principles for specifications and quality attributes of biotechnological and biological products, including proteins, polypeptides, derivatives and products containing them.',
  'Scope is product-class and jurisdiction dependent. It is not a universal specification or a peptide-specific acceptance-limit table.',
  'European Medicines Agency / ICH','ICH-Q6B-STEP5'),
 ('ICH_Q2_R2','ICH / EMA','Validation of Analytical Procedures','ICH Q2(R2)','guideline','ICH member jurisdictions','Step 5 Revision 2','2024-06-14'::date,'Current Step 5 guideline',
  'General framework for validation of analytical procedures used for identity, assay or potency, purity and impurities, and other quantitative or qualitative measurements.',
  'Does not select a test for a peptide or supply molecule-specific acceptance criteria; procedure validation must be justified for intended use.',
  'European Medicines Agency / ICH','ICH-Q2-R2-STEP5'),
 ('ICH_Q14','ICH / EMA','Analytical Procedure Development','ICH Q14','guideline','ICH member jurisdictions','Step 5 Revision 1','2024-06-14'::date,'Current Step 5 guideline',
  'Science- and risk-based approaches to analytical procedure development and lifecycle management for drug substances and products.',
  'Development guidance is not a method recipe or product-specific requirement. Apply with the relevant jurisdiction and product context.',
  'European Medicines Agency / ICH','ICH-Q14-STEP5'),
 ('USP_1503','United States Pharmacopeia','Quality Attributes of Synthetic Peptide Drug Substances','USP General Chapter <1503>','informational_general_chapter','USP-NF / United States','USP-NF documentary standard list effective 2023-12-22','2023-12-22'::date,'Informational general chapter',
  'Informational chapter identified by USP as addressing quality attributes of synthetic peptide drug substances.',
  'Informational chapter status does not make every attribute a mandatory release test or define universal limits for every peptide.',
  'United States Pharmacopeia','USP-PEPTIDE-STANDARDS-2023-12-22'),
 ('USP_1052','United States Pharmacopeia','Biotechnology-Derived Articles — Amino Acid Analysis','USP General Chapter <1052>','informational_general_chapter','USP-NF / United States','USP-NF documentary standard list effective 2023-12-22','2023-12-22'::date,'Informational general chapter',
  'USP lists amino acid analysis among peptide-related documentary standards.',
  'Amino acid composition does not alone establish residue sequence, stereochemistry or intact molecular identity.',
  'United States Pharmacopeia','USP-PEPTIDE-STANDARDS-2023-12-22'),
 ('USP_503','United States Pharmacopeia','Acetic Acid in Peptides','USP General Chapter <503>','procedural_general_chapter','USP-NF / United States','USP-NF documentary standard list effective 2023-12-22','2023-12-22'::date,'Procedural general chapter',
  'USP lists a peptide-specific chapter for determination of acetic acid in peptides.',
  'Applicability depends on whether acetate is relevant to the specific material; do not assume acetate is present.',
  'United States Pharmacopeia','USP-PEPTIDE-STANDARDS-2023-12-22'),
 ('USP_503_1','United States Pharmacopeia','Trifluoroacetic Acid (TFA) in Peptides','USP General Chapter <503.1>','procedural_general_chapter','USP-NF / United States','USP-NF documentary standard list effective 2023-12-22','2023-12-22'::date,'Procedural general chapter',
  'USP describes procedures to determine TFA amount in peptides; TFA may be a residual process impurity or counterion.',
  'Use only when TFA is relevant to the material and applicable compendial context; this is not a general purity or identity assay.',
  'United States Pharmacopeia','USP-503-1-TFA-PEPTIDES'),
 ('USP_85','United States Pharmacopeia','Bacterial Endotoxins Test','USP General Chapter <85>','procedural_general_chapter','USP-NF / United States','USP-NF documentary standard list effective 2023-12-22','2023-12-22'::date,'Procedural general chapter',
  'USP lists bacterial endotoxins testing among peptide-related procedural standards.',
  'Test applicability and sample suitability depend on product, matrix and intended use; endotoxin testing is not sterility testing.',
  'United States Pharmacopeia','USP-PEPTIDE-STANDARDS-2023-12-22'),
 ('USP_1788','United States Pharmacopeia','Methods for the Determination of Subvisible Particulate Matter','USP General Chapter <1788> family','procedural_general_chapter','USP-NF / United States','USP-NF documentary standard list effective 2023-12-22','2023-12-22'::date,'Procedural general chapter family',
  'USP lists <1788>, <1788.1> and <1788.3> for subvisible particulate matter measurement, including light obscuration and flow imaging.',
  'Different techniques detect different particle populations; distinguish subvisible particulate matter from soluble molecular aggregates.',
  'United States Pharmacopeia','USP-PEPTIDE-STANDARDS-2023-12-22')
)
INSERT INTO analytical_reference_frameworks
 (framework_code,issuing_body,document_title,reference_identifier,document_type,jurisdiction_or_system,version_or_edition,effective_date,official_status,scope_summary,applicability_limitations,source_id)
SELECT d.code,d.issuer,d.title,d.ref,d.kind,d.jurisdiction,d.version,d.effective,d.status,d.scope,d.limits,s.id
FROM docs d JOIN source_records s ON s.source_name=d.source_name AND s.source_identifier=d.source_identifier
ON CONFLICT (framework_code) DO NOTHING;

WITH links(test_code,framework_code,relationship,scope,limits) AS (
 VALUES
 ('IDENTITY','ICH_Q6B','quality_attribute_context','ICH Q6B identity and characterization principles for relevant biological and polypeptide products.','The guidance does not prescribe one identity technique for every synthetic or therapeutic peptide.'),
 ('PURITY','ICH_Q6B','quality_attribute_context','ICH Q6B purity and impurity characterization principles.','Product-specific impurity profile and control strategy must be scientifically justified.'),
 ('CONTENT','ICH_Q6B','quality_attribute_context','ICH Q6B quantity and product characterization principles.','Quantity, chromatographic purity and potency are different quality attributes.'),
 ('SEQUENCE','ICH_Q6B','quality_attribute_context','ICH Q6B characterization and identity principles.','Specific sequence and structural techniques depend on molecular structure and modifications.'),
 ('POTENCY','ICH_Q6B','quality_attribute_context','ICH Q6B potency principles for products where biological activity is relevant.','Not every peptide has a suitable or required potency assay in every development context.'),
 ('STABILITY','ICH_Q6B','quality_attribute_context','ICH Q6B stability and degradation-profile considerations.','No shelf-life or stability claim follows from the guidance without product-specific data.'),
 ('IDENTITY','ICH_Q2_R2','analytical_validation_context','ICH Q2(R2) validation framework may be relevant to procedures used for identity measurements.','A guideline cross-reference does not mean every identity method requires identical validation characteristics.'),
 ('PURITY','ICH_Q2_R2','analytical_validation_context','ICH Q2(R2) framework for validation of purity and impurity procedures.','Validation characteristics depend on analytical purpose, range and intended use.'),
 ('CONTENT','ICH_Q2_R2','analytical_validation_context','ICH Q2(R2) framework for quantitative procedures.','No universal assay or acceptance limits are supplied by this mapping.'),
 ('POTENCY','ICH_Q2_R2','analytical_validation_context','ICH Q2(R2) framework can be relevant to quantitative or qualitative potency procedures.','Biological assay design and validation remain molecule- and mechanism-specific.'),
 ('STABILITY','ICH_Q2_R2','analytical_validation_context','ICH Q2(R2) includes considerations relevant to stability-indicating analytical procedures.','The cross-reference does not define a stability study protocol or shelf life.'),
 ('IDENTITY','ICH_Q14','analytical_development_context','ICH Q14 analytical procedure development principles may inform fit-for-purpose identity procedures.','Development framework is not a prescribed peptide identity procedure.'),
 ('PURITY','ICH_Q14','analytical_development_context','ICH Q14 science- and risk-based procedure development may inform impurity-separating methods.','No specific chromatography conditions or impurity limits are prescribed by this link.'),
 ('STABILITY','ICH_Q14','analytical_development_context','ICH Q14 analytical procedure development and lifecycle principles may inform stability-indicating procedures.','This link does not prove that a procedure is stability-indicating without data.'),
 ('AMINO_ACID','USP_1052','informational_chapter','USP lists <1052> amino acid analysis among peptide-related documentary standards.','Composition analysis alone cannot establish sequence order or stereochemistry.'),
 ('COUNTERIONS','USP_503','procedural_chapter','USP lists <503> for acetic acid determination in peptides.','Use only where acetate is a relevant analyte for the material.'),
 ('COUNTERIONS','USP_503_1','procedural_chapter','USP <503.1> describes TFA determination in peptides.','Use only where TFA is relevant; do not assume its presence.'),
 ('ENDOTOXIN','USP_85','procedural_chapter','USP lists <85> bacterial endotoxins test among peptide-related procedural standards.','Endotoxin suitability and requirements are product- and context-specific; this is not sterility testing.'),
 ('AGGREGATES','USP_1788','procedural_chapter','USP lists the <1788> chapter family for subvisible particulate matter measurement.','Subvisible particles are not equivalent to soluble molecular aggregates.')
)
INSERT INTO analytical_test_framework_links(test_id,framework_id,relationship,evidence_scope,applicability_limitations)
SELECT t.id,f.id,l.relationship,l.scope,l.limits
FROM links l JOIN analytical_test_catalogue t ON t.catalogue_code=l.test_code
JOIN analytical_reference_frameworks f ON f.framework_code=l.framework_code
ON CONFLICT (test_id,framework_id,relationship) DO NOTHING;
