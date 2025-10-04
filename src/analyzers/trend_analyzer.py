from __future__ import annotations

from functools import lru_cache
from typing import Optional

from ..core.config import cfg


class TrendAnalyzer:
    """
    Minimal trend analyzer.

    Placeholder that maps a keyword (optionally with location) to a score in [0, 1].
    In the future, wire this to Google Trends or other signals. For now:
      - Uses static per-keyword overrides from config if present
      - Otherwise returns a conservative baseline
    """

    def __init__(self) -> None:
        tr_cfg = cfg.get("trends", {}) or {}
        self.default_score: float = float(tr_cfg.get("default_score", 0.5))
        # Optional explicit overrides in config, e.g.:
        # trends:
        #   overrides:
        #     "iphone": 0.9
        #     "ps5": 0.85
        self.overrides: dict[str, float] = {
            k.lower(): float(v) for k, v in (tr_cfg.get("overrides", {}) or {}).items()
        }

    @lru_cache(maxsize=1024)
    def score_keyword(self, keyword: str, location: Optional[str] = None) -> float:
        key = (keyword or "").strip().lower()
        if not key:
            return 0.0
        # In a real impl, location could adjust score; keep simple for now.
        if key in self.overrides:
            val = self.overrides[key]
            return max(0.0, min(1.0, val))
        return max(0.0, min(1.0, self.default_score))
