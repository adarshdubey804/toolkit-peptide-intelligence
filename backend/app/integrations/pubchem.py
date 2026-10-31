from urllib.parse import quote

import httpx

BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PROPERTIES = "MolecularFormula,MolecularWeight,ConnectivitySMILES,SMILES,InChI,InChIKey"


class PubChemProvider:
    async def search_by_name(self, name: str) -> dict:
        encoded_name = quote(name.strip(), safe="")
        url = f"{BASE_URL}/compound/name/{encoded_name}/property/{PROPERTIES}/JSON"
        timeout = httpx.Timeout(25.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 404:
                return {"source": "PubChem", "query": name, "total": 0, "items": []}
            response.raise_for_status()
            payload = response.json()

        items = []
        for record in payload.get("PropertyTable", {}).get("Properties", []):
            cid = record.get("CID")
            items.append({
                "cid": cid,
                "molecular_formula": record.get("MolecularFormula"),
                "molecular_weight": record.get("MolecularWeight"),
                "canonical_smiles": record.get("ConnectivitySMILES"),
                "isomeric_smiles": record.get("SMILES"),
                "inchi": record.get("InChI"),
                "inchikey": record.get("InChIKey"),
                "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" if cid else None,
                "source": "PubChem",
                "retrieved_from_source": True,
                "curation_status": "not_reviewed",
                "property_origin": "source_reported_or_computed_by_pubchem",
            })
        return {"source": "PubChem", "query": name, "total": len(items), "items": items}
