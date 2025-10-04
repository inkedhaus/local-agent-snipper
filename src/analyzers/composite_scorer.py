from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..core.config import cfg


@dataclass
class CompositeScoreResult:
    demand_score: float
    margin_percent: float  # 0..100 scale
    composite_score: float  # 0..1 scale


class CompositeScorer:
    """
    Combine multiple signals into a single composite score in [0, 1].
    Current inputs:
      - demand_score: already 0..1
      - margin_percent: convert to 0..1 by dividing by a cap (default 50% -> 0.5 becomes 1.0)
    Weights can be adjusted via config.thresholds:
      thresholds:
        composite_weights:
          demand: 0.6
          margin: 0.4
        margin_cap_percent: 50
    """

    def __init__(self) -> None:
        t = cfg.thresholds() or {}
        w = (t.get("composite_weights") or {}) if isinstance(t.get("composite_weights"), dict) else {}
        self.w_demand: float = float(w.get("demand", 0.6))
        self.w_margin: float = float(w.get("margin", 0.4))
        # Normalize weights if they don't sum to 1
        total = max(1e-9, self.w_demand + self.w_margin)
        self.w_demand /= total
        self.w_margin /= total

        self.margin_cap_percent: float = float(t.get("margin_cap_percent", 50.0))

    def score(self, demand_score: float, margin_percent: float) -> CompositeScoreResult:
        d = max(0.0, min(1.0, float(demand_score)))
        # Convert margin % (e.g., 25 means 25%) to [0..1] using cap
        cap = max(1e-6, self.margin_cap_percent)
        m_unit = max(0.0, min(1.0, float(margin_percent) / cap))
        composite = (self.w_demand * d) + (self.w_margin * m_unit)
        composite = max(0.0, min(1.0, composite))
        return CompositeScoreResult(demand_score=d, margin_percent=float(margin_percent), composite_score=composite)
