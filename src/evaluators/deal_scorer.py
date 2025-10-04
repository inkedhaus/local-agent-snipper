from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from ..analyzers.demand_analyzer import DemandAnalyzer
from ..analyzers.trend_analyzer import TrendAnalyzer
from ..analyzers.composite_scorer import CompositeScorer, CompositeScoreResult
from .margin_calculator import calculate_margin, MarginResult
from ..core.config import cfg

if TYPE_CHECKING:
    from ..models.listing import Listing


@dataclass(frozen=True)
class DealScoreOutput:
    demand_score: float
    margin: MarginResult
    composite: CompositeScoreResult


class DealScorer:
    """
    Orchestrates demand, margin, and composite scoring for a listing.
    Assumptions:
      - assumed_sell_price: expected resale price (defaults to listing.price if provided)
      - fees_percent: marketplace/payment fees from config.thresholds.fees_percent (default 10%)
      - shipping_cost: from config.thresholds.shipping_cost (default 0)
      - trend: Uses TrendAnalyzer to compute a keyword-based score (optional, default baseline)
    """

    def __init__(self) -> None:
        self.demand_analyzer = DemandAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.composite = CompositeScorer()

        t = cfg.thresholds() or {}
        self.default_fees_percent: float = float(t.get("fees_percent", 10.0))
        self.default_shipping_cost: float = float(t.get("shipping_cost", 0.0))

    def score_listing(
        self,
        listing: "Listing",
        assumed_sell_price: Optional[float] = None,
        fees_percent: Optional[float] = None,
        shipping_cost: Optional[float] = None,
        trend_keyword: Optional[str] = None,
        trend_location: Optional[str] = None,
    ) -> DealScoreOutput:
        # Determine trend score (optional); fall back to default baseline in TrendAnalyzer
        keyword = trend_keyword or (listing.title or "")[:50]
        trend_score = self.trend_analyzer.score_keyword(keyword, trend_location)

        # Demand score
        demand = self.demand_analyzer.score_listing(listing, trend_score)

        # Margin
        sell_price = assumed_sell_price if assumed_sell_price is not None else listing.price
        fees = self._coalesce_float(fees_percent, self.default_fees_percent)
        ship = self._coalesce_float(shipping_cost, self.default_shipping_cost)
        margin = calculate_margin(
            sell_price=sell_price,
            cost_basis=listing.price,  # treat current price as cost basis by default
            fees_percent=fees,
            shipping_cost=ship,
        )

        # Composite
        composite = self.composite.score(demand_score=demand, margin_percent=margin.margin_percent)

        return DealScoreOutput(demand_score=demand, margin=margin, composite=composite)

    @staticmethod
    def _coalesce_float(val: Optional[float], fallback: float) -> float:
        try:
            return float(val) if val is not None else float(fallback)
        except Exception:
            return float(fallback)
