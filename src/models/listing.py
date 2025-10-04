from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Numeric,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base, TimestampMixin

if TYPE_CHECKING:
    from .deal import Deal


class Listing(Base, TimestampMixin):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(300))
    description: Mapped[Optional[str]] = mapped_column(String)
    price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    posted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    seller_contact: Mapped[Optional[str]] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_seen_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Relationships
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="listing", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "source", "external_id", name="uq_listing_source_external_id"
        ),
        Index("ix_listings_source", "source"),
        Index("ix_listings_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Listing id={self.id} source={self.source} external_id={self.external_id}>"
