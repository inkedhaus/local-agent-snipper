from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, TYPE_CHECKING

from ..core.config import cfg

if TYPE_CHECKING:
    from ..models.listing import Listing


class DemandAnalyzer:
    """
    Lightweight heuristic demand analyzer.

    Produces a demand score in [0.0, 1.0] using simple signals:
      - Recency boost: newer listings imply higher demand/velocity
      - Trend boost: optional external trend score (0..1) lifts demand
      - Category/location hooks (placeholders for future tuning)

    This is intentionally simple to provide a runnable foundation.
    """

    def __init__(self) -> None:
        t = cfg.thresholds() or {}
        # How many hours since posted_at counts as "fresh"
        self.fresh_hours: float = float(t.get("fresh_hours", 24.0))

        # Caps to keep final score in bounds
        self.max_score: float = 1.0
        self.base_score: float = 0.4  # conservative baseline

        # Weights
        self.recency_weight: float = 0.35
        self.trend_weight: float = 0.25

    @staticmethod
    def _hours_since(dt: Optional[datetime]) -> Optional[float]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0

    def score_listing(self, listing: "Listing", trend_score: Optional[float] = None) -> float:
        score = self.base_score

        # Recency: full weight when posted within fresh_hours, linearly decay until 7 days
        hours = self._hours_since(listing.posted_at)
        if hours is not None:
            if hours <= self.fresh_hours:
                score += self.recency_weight
            else:
                # linear decay to zero contribution by 7 days (168h)
                window = max(1.0, 168.0 - self.fresh_hours)
                over = min(168.0 - self.fresh_hours, max(0.0, hours - self.fresh_hours))
                factor = max(0.0, 1.0 - (over / window))
                score += self.recency_weight * factor

        # Trend contribution (if provided 0..1)
        if trend_score is not None:
            clamped = max(0.0, min(1.0, trend_score))
            score += self.trend_weight * clamped

        # Clamp
        return max(0.0, min(self.max_score, score))
