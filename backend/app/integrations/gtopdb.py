"""Read-only IUPHAR/BPS Guide to PHARMACOLOGY peptide-ligand adapter."""
import asyncio

import httpx

BASE_URL = "https://www.guidetopharmacology.org/services"
SOURCE_NAME = "IUPHAR/BPS Guide to PHARMACOLOGY"


def _as_records(payload) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        return [payload]
    raise ValueError("GtoPdb returned an unsupported JSON payload.")


def normalize_ligand(record: dict, interactions: list[dict]) -> dict:
    ligand_id = record.get("ligandId") or record.get("id") or record.get("ligand_id")
    name = record.get("name") or record.get("ligandName") or record.get("preferredName")
    targets = []
    actions = []
    for interaction in interactions:
        target = (
            interaction.get("targetName")
            or interaction.get("target_name")
            or interaction.get("target")
        )
        if isinstance(target, dict):
            target = target.get("name") or target.get("preferredName")
        if target and str(target) not in targets:
            targets.append(str(target))
        action = (
            interaction.get("type")
            or interaction.get("interactionType")
            or interaction.get("action")
        )
        if action:
            phrase = f"{action} at {target}" if target else str(action)
            if phrase not in actions:
                actions.append(phrase)

    ligand_url = f"{BASE_URL}/ligands/{ligand_id}" if ligand_id is not None else None
    return {
        "source_identifier": str(ligand_id) if ligand_id is not None else None,
        "ligand_id": ligand_id,
        "candidate_name": name,
        "ligand_type": record.get("type") or record.get("ligandType"),
        "synonyms": record.get("synonyms") or record.get("synonym"),
        "reported_target": "; ".join(targets) if targets else None,
        "reported_mechanism": "; ".join(actions) if actions else None,
        "target": "; ".join(targets) if targets else None,
        "mechanism_of_action": "; ".join(actions) if actions else None,
        "reported_interactions": interactions,
        "raw_ligand_record": record,
        "source": SOURCE_NAME,
        "source_url": ligand_url,
        "jurisdiction": None,
        "curation_status": "not_reviewed",
        "evidence_notice": (
            "GtoPdb is an expert-curated pharmacology resource. These ligand and interaction "
            "records are source-reported observations; they are not automatically linked to "
            "a canonical peptide identity or promoted to a verified mechanism-of-action claim."
        ),
    }


class GtoPdbProvider:
    async def search_peptides(self, query: str, limit: int = 20, api_key: str | None = None) -> dict:
        term = query.strip()
        if len(term) < 2:
            raise ValueError("GtoPdb peptide search must contain at least two characters.")
        if not 1 <= limit <= 30:
            raise ValueError("GtoPdb result limit must be between 1 and 30.")
        if not api_key or not api_key.strip():
            return {
                "source": SOURCE_NAME,
                "query": term,
                "status": "not_configured",
                "total": None,
                "items": [],
                "error": "GtoPdb requires a registered API key. Configure GTOPDB_API_KEY to enable this source.",
            }

        timeout = httpx.Timeout(25.0, connect=5.0)
        headers = {"GTP-API-Key": api_key.strip(), "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            async def search_type(ligand_type: str) -> list[dict]:
                response = await client.get(
                    f"{BASE_URL}/ligands",
                    params={"type": ligand_type, "name": term},
                )
                if response.status_code in (204, 404):
                    return []
                response.raise_for_status()
                return _as_records(response.json())

            peptide_records, endogenous_records = await asyncio.gather(
                search_type("Peptide"),
                search_type("Endogenous peptide"),
            )
            unique = {}
            for record in peptide_records + endogenous_records:
                ligand_id = record.get("ligandId") or record.get("id") or record.get("ligand_id")
                if ligand_id is not None:
                    unique[str(ligand_id)] = record
            selected = list(unique.values())[:limit]
            semaphore = asyncio.Semaphore(5)

            async def get_interactions(record: dict) -> list[dict]:
                ligand_id = record.get("ligandId") or record.get("id") or record.get("ligand_id")
                async with semaphore:
                    response = await client.get(f"{BASE_URL}/ligands/{ligand_id}/interactions")
                    if response.status_code in (204, 404):
                        return []
                    response.raise_for_status()
                    return _as_records(response.json())

            interactions = await asyncio.gather(*(get_interactions(item) for item in selected))

        items = [
            normalize_ligand(record, interaction_rows)
            for record, interaction_rows in zip(selected, interactions)
        ]
        return {
            "source": SOURCE_NAME,
            "query": term,
            "total": len(unique),
            "items": items,
            "retrieved_from_source": True,
            "curation_status": "not_reviewed",
            "license_notice": (
                "GtoPdb uses ODbL for the database and CC BY-SA 4.0 for contents. "
                "Attribution and share-alike obligations must be reviewed before redistribution."
            ),
            "coverage_notice": (
                "GtoPdb is a curated pharmacology resource, not a complete inventory of every "
                "peptide in existence. API access requires registration and an API key."
            ),
        }
