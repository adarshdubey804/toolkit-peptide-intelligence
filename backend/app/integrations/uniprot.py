import httpx

BASE_URL = "https://rest.uniprot.org/uniprotkb/search"


class UniProtProvider:
    async def search(self, query: str, limit: int = 10) -> dict:
        params = {
            "query": query,
            "format": "json",
            "size": limit,
            "fields": "accession,id,protein_name,gene_names,organism_name,reviewed,length",
        }
        timeout = httpx.Timeout(20.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        items = []
        for record in payload.get("results", []):
            organism = record.get("organism") or {}
            genes = record.get("genes") or []
            protein = record.get("proteinDescription") or {}
            recommended = protein.get("recommendedName") or {}
            full_name = recommended.get("fullName") or {}
            items.append({
                "accession": record.get("primaryAccession"),
                "entry_name": record.get("uniProtkbId"),
                "protein_name": full_name.get("value"),
                "gene_names": [
                    gene.get("geneName", {}).get("value")
                    for gene in genes if gene.get("geneName", {}).get("value")
                ],
                "organism": organism.get("scientificName"),
                "organism_taxonomy_id": organism.get("taxonId"),
                "reviewed": record.get("entryType") == "UniProtKB reviewed (Swiss-Prot)",
                "sequence_length": (record.get("sequence") or {}).get("length"),
                "url": f"https://www.uniprot.org/uniprotkb/{record.get('primaryAccession')}/entry"
                    if record.get("primaryAccession") else None,
                "source": "UniProtKB",
                "retrieved_from_source": True,
                "curation_status": "not_reviewed",
            })
        return {
            "source": "UniProtKB",
            "query": query,
            "total": payload.get("results", []) and payload.get("results", [{}])[0].get("total"),
            "items": items,
        }
