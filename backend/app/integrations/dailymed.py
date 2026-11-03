"""Read-only adapter for NLM DailyMed Structured Product Label (SPL) metadata."""
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

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


def extract_mechanism_of_action(spl_xml: str) -> dict:
    """Extract only the designated SPL 12.1 MOA section; never infer missing text."""
    try:
        root = ET.fromstring(spl_xml)
    except ET.ParseError as exc:
        raise ValueError("DailyMed returned malformed SPL XML.") from exc

    sections = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].lower() != "section":
            continue
        children = list(element)
        code_node = next(
            (child for child in children if child.tag.rsplit("}", 1)[-1].lower() == "code"),
            None,
        )
        title_node = next(
            (child for child in children if child.tag.rsplit("}", 1)[-1].lower() == "title"),
            None,
        )
        code = (code_node.attrib.get("code") if code_node is not None else None)
        title = " ".join("".join(title_node.itertext()).split()) if title_node is not None else None
        title_normalized = (title or "").casefold()
        if code != "43679-0" and not (
            title_normalized.startswith("12.1") and "mechanism of action" in title_normalized
        ):
            continue

        text_node = next(
            (child for child in children if child.tag.rsplit("}", 1)[-1].lower() == "text"),
            None,
        )
        if text_node is None:
            text_nodes = [
                node for node in element.iter()
                if node is not element and node.tag.rsplit("}", 1)[-1].lower() == "text"
            ]
            text_value = " ".join(" ".join("".join(node.itertext()).split()) for node in text_nodes)
        else:
            text_value = " ".join("".join(text_node.itertext()).split())
        if text_value:
            sections.append({"loinc_code": code or "title_fallback", "title": title, "text": text_value})

    if not sections:
        return {
            "found": False,
            "mechanism_text": None,
            "section_code": None,
            "section_title": None,
            "extraction_status": "section_not_present",
            "notice": "No explicit 12.1 Mechanism of Action section was found in this SPL. No mechanism was inferred.",
        }

    unique_text = list(dict.fromkeys(section["text"] for section in sections))
    return {
        "found": True,
        "mechanism_text": "\\n\\n".join(unique_text)[:12000],
        "section_code": "43679-0",
        "section_title": next((section["title"] for section in sections if section["title"]), "12.1 Mechanism of Action"),
        "extraction_status": "extracted_from_explicit_spl_section",
        "evidence_level": "source_asserted",
        "notice": "Extracted from a current DailyMed SPL. DailyMed presence is not proof of FDA approval, and current SPL text may differ from the last FDA-approved labeling. Curator review and product-level regulatory cross-check are required.",
    }


class DailyMedProvider:
    async def get_mechanism_of_action(self, set_id: str) -> dict:
        identifier = set_id.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", identifier):
            raise ValueError("DailyMed SPL Set ID must be a UUID.")
        timeout = httpx.Timeout(25.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}/spls/{identifier}.xml")
            if response.status_code == 404:
                return {
                    "set_id": identifier,
                    "found": False,
                    "mechanism_text": None,
                    "extraction_status": "spl_not_found",
                    "source": "DailyMed",
                }
            response.raise_for_status()
            xml_text = response.text

        extracted = extract_mechanism_of_action(xml_text)
        root = ET.fromstring(xml_text)
        title_node = next(
            (node for node in root.iter() if node.tag.rsplit("}", 1)[-1].lower() == "title"),
            None,
        )
        version_node = next(
            (node for node in root.iter() if node.tag.rsplit("}", 1)[-1].lower() == "versionnumber"),
            None,
        )
        return {
            "set_id": identifier,
            "spl_title": " ".join("".join(title_node.itertext()).split()) if title_node is not None else None,
            "spl_version": version_node.attrib.get("value") if version_node is not None else None,
            **extracted,
            "source": "DailyMed",
            "source_url": f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={identifier}",
            "label_api_url": f"{BASE_URL}/spls/{identifier}.xml",
            "jurisdiction": "US",
            "curation_status": "not_reviewed",
            "approval_status": "not_determined_from_dailymed",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

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
