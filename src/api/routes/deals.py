from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.deal import Deal
from ..schemas.deal_schema import DealCreate, DealRead

router = APIRouter()


@router.get("/", response_model=List[DealRead])
def list_deals(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, max_length=30),
) -> list[Deal]:
    stmt = select(Deal).order_by(Deal.created_at.desc()).offset(offset).limit(limit)
    if status_filter:
        stmt = stmt.where(Deal.status == status_filter)
    rows = db.execute(stmt).scalars().all()
    return rows


@router.post("/", response_model=DealRead, status_code=status.HTTP_201_CREATED)
def create_deal(payload: DealCreate, db: Session = Depends(get_db)) -> Deal:
    obj = Deal(**payload.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{deal_id}", response_model=DealRead)
def get_deal(deal_id: int, db: Session = Depends(get_db)) -> Deal:
    obj = db.get(Deal, deal_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Deal not found")
    return obj


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(deal_id: int, db: Session = Depends(get_db)) -> None:
    obj = db.get(Deal, deal_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Deal not found")
    db.delete(obj)
    db.commit()
    return None
