from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.listing import Listing
from ..schemas.listing_schema import ListingCreate, ListingRead

router = APIRouter()


@router.get("/", response_model=List[ListingRead])
def list_listings(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[Listing]:
    stmt = (
        select(Listing)
        .order_by(Listing.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()
    return rows


@router.post("/", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
def create_listing(payload: ListingCreate, db: Session = Depends(get_db)) -> Listing:
    obj = Listing(**payload.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{listing_id}", response_model=ListingRead)
def get_listing(listing_id: int, db: Session = Depends(get_db)) -> Listing:
    obj = db.get(Listing, listing_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Listing not found")
    return obj


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(listing_id: int, db: Session = Depends(get_db)) -> None:
    obj = db.get(Listing, listing_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Listing not found")
    db.delete(obj)
    db.commit()
    return None
