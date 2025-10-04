from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ListingBase(BaseModel):
    source: str = Field(..., max_length=50)
    external_id: str = Field(..., max_length=100)
    title: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = Field(None, max_length=10)
    url: str = Field(..., max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    posted_at: Optional[datetime] = None
    seller_contact: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = True
    last_seen_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class ListingCreate(ListingBase):
    pass


class ListingRead(ListingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
