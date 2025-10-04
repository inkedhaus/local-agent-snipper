from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from ..core.config import cfg
from .deal_scorer import DealScorer, DealScoreOutput

if TYPE_CHECKING:
    from ..models.listing import Listing


@dataclass(frozen=True)
class SniperDecision:
    should_alert: bool
    reason: str
    scores: DealScoreOutput


class SniperBot:
    """
    High-level evaluator that decides if a listing is a potential 'snipe' based on
    scores and threshold config.

    thresholds in config/config.yaml (example):
      thresholds:
        min_margin_percent: 15
        min_composite_score: 0.75
        min_demand_score: 0.7
        fees_percent: 10
        shipping_cost: 0
    """

    def __init__(self) -> None:
        t = cfg.thresholds() or {}
        self.min_margin_percent: float = float(t.get("min_margin_percent", 15.0))
        self.min_composite_score: float = float(t.get("min_composite_score", 0.75))
        self.min_demand_score: float = float(t.get("min_demand_score", 0.7))
        self.scorer = DealScorer()

    def evaluate(
        self,
        listing: "Listing",
        assumed_sell_price: Optional[float] = None,
        fees_percent: Optional[float] = None,
        shipping_cost: Optional[float] = None,
        trend_keyword: Optional[str] = None,
        trend_location: Optional[str] = None,
    ) -> SniperDecision:
        scores = self.scorer.score_listing(
            listing=listing,
            assumed_sell_price=assumed_sell_price,
            fees_percent=fees_percent,
            shipping_cost=shipping_cost,
            trend_keyword=trend_keyword,
            trend_location=trend_location,
        )

        reasons: list[str] = []
        ok = True

        if scores.demand_score < self.min_demand_score:
            ok = False
            reasons.append(
                f"demand_score {scores.demand_score:.2f} < min_demand {self.min_demand_score:.2f}"
            )

        if scores.margin.margin_percent < self.min_margin_percent:
            ok = False
            reasons.append(
                f"margin {scores.margin.margin_percent:.1f}% < min_margin {self.min_margin_percent:.1f}%"
            )

        if scores.composite.composite_score < self.min_composite_score:
            ok = False
            reasons.append(
                f"composite {scores.composite.composite_score:.2f} < min_composite {self.min_composite_score:.2f}"
            )

        reason = " & ".join(reasons) if reasons else "meets or exceeds all thresholds"
        return SniperDecision(should_alert=ok, reason=reason, scores=scores)
