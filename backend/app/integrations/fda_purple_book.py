"""Read-only FDA Purple Book monthly snapshot discovery adapter.

The Purple Book is a downloadable monthly dataset rather than a JSON API.
The latest snapshot includes all listed FDA-licensed biological products.
"""
import csv
import io
import re

import httpx

DOWNLOADS_PAGE_URL = "https://purplebooksearch.fda.gov/downloads"
CSV_URL_PATTERN = re.compile(
    r'href=["\'](https://www\.accessdata\.fda\.gov/drugsatfda_docs/PurpleBook/'
    r'(\d{4})/purplebook-search-[^"\']+?-data-download\.csv)["\']',
    re.IGNORECASE,
)

FIELD_MAP = {
    "applicant": "Applicant",
    "bla_number": "BLA Number",
    "proprietary_name": "Proprietary Name",
    "proper_name": "Proper Name",
    "license_type": "License Type",
    "strength": "Strength",
    "dosage_form": "Dosage Form",
    "route_of_administration": "Route of Administration",
    "marketing_status": "Marketing Status",
    "licensure": "Licensure",
    "approval_date": "Approval Date",
    "product_number": "Product Number",
    "center": "Center",
    "reference_product_proper_name": "Ref. Product Proper Name",
    "reference_product_proprietary_name": "Ref. Product Proprietary Name",
    "submission_type": "Submission Type",
}


def discover_latest_csv_url(html: str) -> str:
    matches = CSV_URL_PATTERN.findall(html)
    if not matches:
        raise ValueError("No FDA Purple Book monthly CSV links were found.")
    by_year: dict[str, list[str]] = {}
    for url, year in matches:
        by_year.setdefault(year, []).append(url)
    latest_year = max(by_year)
    return by_year[latest_year][-1]


def parse_purple_book_csv(content: str) -> list[dict]:
    """Parse the complete product snapshot (the last matching header table)."""
    rows = list(csv.reader(io.StringIO(content.lstrip("\ufeff"))))
    header_candidates = []
    required = {"BLA Number", "Proper Name", "Product Number", "License Type"}
    for index, row in enumerate(rows):
        normalized = {cell.strip() for cell in row if cell and cell.strip()}
        if required.issubset(normalized):
            header_candidates.append(index)
    if not header_candidates:
        raise ValueError("Purple Book CSV does not contain the expected product table header.")

    header_index = header_candidates[-1]
    headers = [cell.strip() for cell in rows[header_index]]
    products = []
    for row in rows[header_index + 1:]:
        if not row or not any(cell.strip() for cell in row):
            continue
        values = (row + [""] * len(headers))[:len(headers)]
        record = {headers[i]: values[i].strip() for i in range(len(headers)) if headers[i]}
        if not record.get("BLA Number") or not record.get("Proper Name"):
            continue
        products.append({
            key: record.get(source_field) or None
            for key, source_field in FIELD_MAP.items()
        } | {"raw_source_row": record})
    return products


def normalize_product(record: dict, source_csv_url: str) -> dict:
    bla = record.get("bla_number")
    product_number = record.get("product_number")
    stable_id = f"{bla or 'unknown-bla'}:{product_number or record.get('proper_name') or 'unknown-product'}"
    return {
        "source_identifier": stable_id,
        "bla_number": bla,
        "product_number": product_number,
        "proper_name": record.get("proper_name"),
        "proprietary_name": record.get("proprietary_name"),
        "applicant": record.get("applicant"),
        "license_type": record.get("license_type"),
        "strength": record.get("strength"),
        "dosage_form": record.get("dosage_form"),
        "route_of_administration": record.get("route_of_administration"),
        "marketing_status": record.get("marketing_status"),
        "licensure": record.get("licensure"),
        "approval_date": record.get("approval_date"),
        "center": record.get("center"),
        "reference_product_proper_name": record.get("reference_product_proper_name"),
        "reference_product_proprietary_name": record.get("reference_product_proprietary_name"),
        "submission_type": record.get("submission_type"),
        "raw_source_row": record.get("raw_source_row") or {},
        "source": "FDA Purple Book",
        "jurisdiction": "US",
        "source_url": source_csv_url,
        "source_page_url": DOWNLOADS_PAGE_URL,
        "curation_status": "not_reviewed",
        "coverage_notice": (
            "Purple Book records FDA-licensed biological products regulated by CDER and CBER, "
            "including reference products and biosimilars. A record is not proof that the item "
            "is a peptide; peptide identity and exact product mapping require curator review."
        ),
    }


class FdaPurpleBookProvider:
    async def search(self, query: str, limit: int = 20) -> dict:
        term = query.strip()
        if len(term) < 2:
            raise ValueError("Purple Book search must contain at least two characters.")
        if not 1 <= limit <= 100:
            raise ValueError("Purple Book result limit must be between 1 and 100.")

        timeout = httpx.Timeout(45.0, connect=8.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            page = await client.get(DOWNLOADS_PAGE_URL)
            page.raise_for_status()
            csv_url = discover_latest_csv_url(page.text)
            response = await client.get(csv_url)
            response.raise_for_status()
            content = response.content.decode("utf-8-sig", errors="replace")

        products = parse_purple_book_csv(content)
        needle = term.casefold()
        matched = [
            normalize_product(row, csv_url)
            for row in products
            if any(
                needle in str(row.get(field) or "").casefold()
                for field in ("proper_name", "proprietary_name", "applicant", "bla_number")
            )
        ][:limit]
        return {
            "source": "FDA Purple Book",
            "query": term,
            "jurisdiction": "US",
            "snapshot_url": csv_url,
            "snapshot_product_count": len(products),
            "total_matches_in_snapshot": sum(
                1 for row in products
                if any(needle in str(row.get(field) or "").casefold()
                       for field in ("proper_name", "proprietary_name", "applicant", "bla_number"))
            ),
            "items": matched,
            "retrieved_from_source": True,
            "curation_status": "not_reviewed",
            "coverage_notice": (
                "This is a monthly snapshot of FDA-licensed biological products, not a complete "
                "peptide inventory. Purple Book product inclusion does not establish peptide identity."
            ),
        }
