from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from bs4 import BeautifulSoup  # type: ignore[import-not-found]

from .base_scraper import BaseScraper
from .utils.anti_detection import build_headers
from ..utils.logger import get_logger

log = get_logger()


class FacebookMarketplaceScraper(BaseScraper):
    """
    NOTE:
    - Facebook Marketplace typically requires authentication and uses dynamic content.
    - This scraper is a placeholder foundation that returns an empty result set by default.
    - If you later add authenticated session cookies or a headless browser, you can extend parse_listings.
    """

    def __init__(
        self,
        rate_per_sec: float = 0.5,
        timeout: float = 20.0,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        base_url = "https://www.facebook.com/marketplace"
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            extra_headers=extra_headers or {"Referer": "https://www.facebook.com/"},
        )
        # Adjust default rate; FB can be strict
        self.rate_limiter.rate = rate_per_sec

    def build_search_url(self, query: str, location: Optional[str] = None) -> str:
        # FB uses /marketplace/search/?query=...
        # location handling is non-trivial without auth; ignore for now.
        path = "search/"
        q: Dict[str, Any] = {"query": query}
        return self.build_url(path, q)

    def parse_listings(self, html: str) -> List[Dict[str, Any]]:
        # Heavily JS-driven site; parsing static HTML often yields nothing.
        # Keep placeholder implementation.
        soup = BeautifulSoup(html, "html.parser")
        items: List[Dict[str, Any]] = []

        # Example: if future HTML exposes products as <a> with data attributes:
        # for node in soup.select("a[href*='/marketplace/item/']"):
        #     title = (node.get_text(strip=True) or None)
        #     href = node.get("href")
        #     external_id = None
        #     if href:
        #         # Extract ID if present in URL
        #         parts = href.split("/")
        #         for p in parts:
        #             if p.isdigit():
        #                 external_id = p
        #                 break
        #     if not href or not external_id:
        #         continue
        #     items.append({
        #         "source": "facebook",
        #         "external_id": external_id,
        #         "title": title,
        #         "url": f"https://www.facebook.com{href}",
        #         "is_active": True,
        #         "last_seen_at": datetime.now(timezone.utc),
        #         "metadata": {},
        #     })

        if not items:
            log.debug("FacebookMarketplaceScraper: no static items parsed (expected without auth)")
        return items
