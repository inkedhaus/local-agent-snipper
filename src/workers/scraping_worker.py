from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import cfg
from ..models.listing import Listing
from ..utils.logger import get_logger
from ..scrapers.base_scraper import BaseScraper
from ..scrapers.craigslist_scraper import CraigslistScraper
from ..scrapers.offerup_scraper import OfferUpScraper
from ..scrapers.facebook_scraper import FacebookMarketplaceScraper

log = get_logger()


def _get_keywords() -> List[str]:
    scraping_cfg = cfg.get("scraping", {}) or {}
    kws = scraping_cfg.get("keywords", []) or []
    if isinstance(kws, list):
        return [str(x).strip() for x in kws if str(x).strip()]
    return []


def _get_location() -> Optional[str]:
    # For future extension; currently scrapers ignore or embed location differently.
    loc_cfg = cfg.location() or {}
    zip_code = loc_cfg.get("zip_code")
    if not zip_code:
        return None
    return str(zip_code)


async def _scrape_keyword_with_scraper(scraper: BaseScraper, keyword: str, location: Optional[str]) -> List[Dict[str, Any]]:
    try:
        return await scraper.search(keyword, location)
    except Exception as e:
        log.warning("scrape failed (scraper=%s, keyword=%s): %s", scraper.__class__.__name__, keyword, e)
        return []


async def scrape_all_keywords() -> Dict[str, List[Dict[str, Any]]]:
    """
    Run all scrapers across all configured keywords.
    Returns: mapping of scraper_name -> list of listing dicts
    """
    keywords = _get_keywords()
    location = _get_location()

    # Instantiate scrapers (tune base_url/rates as needed)
    scrapers: List[BaseScraper] = [
        CraigslistScraper(),
        OfferUpScraper(),
        FacebookMarketplaceScraper(),
    ]

    results: Dict[str, List[Dict[str, Any]]] = {s.__class__.__name__: [] for s in scrapers}
    for kw in keywords:
        # Run sequentially to be kind to sources; can parallelize if needed
        for s in scrapers:
            items = await _scrape_keyword_with_scraper(s, kw, location)
            results[s.__class__.__name__].extend(items)
    return results


def _upsert_listing(db: Session, data: Dict[str, Any]) -> Tuple[Listing, bool]:
    """
    Insert or update Listing by unique key (source, external_id).
    Returns (obj, created_flag)
    """
    source = data.get("source")
    external_id = data.get("external_id")
    if not source or not external_id:
        raise ValueError("listing requires source and external_id")

    # Try find existing
    stmt = select(Listing).where(Listing.source == source, Listing.external_id == external_id)
    obj = db.execute(stmt).scalars().first()
    created = False
    if obj is None:
        obj = Listing(
            source=source,
            external_id=external_id,
            url=str(data.get("url") or ""),
            is_active=bool(data.get("is_active", True)),
        )
        created = True

    # Update allowed fields
    for field in [
        "title",
        "description",
        "price",
        "currency",
        "url",
        "location",
        "category",
        "posted_at",
        "seller_contact",
        "is_active",
        "metadata",
    ]:
        if field in data and data[field] is not None:
            setattr(obj, field, data[field])

    obj.last_seen_at = datetime.now(timezone.utc)
    if created:
        db.add(obj)
    return obj, created


def persist_scrape_results(db: Session, results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
    """
    Save scraped listings to DB with upsert logic.
    Returns counts: {"created": X, "updated": Y}
    """
    created = 0
    updated = 0
    for scraper_name, items in results.items():
        for data in items:
            try:
                obj, was_created = _upsert_listing(db, data)
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                log.warning("persist failed (scraper=%s): %s", scraper_name, e)
    db.commit()
    return {"created": created, "updated": updated}


def run_once(db: Session) -> Dict[str, int]:
    """
    High-level single-run entrypoint:
      - run async scrape across all keywords/scrapers
      - persist to DB
    """
    log.info("Scraping worker: starting run_once()")
    results = asyncio.run(scrape_all_keywords())
    counts = persist_scrape_results(db, results)
    log.info("Scraping worker: finished (created=%d, updated=%d)", counts["created"], counts["updated"])
    return counts
