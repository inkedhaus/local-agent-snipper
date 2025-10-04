from __future__ import annotations

import re
from typing import Optional


_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_PHONE_RE = re.compile(r"^\+?[0-9\-().\s]{7,20}$")
_URL_RE = re.compile(
    r"^(https?://)"
    r"([A-Za-z0-9\-._~%]+)"
    r"(:\d+)?"
    r"(/[A-Za-z0-9\-._~%!$&'()*+,;=:@/]*)?"
    r"(\?[A-Za-z0-9\-._~%!$&'()*+,;=:@/?]*)?"
    r"(#[A-Za-z0-9\-._~%!$&'()*+,;=:@/?]*)?$"
)


def is_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value))


def is_phone(value: str) -> bool:
    return bool(_PHONE_RE.match(value))


def is_url(value: str) -> bool:
    return bool(_URL_RE.match(value))


def clamp(value: float, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    """
    Clamp a numeric value between optional min and max.
    """
    if min_value is not None and value < min_value:
        return min_value
    if max_value is not None and value > max_value:
        return max_value
    return value
