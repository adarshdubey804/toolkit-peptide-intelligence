import httpx

SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
DATA_URL = "https://data.rcsb.org/rest/v1/core/entry"


class RCSBProvider:
    async def search(self, query: str, limit: int = 10) -> dict:
        payload = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": query},
            },
            "return_type": "entry",
            "request_options": {
                "paginate": {"start": 0, "rows": limit},
                "results_content_type": ["experimental"],
                "sort": [{"sort_by": "score", "direction": "desc"}],
            },
        }
        timeout = httpx.Timeout(25.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.post(SEARCH_URL, json=payload)
            if response.status_code == 204:
                return {"source": "RCSB PDB", "query": query, "total": 0, "items": []}
            response.raise_for_status()
            result = response.json()

            items = []
            for row in result.get("result_set", []):
                pdb_id = row.get("identifier")
                if not pdb_id:
                    continue
                detail_response = await client.get(f"{DATA_URL}/{pdb_id}")
                detail_response.raise_for_status()
                detail = detail_response.json()
                struct = detail.get("struct") or {}
                exptl = detail.get("exptl") or []
                items.append({
                    "pdb_id": pdb_id,
                    "title": struct.get("title"),
                    "experimental_methods": [item.get("method") for item in exptl if item.get("method")],
                    "deposit_date": detail.get("rcsb_accession_info", {}).get("deposit_date"),
                    "url": f"https://www.rcsb.org/structure/{pdb_id}",
                    "source": "RCSB PDB",
                    "retrieved_from_source": True,
                    "curation_status": "not_reviewed",
                })
        return {
            "source": "RCSB PDB",
            "query": query,
            "total": result.get("total_count"),
            "items": items,
        }
