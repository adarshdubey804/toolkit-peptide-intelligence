"""Read-only ChEMBL peptide-biotherapeutic discovery adapter."""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
SOURCE_NAME = "ChEMBL / EMBL-EBI"
ATTRIBUTION = (
    "ChEMBL data are provided by EMBL-EBI under CC BY-SA 3.0. "
    "Attribute ChEMBL and redistribute adaptations under the same licence."
)


def _records(payload: Any, key: str) -> list[dict]:
    if not isinstance(payload, dict):
        raise ValueError(f"ChEMBL response for {key} was not a JSON object.")
    rows = payload.get(key)
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise ValueError(f"ChEMBL response field {key} was not an array.")
    return [row for row in rows if isinstance(row, dict)]


def normalize_peptide_biotherapeutic(
    molecule: dict,
    biotherapeutic: dict,
    mechanisms: list[dict],
    release: str | None,
) -> dict | None:
    chembl_id = molecule.get("molecule_chembl_id")
    if not chembl_id:
        return None
    helm = biotherapeutic.get("helm_notation")
    if not isinstance(helm, str) or not helm.strip().upper().startswith("PEPTIDE1{"):
        # ChEMBL biotherapeutics also include antibodies and recombinant proteins.
        # Only explicitly peptide-typed HELM polymers enter this peptide discovery adapter.
        return None

    moa_rows = []
    targets = []
    for item in mechanisms:
        moa = item.get("mechanism_of_action")
        target = item.get("target_name") or item.get("target_chembl_id")
        action = item.get("action_type")
        if moa:
            moa_rows.append(str(moa))
        if target:
            targets.append(str(target))
        if action and target:
            moa_rows.append(f"{action} at {target}")

    unique_moa = list(dict.fromkeys(moa_rows))
    unique_targets = list(dict.fromkeys(targets))
    return {
        "source": SOURCE_NAME,
        "source_identifier": str(chembl_id),
        "source_version": release or "ChEMBL live API release not returned",
        "source_url": f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/",
        "source_locator": f"ChEMBL molecule {chembl_id}; biotherapeutic HELM record",
        "candidate_name": molecule.get("pref_name") or str(chembl_id),
        "molecule_chembl_id": str(chembl_id),
        "molecule_type": molecule.get("molecule_type"),
        "max_phase": molecule.get("max_phase"),
        "therapeutic_flag": molecule.get("therapeutic_flag"),
        "reported_sequence": helm,
        "reported_sequence_type": "HELM peptide polymer notation",
        "helm_notation": helm,
        "biotherapeutic_description": biotherapeutic.get("description"),
        "reported_target": "; ".join(unique_targets) if unique_targets else None,
        "reported_mechanism": "; ".join(unique_moa) if unique_moa else None,
        "mechanism_of_action": "; ".join(unique_moa) if unique_moa else None,
        "mechanism_records": mechanisms,
        "molecule_properties": molecule.get("molecule_properties") or {},
        "molecule_structures": molecule.get("molecule_structures") or {},
        "curation_status": "not_reviewed",
        "jurisdiction": None,
        "license": "CC BY-SA 3.0",
        "attribution": ATTRIBUTION,
        "evidence_notice": (
            "ChEMBL is a curated drug-discovery database. HELM peptide notation and any mechanism "
            "records are source-reported observations. A ChEMBL molecule record is not, by itself, "
            "proof of regulatory authorisation, clinical efficacy, or exact equivalence to a marketed "
            "product or a canonical peptide dossier."
        ),
    }


class ChEMBLProvider:
    async def search_peptides(self, query: str, limit: int = 20) -> dict:
        term = query.strip()
        if len(term) < 2:
            raise ValueError("ChEMBL peptide search must contain at least two characters.")
        if not 1 <= limit <= 30:
            raise ValueError("ChEMBL result limit must be between 1 and 30.")

        timeout = httpx.Timeout(35.0, connect=8.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            search_response = await client.get(
                f"{BASE_URL}/molecule/search.json",
                params={"q": term, "limit": min(limit * 3, 90)},
                headers={"Accept": "application/json"},
            )
            search_response.raise_for_status()
            search_payload = search_response.json()
            molecules = _records(search_payload, "molecules")
            unique = {}
            for molecule in molecules:
                chembl_id = molecule.get("molecule_chembl_id")
                if chembl_id:
                    unique[str(chembl_id)] = molecule
            selected = list(unique.values())[: min(limit * 3, 90)]

            async def get_biotherapeutic(molecule: dict):
                chembl_id = molecule.get("molecule_chembl_id")
                response = await client.get(
                    f"{BASE_URL}/biotherapeutic.json",
                    params={"molecule_chembl_id": chembl_id, "limit": 5},
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                return molecule, _records(response.json(), "biotherapeutics")

            semaphore = asyncio.Semaphore(4)

            async def bounded_fetch(molecule: dict):
                async with semaphore:
                    return await get_biotherapeutic(molecule)

            biotherapeutic_results = await asyncio.gather(
                *(bounded_fetch(molecule) for molecule in selected)
            )

            peptide_candidates = []
            for molecule, bio_rows in biotherapeutic_results:
                peptide_bio = next(
                    (
                        row for row in bio_rows
                        if isinstance(row.get("helm_notation"), str)
                        and row["helm_notation"].strip().upper().startswith("PEPTIDE1{")
                    ),
                    None,
                )
                if peptide_bio is None:
                    continue
                chembl_id = molecule["molecule_chembl_id"]
                mechanism_response = await client.get(
                    f"{BASE_URL}/mechanism.json",
                    params={"molecule_chembl_id": chembl_id, "limit": 30},
                    headers={"Accept": "application/json"},
                )
                mechanism_response.raise_for_status()
                mechanism_rows = _records(mechanism_response.json(), "mechanisms")
                peptide_candidates.append((molecule, peptide_bio, mechanism_rows))
                if len(peptide_candidates) >= limit:
                    break

            release = None
            try:
                status_response = await client.get(f"{BASE_URL}/status.json")
                status_response.raise_for_status()
                status_payload = status_response.json()
                release = status_payload.get("chembl_db_version")
            except (httpx.HTTPError, ValueError, TypeError):
                release = None

        items = [
            normalized
            for molecule, bio, mechanisms in peptide_candidates
            if (normalized := normalize_peptide_biotherapeutic(molecule, bio, mechanisms, release))
        ]
        return {
            "source": SOURCE_NAME,
            "query": term,
            "total": len(items),
            "items": items,
            "retrieved_from_source": True,
            "source_version": release or "ChEMBL live API release not returned",
            "curation_status": "not_reviewed",
            "license_notice": ATTRIBUTION,
            "coverage_notice": (
                "This adapter searches ChEMBL molecule records and retains only biotherapeutic "
                "records with explicit PEPTIDE1 HELM notation. It does not enumerate all peptides "
                "in ChEMBL or the world; search terms, API result ranking and source coverage limit "
                "the returned candidates."
            ),
        }
