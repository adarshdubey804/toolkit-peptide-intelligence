import httpx

BASE_URL = "https://clinicaltrials.gov/api/v2"
FIELDS = ",".join([
    "NCTId", "BriefTitle", "OfficialTitle", "OverallStatus", "StudyType",
    "Phase", "StartDate", "CompletionDate", "LeadSponsorName",
    "BriefSummary", "Condition", "InterventionName",
])


def _module(study: dict, module_name: str) -> dict:
    return (study.get("protocolSection") or {}).get(module_name) or {}


def normalize_study(study: dict) -> dict:
    identification = _module(study, "identificationModule")
    status = _module(study, "statusModule")
    design = _module(study, "designModule")
    sponsor = _module(study, "sponsorCollaboratorsModule")
    description = _module(study, "descriptionModule")
    conditions = _module(study, "conditionsModule")
    interventions_module = _module(study, "armsInterventionsModule")

    nct_id = identification.get("nctId")
    start = status.get("startDateStruct") or {}
    completion = status.get("completionDateStruct") or {}
    interventions = interventions_module.get("interventions") or []

    return {
        "nct_id": nct_id,
        "title": identification.get("briefTitle"),
        "official_title": identification.get("officialTitle"),
        "overall_status": status.get("overallStatus"),
        "study_type": design.get("studyType"),
        "phases": design.get("phases") or [],
        "start_date": start.get("date"),
        "completion_date": completion.get("date"),
        "lead_sponsor": (sponsor.get("leadSponsor") or {}).get("name"),
        "brief_summary": description.get("briefSummary"),
        "conditions": conditions.get("conditions") or [],
        "interventions": [
            {"name": item.get("name"), "type": item.get("type")}
            for item in interventions if item.get("name")
        ],
        "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else None,
        "source": "ClinicalTrials.gov",
        "retrieved_from_source": True,
        "curation_status": "not_reviewed",
    }


class ClinicalTrialsProvider:
    async def search(self, query: str, limit: int = 10, page_token: str | None = None) -> dict:
        params = {
            "query.term": query,
            "format": "json",
            "pageSize": limit,
            "countTotal": "true",
            "fields": FIELDS,
        }
        if page_token:
            params["pageToken"] = page_token

        timeout = httpx.Timeout(20.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}/studies", params=params)
            response.raise_for_status()
            payload = response.json()

        studies = payload.get("studies") or []
        return {
            "source": "ClinicalTrials.gov",
            "query": query,
            "total": payload.get("totalCount"),
            "next_page_token": payload.get("nextPageToken"),
            "items": [normalize_study(study) for study in studies],
        }
