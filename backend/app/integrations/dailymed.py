"""Read-only adapter for NLM DailyMed Structured Product Label (SPL) metadata."""
import httpx

BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"


def normalize_spl(record: dict) -> dict:
    set_id = record.get("setid")
    return {
        "set_id": set_id,
        "spl_version": record.get("spl_version"),
        "title": record.get("title"),
        "published_date": record.get("published_date"),
        "source_url": f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}" if set_id else None,
        "label_api_url": f"{BASE_URL}/spls/{set_id}.json" if set_id else None,
        "source": "DailyMed",
        "jurisdiction": "US",
        "curation_status": "not_reviewed",
        "label_notice": "DailyMed provides current Structured Product Label information. Its current SPL is not necessarily identical to the last FDA-approved labeling in Drugs@FDA.",
    }


class DailyMedProvider:
    async def search_by_name(self, name: str, limit: int = 20, page: int = 1) -> dict:
        term = name.strip()
        if len(term) < 2:
            raise ValueError("DailyMed name search must contain at least two characters.")
        if not 1 <= limit <= 100:
            raise ValueError("DailyMed page size must be between 1 and 100.")
        if page < 1:
            raise ValueError("DailyMed page must be at least 1.")

        timeout = httpx.Timeout(25.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(
                f"{BASE_URL}/spls.json",
                params={"drug_name": term, "pagesize": limit, "page": page},
            )
            if response.status_code == 404:
                return {"source": "DailyMed", "query": term, "total": 0, "items": []}
            response.raise_for_status()
            payload = response.json()

        metadata = payload.get("metadata") or {}
        records = payload.get("data") or []
        return {
            "source": "DailyMed",
            "query": term,
            "total": int(metadata.get("total_elements") or len(records)),
            "page": int(metadata.get("current_page") or page),
            "total_pages": int(metadata.get("total_pages") or 1),
            "items": [normalize_spl(item) for item in records],
            "retrieved_from_source": True,
            "curation_status": "not_reviewed",
            "coverage_notice": "SPL search results are label records, not proof of FDA approval or a complete inventory of peptide entities.",
        }
