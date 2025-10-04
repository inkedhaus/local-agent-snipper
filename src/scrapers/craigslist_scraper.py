from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup  # type: ignore[import-not-found]

from .base_scraper import BaseScraper
from ..utils.logger import get_logger

log = get_logger()


class CraigslistScraper(BaseScraper):
    """
    Basic Craigslist search scraper.
    Note: Craigslist uses regional subdomains (e.g., austin.craigslist.org). This base class
    targets the global domain and public search markup, but real usage should set base_url
    to your target region like https://austin.craigslist.org.
    """

    def __init__(
        self,
        base_url: str = "https://www.craigslist.org",
        timeout: float = 20.0,
    ) -> None:
        super().__init__(base_url=base_url, timeout=timeout)
        # Craigslist can tolerate ~1 req/sec but keep conservative
        self.rate_limiter.rate = 0.75

    def build_search_url(self, query: str, location: Optional[str] = None) -> str:
        # General goods-for-sale search path (sss). Location is encoded into subdomain typically, so ignored.
        path = "/search/sss"
        return self.build_url(path, {"query": query})

    def parse_listings(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        items: List[Dict[str, Any]] = []

        # Legacy/classic markup
        for li in soup.select("li.result-row"):
            a = li.select_one("a.result-title.hdrlnk")
            if not a:
                # Some variants use different link class names
                a = li.select_one("a.hdrlnk") or li.select_one("a")
            if not a or not a.get("href"):
                continue
            url = a.get("href") or ""
            title = (a.get_text(strip=True) or None)

            pid = li.get("data-pid") or ""
            price_el = li.select_one(".result-price")
            price_val: Optional[float] = None
            if price_el and price_el.get_text(strip=True).replace("$", "").replace(",", "").isdigit():
                try:
                    price_val = float(price_el.get_text(strip=True).replace("$", "").replace(",", ""))
                except Exception:
                    price_val = None

            time_el = li.select_one("time")
            posted_at: Optional[datetime] = None
            if time_el and time_el.get("datetime"):
                try:
                    posted_at = datetime.fromisoformat(time_el.get("datetime")).astimezone(timezone.utc)  # type: ignore[arg-type]
                except Exception:
                    posted_at = None

            items.append(
                {
                    "source": "craigslist",
                    "external_id": pid or url,
                    "title": title,
                    "description": None,
                    "price": price_val,
                    "currency": "USD",
                    "url": urljoin(self.base_url, url),
                    "location": None,
                    "category": None,
                    "posted_at": posted_at,
                    "seller_contact": None,
                    "is_active": True,
                    "last_seen_at": datetime.now(timezone.utc),
                    "metadata": {},
                }
            )

        # Newer/static search results sometimes use different containers
        if not items:
            for card in soup.select("li.cl-static-search-result"):
                a = card.select_one("a")
                if not a or not a.get("href"):
                    continue
                url = a.get("href") or ""
                title = (a.get_text(strip=True) or None)
                items.append(
                    {
                        "source": "craigslist",
                        "external_id": url,
                        "title": title,
                        "description": None,
                        "price": None,
                        "currency": "USD",
                        "url": urljoin(self.base_url, url),
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
            log.debug("CraigslistScraper: no items parsed (markup may have changed)")
        return items
