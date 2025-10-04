from __future__ import annotations

from typing import Dict, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import cfg
from ..models.listing import Listing
from ..models.deal import Deal
from ..utils.logger import get_logger
from ..evaluators.sniper_bot import SniperBot

log = get_logger()


def _get_thresholds() -> dict:
    return cfg.thresholds() or {}


def _upsert_deal_from_listing(db: Session, listing: Listing, bot: SniperBot) -> Tuple[Deal, bool]:
    """
    Create or update a Deal row derived from a Listing + SniperBot decision.
    Returns (deal, created_flag)
    """
    # Try to find an existing deal for this listing
    stmt = select(Deal).where(Deal.listing_id == listing.id)
    deal = db.execute(stmt).scalars().first()
    created = False

    # Evaluate listing
    decision = bot.evaluate(listing)

    if deal is None:
        deal = Deal(listing_id=listing.id, status="new")
        created = True

    # Update fields
    deal.status = "eligible" if decision.should_alert else "ignored"
    deal.score = decision.composite.composite_score
    deal.estimated_margin = decision.margin.margin_amount
    deal.currency = listing.currency or deal.currency
    # Optionally store reason in notes for visibility
    deal.notes = decision.reason

    if created:
        db.add(deal)

    return deal, created


def analyze_all(db: Session) -> Dict[str, int]:
    """
    Evaluate all active listings and upsert Deals accordingly.
    Returns counts: {"created": X, "updated": Y}
    """
    log.info("Analysis worker: evaluating listings into deals")
    bot = SniperBot()

    stmt = select(Listing).where(Listing.is_active.is_(True))
    listings = db.execute(stmt).scalars().all()

    created = 0
    updated = 0
    for lst in listings:
        try:
            deal, was_created = _upsert_deal_from_listing(db, lst, bot)
            if was_created:
                created += 1
            else:
                updated += 1
        except Exception as e:
            log.warning("analyze failed for listing id=%s: %s", getattr(lst, "id", None), e)

    db.commit()
    log.info("Analysis worker: finished (created=%d, updated=%d)", created, updated)
    return {"created": created, "updated": updated}
