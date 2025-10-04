from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base, TimestampMixin

if TYPE_CHECKING:
    from .deal import Deal


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    channel: Mapped[str] = mapped_column(String(30), default="email", index=True)  # e.g., email, sms, slack
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)  # pending, sent, failed
    message: Mapped[Optional[str]] = mapped_column(String)
    sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", back_populates="alerts")

    __table_args__ = (
        Index("ix_alerts_channel", "channel"),
        Index("ix_alerts_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Alert id={self.id} deal_id={self.deal_id} status={self.status} channel={self.channel}>"
