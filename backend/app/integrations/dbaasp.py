"""Read-only DBAASP v4 peptide discovery adapter with source attribution."""
import asyncio
from urllib.parse import quote

import httpx

BASE_URL = "https://dbaasp.org"
API_VERSION = "4.0.1"


def normalize_peptide(record: dict) -> dict:
    dbaasp_id = record.get("dbaaspId") or record.get("id")
    if not dbaasp_id:
        raise ValueError("DBAASP record is missing its stable identifier.")
    name = record.get("name") or record.get("majorName") or str(dbaasp_id)
    sequence = record.get("sequence")
    target_objects = record.get("targetObjects") or []
    target_names = [
        item.get("name") for item in target_objects
        if isinstance(item, dict) and item.get("name")
    ]
    n_terminus = record.get("nTerminus") or record.get("nterminus")
    c_terminus = record.get("cTerminus") or record.get("cterminus")
    chemical_features = []
    for label, value in (("N-terminus", n_terminus), ("C-terminus", c_terminus)):
        if isinstance(value, dict) and value.get("name"):
            chemical_features.append(f"{label}: {value['name']}")
    return {
        "source_identifier": str(dbaasp_id),
        "candidate_name": name,
        "reported_sequence": sequence,
        "reported_sequence_type": "mature_peptide_sequence" if sequence else None,
        "reported_chemical_form": "; ".join(chemical_features) or None,
        "reported_target": "; ".join(dict.fromkeys(target_names)) or None,
        "sequence_length": record.get("sequenceLength") or (len(sequence) if sequence else None),
        "complexity": (record.get("complexity") or {}).get("name")
            if isinstance(record.get("complexity"), dict) else record.get("complexity"),
        "synthesis_type": (record.get("synthesisType") or {}).get("name")
            if isinstance(record.get("synthesisType"), dict) else record.get("synthesisType"),
        "source": "DBAASP",
        "source_url": f"{BASE_URL}/peptides/{quote(str(dbaasp_id), safe='')}",
        "source_version": API_VERSION,
        "jurisdiction": None,
        "curation_status": "not_reviewed",
        "development_status": "experimental_antimicrobial_activity_record_observed",
        "coverage_notice": (
            "DBAASP is a curated antimicrobial peptide activity and structure resource. "
            "Its experimental activity records are not proof of clinical efficacy, safety, "
            "regulatory authorization or therapeutic development status."
        ),
        "attribution": (
            "Acknowledge DBAASP as the source in public materials and cite its database publication."
        ),
        "raw_source_record": record,
    }


class DbaaspProvider:
    async def _get_json(self, path: str, params: dict | None = None) -> dict:
        timeout = httpx.Timeout(30.0, connect=8.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}{path}", params=params)
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("DBAASP returned an unexpected response.")
        return payload

    async def get_peptide(self, dbaasp_id: str) -> dict:
        return await self._get_json(f"/peptides/{quote(dbaasp_id, safe='')}")

    async def search(self, query: str, limit: int = 20, offset: int = 0) -> dict:
        term = query.strip()
        if len(term) < 2:
            raise ValueError("DBAASP search requires at least two characters.")
        if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
            raise ValueError("DBAASP pagination is outside the supported range.")
        search_result = await self._get_json(
            "/peptides",
            params={"name.value": term, "limit": limit, "offset": offset},
        )
        rows = search_result.get("data") or []
        semaphore = asyncio.Semaphore(5)

        async def enrich(row: dict) -> dict:
            identifier = row.get("dbaaspId")
            if not identifier:
                return row
            try:
                async with semaphore:
                    detail = await self.get_peptide(str(identifier))
                return detail
            except (httpx.HTTPError, ValueError, TypeError):
                # Keep the search hit when a detail endpoint is temporarily unavailable.
                return row

        details = await asyncio.gather(*(enrich(row) for row in rows if isinstance(row, dict)))
        items = [normalize_peptide(record) for record in details]
        return {
            "source": "DBAASP",
            "source_version": API_VERSION,
            "query": term,
            "total": search_result.get("totalCount"),
            "offset": offset,
            "limit": limit,
            "items": items,
            "curation_status": "not_reviewed",
            "coverage_notice": (
                "DBAASP covers antimicrobial peptide records, including ribosomal, nonribosomal "
                "and synthetic peptides. It is not a complete global inventory of all peptides."
            ),
            "attribution": (
                "DBAASP data may be accessed and reused without restriction, with public acknowledgement "
                "of DBAASP as the source and citation of the database publication."
            ),
        }
