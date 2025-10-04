from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MarginResult:
    sell_price: float
    cost_basis: float
    fees_amount: float
    shipping_cost: float
    total_cost: float
    margin_amount: float
    margin_percent: float  # 0..100


def _to_float(x: Optional[float], default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def calculate_margin(
    sell_price: Optional[float],
    cost_basis: Optional[float],
    fees_percent: Optional[float] = 10.0,
    shipping_cost: Optional[float] = 0.0,
) -> MarginResult:
    """
    Compute simple margin given sell_price and cost_basis.
    - fees_percent is a % of sell_price to account for marketplace fees, payment processor, etc.
    - shipping_cost is added as a fixed cost.
    Returns amounts and margin % (0..100 scale).
    """
    sp = _to_float(sell_price, 0.0)
    cb = _to_float(cost_basis, 0.0)
    fp = max(0.0, _to_float(fees_percent, 0.0))
    ship = max(0.0, _to_float(shipping_cost, 0.0))

    fees_amount = sp * (fp / 100.0)
    total_cost = cb + fees_amount + ship
    margin_amount = sp - total_cost
    margin_percent = 0.0
    if sp > 0:
        margin_percent = max(0.0, (margin_amount / sp) * 100.0)

    return MarginResult(
        sell_price=sp,
        cost_basis=cb,
        fees_amount=fees_amount,
        shipping_cost=ship,
        total_cost=total_cost,
        margin_amount=margin_amount,
        margin_percent=margin_percent,
    )
