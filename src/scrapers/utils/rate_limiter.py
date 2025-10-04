from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Optional, TypeVar


T = TypeVar("T")


class AsyncRateLimiter:
    """
    Simple token-bucket async rate limiter.
    - rate: allowed operations per 'per' seconds (e.g., rate=5, per=1 means 5 ops/sec)
    - burst: optional burst capacity (defaults to rate)
    """

    def __init__(self, rate: float, per: float = 1.0, burst: Optional[float] = None) -> None:
        if rate <= 0 or per <= 0:
            raise ValueError("rate and per must be > 0")
        self.rate = float(rate)
        self.per = float(per)
        self.capacity = float(burst if burst is not None else rate)

        self._tokens = self.capacity
        self._lock = asyncio.Lock()
        self._last = asyncio.get_event_loop().time()

    def _refill(self) -> None:
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last
        if elapsed <= 0:
            return
        # Add tokens based on elapsed time
        self._tokens = min(self.capacity, self._tokens + elapsed * (self.rate / self.per))
        self._last = now

    async def acquire(self) -> None:
        """
        Wait until a token is available, then consume one.
        """
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                # compute sleep to the next token
                # tokens needed = 1 - self._tokens
                needed = 1.0 - self._tokens
                # production rate per second
                prod_per_sec = self.rate / self.per
                sleep_for = max(0.0, needed / prod_per_sec)
            await asyncio.sleep(sleep_for)

    async def __aenter__(self) -> "AsyncRateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


def rate_limited(
    limiter: AsyncRateLimiter,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator to rate-limit an async function with the given limiter.

    Usage:
        limiter = AsyncRateLimiter(rate=5, per=1.0)

        @rate_limited(limiter)
        async def fetch(...):
            ...

    """
    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        async def wrapper(*args, **kwargs) -> T:  # type: ignore[no-untyped-def]
            async with limiter:
                return await fn(*args, **kwargs)
        return wrapper
    return decorator
