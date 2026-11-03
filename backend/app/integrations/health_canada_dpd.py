"""Read-only adapter for Health Canada's Drug Product Database (DPD)."""
import asyncio

import httpx

BASE_URL = "https://health-products.canada.ca/api/drug"


def normalize_product(product: dict, ingredients: list[dict], status: list[dict] | None = None,
                     forms: list[dict] | None = None, routes: list[dict] | None = None) -> dict:
    """Preserve Health Canada product identifiers and source status without inference."""
    return {
        "drug_code": product.get("drug_code"),
        "drug_identification_number": product.get("drug_identification_number"),
        "brand_name": product.get("brand_name"),
        "company_name": product.get("company_name"),
        "class_name": product.get("class_name"),
        "descriptor": product.get("descriptor"),
        "last_update_date": product.get("last_update_date"),
        "active_ingredients": [
            {
                "ingredient_name": item.get("ingredient_name"),
                "strength": item.get("strength"),
                "strength_unit": item.get("strength_unit"),
                "dosage_value": item.get("dosage_value"),
                "dosage_unit": item.get("dosage_unit"),
            }
            for item in ingredients
        ],
        "source_status_records": status or [],
        "dosage_forms": forms or [],
        "routes": routes or [],
        "source": "Health Canada Drug Product Database",
        "jurisdiction": "CA",
        "curation_status": "not_reviewed",
        "source_url": (
            "https://health-products.canada.ca/dpd-bdpp/index-eng.jsp"
        ),
        "status_notice": (
            "Health Canada DPD distinguishes approved, marketed, dormant and multiple "
            "cancelled/interim-order states. Source status is retained verbatim; do not "
            "collapse it into a generic FDA-approved flag."
        ),
    }


class HealthCanadaDpdProvider:
    async def search_by_ingredient(self, ingredient: str, limit: int = 20) -> dict:
        term = ingredient.strip()
        if len(term) < 2:
            raise ValueError("Health Canada ingredient search must contain at least two characters.")
        if not 1 <= limit <= 50:
            raise ValueError("Health Canada DPD result limit must be between 1 and 50.")

        timeout = httpx.Timeout(25.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(
                f"{BASE_URL}/activeingredient/",
                params={"ingredientname": term, "lang": "en", "type": "json"},
            )
            response.raise_for_status()
            ingredient_rows = response.json()
            if not isinstance(ingredient_rows, list):
                raise ValueError("Health Canada DPD returned an unexpected active-ingredient payload.")

            by_code: dict[str, list[dict]] = {}
            for row in ingredient_rows:
                code = row.get("drug_code")
                if code is not None:
                    by_code.setdefault(str(code), []).append(row)

            codes = list(by_code)[:limit]

            semaphore = asyncio.Semaphore(5)

            async def fetch_product(code: str) -> dict | None:
                async with semaphore:
                    async def get_list(endpoint: str) -> list[dict]:
                        result = await client.get(
                            f"{BASE_URL}/{endpoint}/",
                            params={"id": code, "lang": "en", "type": "json"},
                        )
                        if result.status_code == 404:
                            return []
                        result.raise_for_status()
                        payload = result.json()
                        if payload is None:
                            return []
                        if isinstance(payload, dict):
                            return [payload]
                        if not isinstance(payload, list):
                            raise ValueError(f"Unexpected Health Canada DPD {endpoint} payload.")
                        return payload

                    product_rows, status_rows, form_rows, route_rows = await asyncio.gather(
                        get_list("drugproduct"),
                        get_list("status"),
                        get_list("form"),
                        get_list("route"),
                    )
                    if not product_rows:
                        return None
                    return normalize_product(
                        product_rows[0], by_code.get(code, []),
                        status_rows, form_rows, route_rows,
                    )

            products = await asyncio.gather(*(fetch_product(code) for code in codes))

        items = [item for item in products if item is not None]
        return {
            "source": "Health Canada Drug Product Database",
            "query": term,
            "jurisdiction": "CA",
            "total_active_ingredient_rows": len(ingredient_rows),
            "products_returned": len(items),
            "items": items,
            "retrieved_from_source": True,
            "curation_status": "not_reviewed",
            "coverage_notice": (
                "The DPD includes human pharmaceutical and biological products as well as "
                "other product classes. This ingredient-name search is not a complete global "
                "peptide inventory. An empty result is not proof of non-authorization."
            ),
        }
