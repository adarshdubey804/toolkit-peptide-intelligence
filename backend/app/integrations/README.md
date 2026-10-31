# External research integrations

All integrations are read-only discovery clients. Results returned from external registries are source-attributed and marked `curation_status=not_reviewed`; they must not be silently promoted into curated scientific records.

## PubMed
- NCBI E-utilities ESearch and ESummary.
- Configure `NCBI_EMAIL`; `NCBI_API_KEY` is optional.
- API: `GET /api/v1/research/pubmed?q=...`.

## ClinicalTrials.gov
- ClinicalTrials.gov REST API v2: `GET https://clinicaltrials.gov/api/v2/studies`.
- No API key is required for public study search.
- API: `GET /api/v1/research/clinicaltrials?q=...`; optional `page_token` follows the registry cursor.

## UniProtKB
- UniProt REST API: `GET https://rest.uniprot.org/uniprotkb/search`.
- Search returns accession, protein/gene names, organism, reviewed status and sequence length.
- API: `GET /api/v1/research/uniprot?q=...`.

## RCSB Protein Data Bank
- RCSB Search API v2 plus Data API entry detail.
- Search results are capped at 20; each returned entry includes PDB identifier, title, experimental method and deposit date where available.
- API: `GET /api/v1/research/rcsb?q=...`.

## PubChem
- PubChem PUG REST compound-name property lookup.
- Resolves a chemical name to CID, formula, molecular weight, SMILES, InChI and InChIKey where available.
- API: `GET /api/v1/research/pubchem?name=...`.
- A PubChem compound is not necessarily identical to a biologically active peptide entity, salt, conjugate or formulation. Confirm identity and chemical form before linking properties to a peptide profile.
