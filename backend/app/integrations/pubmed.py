import httpx

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedProvider:
    def __init__(self, email: str, api_key: str | None = None):
        self.email = email
        self.api_key = api_key

    async def search(self, query: str, limit: int = 10) -> dict:
        common = {"tool": "ToolkitPeptideIntelligence", "email": self.email}
        if self.api_key:
            common["api_key"] = self.api_key
        timeout = httpx.Timeout(20.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}/esearch.fcgi", params={**common, "db": "pubmed", "term": query, "retmode": "json", "retmax": limit, "sort": "relevance"})
            response.raise_for_status()
            result = response.json()["esearchresult"]
            ids = result.get("idlist", [])
            if not ids:
                return {"source": "PubMed", "query": query, "total": int(result.get("count", 0)), "items": []}
            response = await client.get(f"{BASE_URL}/esummary.fcgi", params={**common, "db": "pubmed", "id": ",".join(ids), "retmode": "json"})
            response.raise_for_status()
            summary = response.json()["result"]
            items = []
            for uid in summary.get("uids", []):
                record = summary.get(uid, {})
                items.append({
                    "pmid": uid,
                    "title": record.get("title"),
                    "journal": record.get("fulljournalname") or record.get("source"),
                    "publication_date": record.get("pubdate"),
                    "authors": [author.get("name") for author in record.get("authors", [])[:8]],
                    "doi": next((item.get("value") for item in record.get("articleids", []) if item.get("idtype") == "doi"), None),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    "source": "PubMed",
                    "retrieved_from_source": True,
                    "curation_status": "not_reviewed",
                })
            return {"source": "PubMed", "query": query, "total": int(result.get("count", 0)), "items": items}
