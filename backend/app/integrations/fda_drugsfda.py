"""Read-only adapter for the FDA Drugs@FDA openFDA dataset."""
import httpx

BASE_URL = "https://api.fda.gov/drug/drugsfda.json"


def normalize_application(record: dict) -> dict:
    """Normalize an application while preserving product and submission distinctions."""
    products = []
    for product in record.get("products") or []:
        ingredients = product.get("active_ingredients") or []
        products.append({
            "product_number": product.get("product_number"),
            "dosage_form": product.get("dosage_form"),
            "route": product.get("route"),
            "marketing_status": product.get("marketing_status"),
            "active_ingredients": [
                {"name": item.get("name"), "strength": item.get("strength")}
                for item in ingredients
            ],
        })

    submissions = []
    for submission in record.get("submissions") or []:
        submissions.append({
            "submission_type": submission.get("submission_type"),
            "submission_number": submission.get("submission_number"),
            "submission_status": submission.get("submission_status"),
            "submission_status_date": submission.get("submission_status_date"),
            "submission_class_code": submission.get("submission_class_code"),
            "review_priority": submission.get("review_priority"),
        })

    approved_actions = [
        item for item in submissions
        if item.get("submission_status") == "AP"
    ]
    application_number = record.get("application_number")
    return {
        "application_number": application_number,
        "sponsor_name": record.get("sponsor_name"),
        "products": products,
        "submissions": submissions,
        "approved_submission_actions_observed": approved_actions,
        "approval_state_interpretation": (
            "approved_submission_action_present_in_source_record"
            if approved_actions else "no_approved_action_observed_in_returned_record"
        ),
        "source_url": (
            "https://api.fda.gov/drug/drugsfda.json"
            f"?search=application_number:{application_number}"
            if application_number else "https://api.fda.gov/drug/drugsfda.json"
        ),
        "source": "FDA Drugs@FDA via openFDA",
        "jurisdiction": "US",
        "curation_status": "not_reviewed",
        "identity_notice": "An application may contain multiple products and strengths. Review each product and submission; this result is not a peptide identity or final current marketing-status determination.",
    }


class FdaDrugsFdaProvider:
    async def search_by_ingredient(self, ingredient: str, limit: int = 20, api_key: str | None = None) -> dict:
        term = ingredient.strip()
        if len(term) < 3:
            raise ValueError("Ingredient search must contain at least three characters.")
        if not 1 <= limit <= 99:
            raise ValueError("FDA Drugs@FDA result limit must be between 1 and 99.")

        # The term is escaped as a Lucene phrase and passed as a query parameter;
        # httpx performs URL encoding.
        phrase = term.replace("\\", "\\\\").replace('"', '\\"')
        params = {
            "search": f'products.active_ingredients.name:"{phrase}"',
            "limit": limit,
        }
        if api_key:
            params["api_key"] = api_key

        timeout = httpx.Timeout(25.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(BASE_URL, params=params)
            if response.status_code == 404:
                return {"source": "FDA Drugs@FDA via openFDA", "query": term, "total": 0, "items": []}
            response.raise_for_status()
            payload = response.json()

        results = payload.get("results") or []
        return {
            "source": "FDA Drugs@FDA via openFDA",
            "query": term,
            "total": (payload.get("meta") or {}).get("results", {}).get("total", len(results)),
            "items": [normalize_application(item) for item in results],
            "retrieved_from_source": True,
            "curation_status": "not_reviewed",
            "coverage_notice": "Drugs@FDA covers most FDA-approved human drug products, but does not include every CBER-regulated biological product or non-approved product. A missing result is not evidence of non-approval.",
        }
