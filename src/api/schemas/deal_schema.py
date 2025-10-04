from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class DealBase(BaseModel):
    listing_id: int = Field(..., ge=1)
    status: str = Field("new", max_length=30)
    score: Optional[float] = None
    estimated_margin: Optional[float] = None
    currency: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class DealCreate(DealBase):
    pass


class DealRead(DealBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
