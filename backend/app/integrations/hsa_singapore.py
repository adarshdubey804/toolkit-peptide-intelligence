"""Read-only HSA Singapore registered therapeutic products dataset adapter."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

BASE_URL = "https://data.gov.sg/api/action"
DATASET_ID = "d_767279312753558cbf19d48344577084"
DATASET_URL = "https://data.gov.sg/datasets/d_767279312753558cbf19d48344577084/view"
SOURCE_NAME = "Singapore HSA Register of Therapeutic Products"
LICENSE_NOTICE = (
    "Health Sciences Authority. Listing of Registered Therapeutic Products. "
    "data.gov.sg Open Data Licence; free for personal or commercial use."
)


def normalize_product(record: dict, source_version: str | None = None) -> dict | None:
    licence_no = str(record.get("LicenceNo") or "").strip()
    if not licence_no:
        return None
    product_name = str(record.get("Productname") or "").strip() or None
    active_ingredients = str(record.get("Activeingredients") or "").strip() or None
    return {
        "source": SOURCE_NAME,
        "source_identifier": licence_no,
        "source_version": source_version or f"data.gov.sg resource {DATASET_ID}",
        "source_url": DATASET_URL,
        "source_locator": f"HSA therapeutic product licence {licence_no}",
        "candidate_name": active_ingredients or product_name or licence_no,
        "product_name": product_name,
        "license_number": licence_no,
        "marketing_authorisation_holder": str(record.get("Licenseholder") or "").strip() or None,
        "approval_date": str(record.get("Approvaldate") or "").strip() or None,
        "forensic_classification": str(record.get("Forensicclassification") or "").strip() or None,
        "atc_code": str(record.get("ATCCode") or "").strip() or None,
        "dosage_form": str(record.get("Dosageform") or "").strip() or None,
        "route_of_administration": str(record.get("RouteofAdministration") or "").strip() or None,
        "manufacturer": str(record.get("Manufacturer") or "").strip() or None,
        "manufacturer_country": str(record.get("Countryofmanufacturer") or "").strip() or None,
        "active_ingredients": active_ingredients,
        "strength": str(record.get("Strength") or "").strip() or None,
        "jurisdiction": "SG",
        "source_status": "registered_product_snapshot_observed",
        "status_notice": (
            "This record comes from HSA's periodically updated public dataset. It is not a live "
            "status check; verify current registration and post-registration actions in HSA Infosearch."
        ),
        "curation_status": "not_reviewed",
        "license": "Open Data Licence (data.gov.sg)",
        "license_notice": LICENSE_NOTICE,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "raw_source_record": record,
    }


class HsaSingaporeProvider:
    async def search_products(self, query: str, limit: int = 20, offset: int = 0) -> dict:
        term = query.strip()
        if len(term) < 2:
            raise ValueError("HSA product search must contain at least two characters.")
        if not 1 <= limit <= 50:
            raise ValueError("HSA product result limit must be between 1 and 50.")
        if offset < 0 or offset > 10000:
            raise ValueError("HSA product offset is outside the permitted range.")

        timeout = httpx.Timeout(30.0, connect=8.0)
        headers = {"Accept": "application/json", "User-Agent": "ToolkitPeptideIntelligence/1.0"}
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            response = await client.get(
                f"{BASE_URL}/datastore_search",
                params={"resource_id": DATASET_ID, "q": term, "limit": limit, "offset": offset},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("success") is not True:
                raise ValueError("HSA data.gov.sg API returned an unsuccessful response.")
            result = payload.get("result")
            if not isinstance(result, dict):
                raise ValueError("HSA data.gov.sg API response did not contain a result object.")
            rows = result.get("records")
            if not isinstance(rows, list):
                raise ValueError("HSA data.gov.sg API records field was not an array.")

            source_version = f"data.gov.sg resource {DATASET_ID}"
            try:
                metadata_response = await client.get(
                    f"{BASE_URL}/resource_show",
                    params={"id": DATASET_ID},
                )
                metadata_response.raise_for_status()
                metadata_payload = metadata_response.json()
                metadata = metadata_payload.get("result") if isinstance(metadata_payload, dict) else None
                if isinstance(metadata, dict):
                    modified = metadata.get("last_modified") or metadata.get("metadata_modified")
                    if modified:
                        source_version = f"HSA dataset last modified {modified}"
            except (httpx.HTTPError, ValueError, TypeError):
                pass

        items = [
            normalized
            for row in rows
            if isinstance(row, dict)
            if (normalized := normalize_product(row, source_version))
        ]
        return {
            "source": SOURCE_NAME,
            "query": term,
            "total": result.get("total", len(items)),
            "limit": limit,
            "offset": offset,
            "items": items,
            "source_version": source_version,
            "retrieved_from_source": True,
            "curation_status": "not_reviewed",
            "license_notice": LICENSE_NOTICE,
            "coverage_notice": (
                "This is a periodically updated snapshot of registered therapeutic products in Singapore, "
                "not a live register. HSA reports an update cadence of approximately six months. "
                "Current product registration and post-registration actions must be verified in HSA Infosearch."
            ),
        }
