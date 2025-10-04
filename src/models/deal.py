from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base, TimestampMixin

if TYPE_CHECKING:
    from .listing import Listing
    from .alert import Alert


class Deal(Base, TimestampMixin):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    estimated_margin: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    notes: Mapped[Optional[str]] = mapped_column(String)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Relationships
    listing: Mapped["Listing"] = relationship("Listing", back_populates="deals")
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="deal", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_deals_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Deal id={self.id} listing_id={self.listing_id} status={self.status}>"
