"""One-shot scheduler for registered, allowlisted regulatory RSS feeds.

Run from backend/: python -m app.services.regulatory_scheduler
Invoke periodically with an external scheduler (cron, Kubernetes CronJob, etc.).
"""
import asyncio
import hashlib
import json
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

import httpx
from sqlalchemy import text

from ..db import SessionLocal
from ..routers.regulatory import APPROVED_REGULATORY_DOMAINS, _parse_rss_items

MAX_SOURCES_PER_RUN = 25
MAX_FEED_BYTES = 2_000_000


async def _fetch_feed(url: str) -> list[dict]:
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(15.0, connect=4.0),
        follow_redirects=False,
        headers={
            "User-Agent": "ToolkitPeptideIntelligence/0.1",
            "Accept": "application/rss+xml, application/xml, text/xml",
        },
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        if len(response.content) > MAX_FEED_BYTES:
            raise ValueError("feed_too_large")
        content_type = response.headers.get("content-type", "").lower()
        if not any(value in content_type for value in ("xml", "rss", "atom")):
            raise ValueError("unexpected_content_type")
        return _parse_rss_items(response.content)


async def poll_due_sources(limit: int = MAX_SOURCES_PER_RUN) -> dict:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    db = SessionLocal()
    processed = 0
    succeeded = 0
    failed = 0
    try:
        for _ in range(limit):
            source = db.execute(text("""
                SELECT id, organization_id, feed_url, official_domain, polling_interval_hours
                FROM regulatory_source_registry
                WHERE is_active=true AND source_type='rss'
                  AND (next_poll_at IS NULL OR next_poll_at <= now())
                ORDER BY COALESCE(next_poll_at, to_timestamp(0)), created_at
                LIMIT 1 FOR UPDATE SKIP LOCKED
            """)).mappings().first()
            if not source:
                db.rollback()
                break
            domain = str(source["official_domain"]).lower().rstrip(".")
            host = (urlsplit(source["feed_url"]).hostname or "").lower().rstrip(".")
            valid_domain = domain in APPROVED_REGULATORY_DOMAINS and (
                host == domain or host.endswith("." + domain)
            )
            run = db.execute(text("""
                INSERT INTO regulatory_source_poll_runs
                  (organization_id,source_id,trigger_type,status)
                VALUES(:org,:source,'scheduled','running') RETURNING id
            """), {"org": source["organization_id"], "source": source["id"]}).scalar_one()
            # Reserve the schedule before network I/O so overlapping scheduler instances do not duplicate work.
            db.execute(text("""
                UPDATE regulatory_source_registry
                SET next_poll_at=now() + make_interval(hours => polling_interval_hours)
                WHERE id=:id
            """), {"id": source["id"]})
            db.commit()
            processed += 1
            try:
                if not valid_domain:
                    raise ValueError("domain_not_allowlisted")
                items = await _fetch_feed(source["feed_url"])
                inserted = 0
                for item in items:
                    digest = hashlib.sha256(
                        json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
                    ).hexdigest()
                    row = db.execute(text("""
                        INSERT INTO regulatory_source_observations
                          (organization_id,source_id,external_identifier,item_title,item_url,
                           published_at,summary,content_hash,raw_metadata)
                        VALUES(:org,:source,:guid,:title,:url,:published,:summary,:hash,CAST(:metadata AS jsonb))
                        ON CONFLICT(source_id,external_identifier) DO NOTHING RETURNING id
                    """), {
                        "org": source["organization_id"], "source": source["id"],
                        "guid": item["guid"], "title": item["title"], "url": item["url"],
                        "published": item["published"], "summary": item["summary"],
                        "hash": digest, "metadata": json.dumps(item),
                    }).first()
                    if row:
                        inserted += 1
                db.execute(text("""
                    UPDATE regulatory_source_poll_runs
                    SET status='success',items_seen=:seen,items_added=:added,finished_at=now()
                    WHERE id=:id
                """), {"seen": len(items), "added": inserted, "id": run})
                db.execute(text("""
                    UPDATE regulatory_source_registry
                    SET last_polled_at=now(),last_poll_status='success'
                    WHERE id=:id
                """), {"id": source["id"]})
                db.execute(text("""
                    INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
                    VALUES(NULL,:org,'regulatory_source_scheduled_poll','regulatory_source',:source,
                      jsonb_build_object('items_seen',:seen,'items_added',:added,'run_id',:run))
                """), {"org": source["organization_id"], "source": source["id"],
                       "seen": len(items), "added": inserted, "run": str(run)})
                db.commit()
                succeeded += 1
            except Exception as exc:
                db.rollback()
                db.execute(text("""
                    UPDATE regulatory_source_poll_runs
                    SET status='error',error_code=:error,finished_at=now()
                    WHERE id=:id
                """), {"error": type(exc).__name__[:100], "id": run})
                db.execute(text("""
                    UPDATE regulatory_source_registry
                    SET last_polled_at=now(),last_poll_status='error'
                    WHERE id=:id
                """), {"id": source["id"]})
                db.commit()
                failed += 1
        return {"processed": processed, "succeeded": succeeded, "failed": failed}
    finally:
        db.close()


def main():
    result = asyncio.run(poll_due_sources())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
