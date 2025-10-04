from __future__ import annotations

import asyncio
import random
from typing import Dict, Iterable, Optional

# Keep a compact, representative set of desktop and mobile UAs to avoid huge files/parsing issues.
# These are sufficient for initial scraping without tripping basic bot heuristics.
_USER_AGENTS: list[str] = [
    # Chrome (Windows/Mac/Linux)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Firefox (Windows/Mac/Linux)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.4; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    # Mobile (Android/iOS)
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]


_ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-US,en-CA;q=0.8,en;q=0.7",
    "en-US,en;q=0.8,es;q=0.6",
]


def random_user_agent(pool: Optional[Iterable[str]] = None) -> str:
    """
    Return a random user-agent. If a pool is provided, use it; otherwise use built-in list.
    """
    source = list(pool) if pool is not None else _USER_AGENTS
    if not source:
        # Extremely unlikely; provide a conservative fallback
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    return random.choice(source)


def random_accept_language() -> str:
    return random.choice(_ACCEPT_LANGUAGES)


def build_headers(base: Optional[Dict[str, str]] = None, user_agent: Optional[str] = None) -> Dict[str, str]:
    """
    Construct HTTP headers with randomized anti-detection fields.
    """
    headers: Dict[str, str] = {}
    if base:
        headers.update(base)

    headers.setdefault("User-Agent", user_agent or random_user_agent())
    headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8")
    headers.setdefault("Accept-Language", random_accept_language())
    headers.setdefault("Accept-Encoding", "gzip, deflate, br, zstd")
    headers.setdefault("Cache-Control", "no-cache")
    headers.setdefault("Pragma", "no-cache")
    headers.setdefault("Sec-Fetch-Dest", "document")
    headers.setdefault("Sec-Fetch-Mode", "navigate")
    headers.setdefault("Sec-Fetch-Site", "none")
    headers.setdefault("Sec-Fetch-User", "?1")
    headers.setdefault("Upgrade-Insecure-Requests", "1")
    return headers


async def human_delay(min_seconds: float = 0.25, max_seconds: float = 1.25) -> None:
    """
    Sleep a small random amount of time to simulate human pacing.
    """
    if max_seconds < min_seconds:
        max_seconds = min_seconds
    duration = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(duration)


def shuffle_params(params: Dict[str, str]) -> Dict[str, str]:
    """
    Returns a shallow-copied dict with identical content. Placeholder for future
    subtle param randomization if needed (e.g., toggling innocuous flags).
    """
    return dict(params)
