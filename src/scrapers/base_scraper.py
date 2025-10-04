from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlencode

import httpx

from .utils.anti_detection import build_headers, human_delay
from .utils.proxy_manager import ProxyManager
from .utils.rate_limiter import AsyncRateLimiter


class BaseScraper(ABC):
    """
    Async base scraper with:
      - Simple rate limiting
      - Optional proxy rotation
      - Anti-detection headers and human delays
    Subclasses implement:
      - build_search_url
      - parse_listings
    """

    def __init__(
        self,
        base_url: str,
        rate_limiter: Optional[AsyncRateLimiter] = None,
        proxy_manager: Optional[ProxyManager] = None,
        timeout: float = 20.0,
        extra_headers: Optional[Dict[str, str]] = None,
        human_delay_range: tuple[float, float] = (0.25, 1.25),
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter or AsyncRateLimiter(rate=1, per=1.0)
        self.proxy_manager = proxy_manager or ProxyManager()
        self.timeout = timeout
        self.extra_headers = extra_headers or {}
        self.human_delay_range = human_delay_range
        self._closed = True

    async def __aenter__(self) -> "BaseScraper":
        self._closed = False
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self._closed = True

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        # Rate limit + human delay
        await self.rate_limiter.acquire()
        await human_delay(*self.human_delay_range)

        req_headers = build_headers(self.extra_headers, None)
        if headers:
            req_headers.update(headers)

        # Optional proxy rotation: create a short-lived client per request
        proxy_url: Optional[str] = None
        if self.proxy_manager and self.proxy_manager.has_proxies():
            proxy = self.proxy_manager.next()
            proxy_url = proxy.url if proxy else None

        async with httpx.AsyncClient(
            timeout=self.timeout, follow_redirects=True, proxies=proxy_url
        ) as client:
            resp = await client.request(method, url, params=params, headers=req_headers)
            resp.raise_for_status()
            return resp

    async def fetch_text(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        resp = await self._request("GET", url, params=params)
        return resp.text

    def build_url(self, path: str, query: Optional[Dict[str, Any]] = None) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if query:
            return f"{url}?{urlencode(query, doseq=True)}"
        return url

    @abstractmethod
    def build_search_url(self, query: str, location: Optional[str] = None) -> str:
        """
        Return a fully-composed search URL for a given query (and optional location).
        """
        raise NotImplementedError

    @abstractmethod
    def parse_listings(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML and return a list of normalized listing dicts with fields
        that map to src/models/listing.py.
        Example keys:
          - source, external_id, title, description, price, currency, url,
            location, category, posted_at, seller_contact, metadata
        """
        raise NotImplementedError

    async def search(
        self, query: str, location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Convenience: build the search URL, fetch it, and parse listings.
        """
        url = self.build_search_url(query, location)
        html = await self.fetch_text(url)
        return self.parse_listings(html)
