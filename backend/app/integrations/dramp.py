"""Read-only DRAMP 5.0 antimicrobial-peptide dataset discovery adapter."""
import asyncio
import re
import time
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlparse

import httpx

DOWNLOADS_PAGE_URL = "https://dramp.cpu-bioinfor.org/downloads/"
UPDATE_PAGE_URL = "https://dramp.cpu-bioinfor.org/static/update.php"
SOURCE_NAME = "Data Repository of Antimicrobial Peptides (DRAMP)"
DRAMP_ID_PATTERN = re.compile(r"(DRAMP\d{5,})", re.IGNORECASE)
CACHE_TTL_SECONDS = 21600
_CACHE: tuple[float, str, list[dict]] | None = None
_CACHE_LOCK = asyncio.Lock()


class _DownloadLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def discover_fasta_downloads(html: str) -> list[dict]:
    parser = _DownloadLinkParser()
    parser.feed(html)
    found = []
    seen = set()
    for href in parser.links:
        absolute = urljoin(DOWNLOADS_PAGE_URL, href)
        parsed = urlparse(absolute)
        filename_values = parse_qs(parsed.query).get("filename", [])
        filename = filename_values[0].split("/")[-1] if filename_values else parsed.path.split("/")[-1]
        if not filename.lower().endswith(".fasta"):
            continue
        if "download.php" not in parsed.path and "download.php" not in absolute:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        found.append({
            "url": absolute,
            "filename": filename,
            "dataset": filename[:-6],
            "contains_smiles": "smiles" in filename.casefold(),
        })
    return found


def parse_fasta_records(content: str, dataset: str, contains_smiles: bool = False) -> list[dict]:
    records = []
    header = None
    sequence_parts: list[str] = []

    def emit():
        if not header:
            return
        sequence = "".join(sequence_parts).replace(" ", "").replace("\r", "").upper()
        if not sequence:
            return
        match = DRAMP_ID_PATTERN.search(header)
        if not match:
            return
        identifier = match.group(1).upper()
        annotation = header[match.end():].strip(" |\t")
        records.append({
            "source_identifier": identifier,
            "candidate_name": identifier if contains_smiles or not annotation else annotation,
            "reported_sequence": sequence,
            "sequence": sequence,
            "sequence_type": "source_reported_peptide_sequence",
            "reported_chemical_form": annotation if contains_smiles and annotation else None,
            "chemical_form": annotation if contains_smiles and annotation else None,
            "dataset_categories": [dataset],
            "raw_header": header,
        })

    for line in content.lstrip("\ufeff").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            emit()
            header = line[1:].strip()
            sequence_parts = []
        elif header is not None:
            sequence_parts.append(line)
    emit()
    return records


def merge_records(dataset_records: list[tuple[dict, str]]) -> list[dict]:
    merged: dict[str, dict] = {}
    for record, source_url in dataset_records:
        identifier = record["source_identifier"]
        if identifier not in merged:
            merged[identifier] = {
                **record,
                "source_url": source_url,
                "dataset_categories": list(record.get("dataset_categories") or []),
            }
            continue
        existing = merged[identifier]
        existing["dataset_categories"] = sorted(set(
            existing["dataset_categories"] + list(record.get("dataset_categories") or [])
        ))
        if record.get("reported_sequence") and not existing.get("reported_sequence"):
            existing["reported_sequence"] = record["reported_sequence"]
        if record.get("reported_chemical_form"):
            existing["reported_chemical_form"] = record["reported_chemical_form"]
        if record.get("candidate_name") and existing["candidate_name"] == identifier:
            if record["candidate_name"] != identifier:
                existing["candidate_name"] = record["candidate_name"]
    return list(merged.values())


class DrampProvider:
    async def _load_snapshot(self) -> tuple[str, list[dict]]:
        global _CACHE
        async with _CACHE_LOCK:
            now = time.monotonic()
            if _CACHE and now - _CACHE[0] < CACHE_TTL_SECONDS:
                return _CACHE[1], _CACHE[2]

            timeout = httpx.Timeout(60.0, connect=8.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                downloads_page = await client.get(DOWNLOADS_PAGE_URL)
                downloads_page.raise_for_status()
                download_links = discover_fasta_downloads(downloads_page.text)
                if not download_links:
                    raise ValueError("DRAMP downloads page did not expose FASTA/FASTS files.")

                # Prefer core biological datasets and their sequence/SMILES counterparts;
                # omit activity-only exports because they duplicate the same entries.
                core_links = [
                    link for link in download_links
                    if any(token in link["filename"].casefold() for token in (
                        "general_amps", "patent_amps", "specific_amps",
                        "stability_amps", "expanded_amps", "natural_amps",
                        "synthetic_amps", "stapled_amps", "candidate_amps", "general_smiles", "patent_smiles", "specific_smiles",
                        "stability_smiles", "expanded_smiles",
                    ))
                ]
                semaphore = asyncio.Semaphore(4)

                async def fetch(link: dict):
                    async with semaphore:
                        response = await client.get(link["url"])
                        response.raise_for_status()
                        return link, response.text

                downloaded = await asyncio.gather(*(fetch(link) for link in core_links))
                parsed_records = []
                for link, content in downloaded:
                    parsed_records.extend(
                        (record, link["url"])
                        for record in parse_fasta_records(
                            content, link["dataset"], link["contains_smiles"]
                        )
                    )

                update_page = await client.get(UPDATE_PAGE_URL)
                update_page.raise_for_status()
                release = "DRAMP 5.0" if "DRAMP V5.0" in update_page.text or "DRAMP 5.0" in update_page.text else "DRAMP current release"
                snapshot = merge_records(parsed_records)
                _CACHE = (now, release, snapshot)
                return release, snapshot

    async def search(self, query: str, limit: int = 20) -> dict:
        term = query.strip()
        if len(term) < 2:
            raise ValueError("DRAMP search must contain at least two characters.")
        if not 1 <= limit <= 100:
            raise ValueError("DRAMP result limit must be between 1 and 100.")

        release, records = await self._load_snapshot()
        needle = term.casefold()
        matches = [
            record for record in records
            if needle in str(record.get("candidate_name") or "").casefold()
            or needle in str(record.get("source_identifier") or "").casefold()
            or needle in str(record.get("reported_sequence") or "").casefold()
            or needle in str(record.get("reported_chemical_form") or "").casefold()
        ]
        items = []
        for record in matches[:limit]:
            items.append({
                **record,
                "source": SOURCE_NAME,
                "source_release": release,
                "source_version": release,
                "jurisdiction": None,
                "curation_status": "not_reviewed",
                "reported_mechanism": None,
                "reported_target": None,
                "coverage_notice": (
                    "DRAMP is a manually curated antimicrobial-peptide repository. Its records "
                    "are not a complete inventory of all peptides, and sequence/SMILES records "
                    "require identity and chemical-form review before canonicalization."
                ),
            })
        return {
            "source": SOURCE_NAME,
            "query": term,
            "source_release": release,
            "snapshot_entry_count": len(records),
            "total_matches": len(matches),
            "items": items,
            "retrieved_from_source": True,
            "curation_status": "not_reviewed",
            "license_notice": "DRAMP 5.0 data are distributed under CC BY 4.0; retain attribution and source release.",
        }
