import httpx

ALPHAFOLD_API = "https://alphafold.ebi.ac.uk/api/prediction"


class AlphaFoldProvider:
    async def get_prediction(self, accession: str) -> dict:
        accession = accession.strip().upper()
        if not accession or len(accession) > 20 or not accession.replace("-", "").isalnum():
            raise ValueError("Provide a valid UniProt accession.")
        timeout = httpx.Timeout(20.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(f"{ALPHAFOLD_API}/{accession}")
            if response.status_code == 404:
                return {
                    "source": "AlphaFold Protein Structure Database",
                    "accession": accession,
                    "total": 0,
                    "items": [],
                    "curation_status": "not_reviewed",
                }
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("AlphaFold returned an unexpected response.")
        items = []
        for record in payload[:20]:
            if not isinstance(record, dict):
                continue
            items.append({
                "accession": record.get("uniprotAccession") or accession,
                "entry_id": record.get("entryId"),
                "gene": record.get("gene"),
                "protein_description": record.get("uniprotDescription"),
                "organism": record.get("organismScientificName"),
                "taxonomy_id": record.get("taxId"),
                "sequence_length": record.get("uniprotSequenceLength"),
                "model_version": record.get("latestVersion"),
                "model_created_date": record.get("modelCreatedDate"),
                "model_modified_date": record.get("latestVersionDate"),
                "global_confidence_score": record.get("globalMetricValue"),
                "mean_plddt": record.get("confidenceAvg"),
                "fraction_plddt_very_high": record.get("fractionPlddtVeryHigh"),
                "fraction_plddt_confident": record.get("fractionPlddtConfident"),
                "fraction_plddt_low": record.get("fractionPlddtLow"),
                "fraction_plddt_very_low": record.get("fractionPlddtVeryLow"),
                "pdb_url": record.get("pdbUrl"),
                "cif_url": record.get("cifUrl"),
                "pae_image_url": record.get("paeImageUrl"),
                "source_url": f"https://alphafold.ebi.ac.uk/entry/{accession}",
                "source": "AlphaFold Protein Structure Database",
                "curation_status": "not_reviewed",
                "structure_type": "computational_prediction",
            })
        return {
            "source": "AlphaFold Protein Structure Database",
            "accession": accession,
            "total": len(items),
            "items": items,
            "curation_status": "not_reviewed",
        }
