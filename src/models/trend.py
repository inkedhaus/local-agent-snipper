from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from . import Base, TimestampMixin


class Trend(Base, TimestampMixin):
    __tablename__ = "trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., US-TX
    source: Mapped[str] = mapped_column(String(50), default="google_trends")  # google_trends, internal
    score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))  # normalized interest score
    timeframe_start: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    timeframe_end: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint(
            "keyword", "location", "timeframe_start", "timeframe_end",
            name="uq_trends_keyword_loc_timeframe",
        ),
        Index("ix_trends_keyword_location", "keyword", "location"),
    )

    def __repr__(self) -> str:
        return f"<Trend id={self.id} keyword={self.keyword} location={self.location} score={self.score}>"
