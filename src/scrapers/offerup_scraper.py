from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup  # type: ignore[import-not-found]

from .base_scraper import BaseScraper
from ..utils.logger import get_logger

log = get_logger()


class OfferUpScraper(BaseScraper):
    """
    Lightweight OfferUp scraper for public search results.
    Note: Real pages may lazy-load items; this parser targets basic static markup.
    """

    def __init__(self, base_url: str = "https://offerup.com", timeout: float = 20.0) -> None:
        super().__init__(base_url=base_url, timeout=timeout)
        self.rate_limiter.rate = 0.75

    def build_search_url(self, query: str, location: Optional[str] = None) -> str:
        # OfferUp search path typically /search?q=...
        return self.build_url("/search", {"q": query})

    def parse_listings(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        items: List[Dict[str, Any]] = []

        # Try common card containers
        for card in soup.select("[data-qa='feed-item-card'], a[href*='/item/detail/']"):
            a = card if card.name == "a" else card.find("a")
            if not a or not a.get("href"):
                continue
            href = a.get("href") or ""
            title_el = card.select_one("[data-qa='item-title'], .styles__Title") or a
            title = title_el.get_text(strip=True) if title_el else None

            price_el = card.select_one("[data-qa='item-price'], .styles__Price")
            price_val: Optional[float] = None
            if price_el:
                txt = price_el.get_text(strip=True).replace("$", "").replace(",", "")
                try:
                    price_val = float(txt)
                except Exception:
                    price_val = None

            external_id = href.rstrip("/").split("/")[-1] or href
            items.append(
                {
                    "source": "offerup",
                    "external_id": external_id,
                    "title": title or None,
                    "description": None,
                    "price": price_val,
                    "currency": "USD",
                    "url": urljoin(self.base_url, href),
                    "location": None,
                    "category": None,
                    "posted_at": None,
                    "seller_contact": None,
                    "is_active": True,
                    "last_seen_at": datetime.now(timezone.utc),
                    "metadata": {},
                }
            )

        if not items:
            log.debug("OfferUpScraper: no items parsed (markup may be dynamic)")
        return items
