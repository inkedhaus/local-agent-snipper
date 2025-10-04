from __future__ import annotations

import os
import itertools
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional

from ...core.config import cfg


@dataclass(frozen=True)
class Proxy:
    """
    Represents a single proxy endpoint.
    Examples:
      http://user:pass@host:port
      socks5://host:1080
    """
    url: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.url


class ProxyManager:
    """
    Simple round-robin proxy manager.
    Sources (priority order):
      1) Explicit list passed to constructor
      2) Environment variable PROXIES (comma-separated URLs)
      3) config['scraping']['proxies'] if present (list of URLs)
    """

    def __init__(self, proxies: Optional[Iterable[str]] = None) -> None:
        discovered = list(self._discover_proxies(proxies))
        self._proxies: List[Proxy] = [Proxy(p) for p in discovered if p]
        self._cycle: Optional[Iterator[Proxy]] = itertools.cycle(self._proxies) if self._proxies else None

    def _discover_proxies(self, provided: Optional[Iterable[str]]) -> Iterable[str]:
        if provided:
            yield from provided

        env_val = os.getenv("PROXIES", "").strip()
        if env_val:
            for item in env_val.split(","):
                url = item.strip()
                if url:
                    yield url

        # config-based proxies (optional)
        scraping_cfg = cfg.get("scraping", {}) or {}
        cfg_list = scraping_cfg.get("proxies", []) or []
        for url in cfg_list:
            if isinstance(url, str) and url.strip():
                yield url.strip()

    def has_proxies(self) -> bool:
        return bool(self._proxies)

    def add_proxy(self, url: str) -> None:
        url = url.strip()
        if not url:
            return
        p = Proxy(url)
        self._proxies.append(p)
        # re-create the cycle to include the new proxy
        self._cycle = itertools.cycle(self._proxies)

    def next(self) -> Optional[Proxy]:
        if not self._cycle:
            return None
        return next(self._cycle)

    def all(self) -> List[Proxy]:
        return list(self._proxies)
