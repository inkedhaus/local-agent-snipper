from __future__ import annotations

import asyncio
import math
import random
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Iterable, Iterator, Optional, Sequence, Tuple, TypeVar


T = TypeVar("T")


def utc_now() -> datetime:
    """
    Return current UTC time as timezone-aware datetime.
    """
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware in UTC.
    If naive, assume it's UTC and set tzinfo.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def slugify(value: str, allow_unicode: bool = False) -> str:
    """
    Simple slugify implementation (Django-inspired) without external deps.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        if isinstance(value, (int,)):
            return int(value)
        s = str(value).strip().replace(",", "")
        return int(float(s)) if s else default
    except Exception:
        return default


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if isinstance(value, (float, int)):
            return float(value)
        s = str(value).strip().replace(",", "").replace("$", "")
        return float(s) if s else default
    except Exception:
        return default


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def chunked(iterable: Sequence[T] | Iterable[T], size: int) -> Iterator[list[T]]:
    """
    Yield lists of length size (last may be shorter).
    Works with sequences and generic iterables.
    """
    if size <= 0:
        raise ValueError("size must be > 0")
    if isinstance(iterable, Sequence):
        for i in range(0, len(iterable), size):
            yield list(iterable[i : i + size])
    else:
        buf: list[T] = []
        for item in iterable:
            buf.append(item)
            if len(buf) >= size:
                yield buf
                buf = []
        if buf:
            yield buf


def jitter(base_seconds: float, jitter_ratio: float = 0.2) -> float:
    """
    Add +/- jitter to a base delay.
    """
    jr = abs(jitter_ratio)
    return max(0.0, base_seconds * (1.0 + random.uniform(-jr, jr)))


def backoff(attempt: int, base: float = 0.5, factor: float = 2.0, cap: float = 10.0) -> float:
    """
    Exponential backoff with cap.
    """
    return min(cap, base * (factor ** max(0, attempt - 1)))


FuncSync = TypeVar("FuncSync", bound=Callable[..., T])


def retry_sync(
    tries: int = 3,
    base_delay: float = 0.5,
    factor: float = 2.0,
    jitter_ratio: float = 0.2,
    exceptions: Tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[FuncSync], FuncSync]:
    """
    Simple sync retry decorator with exponential backoff + jitter.
    """
    def decorator(fn: FuncSync) -> FuncSync:
        def wrapper(*args: Any, **kwargs: Any):  # type: ignore[misc]
            last_exc: Optional[BaseException] = None
            for attempt in range(1, tries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:  # type: ignore[misc]
                    last_exc = exc
                    if attempt >= tries:
                        break
                    delay = jitter(backoff(attempt, base_delay, factor))
                    # In sync context, we cannot asyncio.sleep; use time.sleep
                    import time
                    time.sleep(delay)
            assert last_exc is not None
            raise last_exc
        return wrapper  # type: ignore[return-value]
    return decorator


FuncAsync = TypeVar("FuncAsync", bound=Callable[..., Any])


def retry_async(
    tries: int = 3,
    base_delay: float = 0.5,
    factor: float = 2.0,
    jitter_ratio: float = 0.2,
    exceptions: Tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[FuncAsync], FuncAsync]:
    """
    Simple async retry decorator with exponential backoff + jitter.
    """
    def decorator(fn: FuncAsync) -> FuncAsync:
        async def wrapper(*args: Any, **kwargs: Any):  # type: ignore[misc]
            last_exc: Optional[BaseException] = None
            for attempt in range(1, tries + 1):
                try:
                    res = fn(*args, **kwargs)
                    if asyncio.iscoroutine(res):
                        return await res
                    return res
                except exceptions as exc:  # type: ignore[misc]
                    last_exc = exc
                    if attempt >= tries:
                        break
                    delay = jitter(backoff(attempt, base_delay, factor), jitter_ratio)
                    await asyncio.sleep(delay)
            assert last_exc is not None
            raise last_exc
        return wrapper  # type: ignore[return-value]
    return decorator
