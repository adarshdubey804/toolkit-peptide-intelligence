"""Read-only DBAASP v4 adapter for source-attributed experimental peptide evidence."""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

BASE_URL = "https://dbaasp.org"
API_VERSION = "4.0.1"
SOURCE_NAME = "Database of Antimicrobial Activity and Structure of Peptides (DBAASP)"
SOURCE_URL = "https://dbaasp.org"
ATTRIBUTION = (
    "Data were obtained from the DBAASP (https://dbaasp.org), an open-access antimicrobial "
    "peptide data resource. Cite the DBAASP source and its current release in public materials."
)
CACHE_TTL_SECONDS = 3600
_CACHE: dict[tuple[str, int], tuple[float, dict]] = {}
_CACHE_LOCK = asyncio.Lock()


def _as_search_rows(payload: Any) -> tuple[int | None, list[dict]]:
    if not isinstance(payload, dict):
        raise ValueError("DBAASP returned an unsupported search response.")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("DBAASP search response did not contain a data array.")
    total = payload.get("totalCount")
    return (int(total) if total is not None else None), [row for row in rows if isinstance(row, dict)]


def normalize_peptide(detail: dict) -> dict:
    identifier = detail.get("dbaaspId") or detail.get("id")
    if identifier is None:
        raise ValueError("DBAASP peptide record is missing its stable identifier.")
    record_id = str(identifier)
    record_url = detail.get("url")
    if not isinstance(record_url, str) or not record_url.startswith("https://dbaasp.org/"):
        record_url = f"{BASE_URL}/peptides/{identifier}"

    target_activities = detail.get("targetActivities") or []
    antibiofilm_activities = detail.get("antibiofilmActivities") or []
    cytotoxic_activities = detail.get("hemoliticCytotoxicActivities") or []
    synergy_records = detail.get("synergies") or []
    articles = detail.get("articles") or []
    return {
        "source": SOURCE_NAME,
        "source_identifier": record_id,
        "source_version": f"DBAASP API {API_VERSION}",
        "source_url": record_url,
        "source_locator": f"DBAASP peptide record {record_id}",
        "candidate_name": detail.get("majorName") or detail.get("name") or f"DBAASP {record_id}",
        "name": detail.get("name"),
        "major_name": detail.get("majorName"),
        "sequence": detail.get("sequence"),
        "sequence_length": detail.get("sequenceLength"),
        "synthesis_type": (detail.get("synthesisType") or {}).get("name") if isinstance(detail.get("synthesisType"), dict) else detail.get("synthesisType"),
        "complexity": (detail.get("complexity") or {}).get("name") if isinstance(detail.get("complexity"), dict) else detail.get("complexity"),
        "n_terminus": detail.get("nterminus") or detail.get("nTerminus"),
        "c_terminus": detail.get("cterminus") or detail.get("cTerminus"),
        "unusual_amino_acids": detail.get("unusualAminoAcids") or [],
        "intrachain_bonds": detail.get("intrachainBonds") or [],
        "interchain_bonds": detail.get("interchainBonds") or [],
        "coordination_bonds": detail.get("coordinationBonds") or [],
        "smiles": detail.get("smiles") or [],
        "pdb_structures": detail.get("pdbs") or [],
        "structure_model": detail.get("structureModel"),
        "physicochemical_properties": detail.get("physicoChemicalProperties") or [],
        "target_activities": target_activities,
        "antibiofilm_activities": antibiofilm_activities,
        "hemolytic_cytotoxic_activities": cytotoxic_activities,
        "reported_combination_activity": synergy_records,
        "references": articles,
        "target_groups": detail.get("targetGroups") or [],
        "target_objects": detail.get("targetObjects") or [],
        "source_genes": detail.get("sourceGenes") or [],
        "uniprot_cross_references": detail.get("uniprots") or [],
        "pubchem": detail.get("pubChem"),
        "curation_status": "not_reviewed_in_peptide_intelligence",
        "evidence_level": "source_asserted",
        "evidence_notice": (
            "DBAASP records contain literature-derived experimental observations. Preserve assay, "
            "organism/strain, medium, pH, ionic strength, concentration, unit and reference context. "
            "Do not treat reported activity as clinical efficacy or incidence. Combination records "
            "may be peptide-antibiotic combinations and must not be mislabeled as peptide-peptide synergy."
        ),
        "license_notice": ATTRIBUTION,
        "jurisdiction": None,
        "raw_record": detail,
    }


class DbaaspProvider:
    async def search(self, query: str, limit: int = 20) -> dict:
        term = query.strip()
        if len(term) < 2:
            raise ValueError("DBAASP search query must contain at least two characters.")
        if not 1 <= limit <= 25:
            raise ValueError("DBAASP result limit must be between 1 and 25.")
        cache_key = (term.casefold(), limit)
        now = time.monotonic()
        async with _CACHE_LOCK:
            cached = _CACHE.get(cache_key)
            if cached and now - cached[0] < CACHE_TTL_SECONDS:
                return cached[1]

        timeout = httpx.Timeout(40.0, connect=8.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers={"Accept": "application/json"}) as client:
            response = await client.get(
                f"{BASE_URL}/peptides",
                params={"name.value": term, "limit": limit, "offset": 0},
            )
            if response.status_code == 204:
                result = {
                    "source": SOURCE_NAME, "query": term, "total": 0, "returned_count": 0,
                    "items": [], "source_version": f"DBAASP API {API_VERSION}",
                    "license_notice": ATTRIBUTION,
                }
            else:
                response.raise_for_status()
                total, rows = _as_search_rows(response.json())
                semaphore = asyncio.Semaphore(3)

                async def get_detail(row: dict) -> dict | None:
                    peptide_id = row.get("id") or row.get("dbaaspId")
                    if peptide_id is None:
                        return None
                    async with semaphore:
                        detail_response = await client.get(f"{BASE_URL}/peptides/{peptide_id}")
                        if detail_response.status_code in (204, 404):
                            return None
                        detail_response.raise_for_status()
                        payload = detail_response.json()
                        if not isinstance(payload, dict):
                            raise ValueError("DBAASP peptide detail response was not an object.")
                        return payload

                detail_results = await asyncio.gather(
                    *(get_detail(row) for row in rows[:limit]),
                    return_exceptions=True,
                )
                items = []
                failed_details = 0
                seen = set()
                for detail in detail_results:
                    if isinstance(detail, Exception):
                        failed_details += 1
                        continue
                    if not detail:
                        continue
                    normalized = normalize_peptide(detail)
                    identifier = normalized["source_identifier"]
                    if identifier not in seen:
                        seen.add(identifier)
                        items.append(normalized)

                result = {
                    "source": SOURCE_NAME,
                    "query": term,
                    "total": total,
                    "returned_count": len(items),
                    "items": items,
                    "detail_failures": failed_details,
                    "source_version": f"DBAASP API {API_VERSION}",
                    "source_url": SOURCE_URL,
                    "license_notice": ATTRIBUTION,
                    "coverage_notice": (
                        "DBAASP covers antimicrobial and cytotoxic peptide/peptidomimetic records, "
                        "including ribosomal, nonribosomal, synthetic and modified forms. It is an "
                        "AMP-focused resource, not a complete inventory of all therapeutic peptides."
                    ),
                }

        async with _CACHE_LOCK:
            _CACHE[cache_key] = (time.monotonic(), result)
        return result
