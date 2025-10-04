from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.alert import Alert

router = APIRouter()


@router.get("/", response_model=List[dict])
def list_alerts(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, max_length=30),
    channel_filter: str | None = Query(None, max_length=30),
) -> list[dict]:
    stmt = select(Alert).order_by(Alert.created_at.desc()).offset(offset).limit(limit)
    if status_filter:
        stmt = stmt.where(Alert.status == status_filter)
    if channel_filter:
        stmt = stmt.where(Alert.channel == channel_filter)
    rows = db.execute(stmt).scalars().all()
    # Return plain dicts for now; schemas can be added later if needed
    return [  # type: ignore[return-value]
        {
            "id": r.id,
            "deal_id": r.deal_id,
            "channel": r.channel,
            "status": r.status,
            "message": r.message,
            "sent_at": r.sent_at,
            "metadata": r.metadata,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in rows
    ]


@router.get("/{alert_id}", response_model=dict)
def get_alert(alert_id: int, db: Session = Depends(get_db)) -> dict:
    obj = db.get(Alert, alert_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "id": obj.id,
        "deal_id": obj.deal_id,
        "channel": obj.channel,
        "status": obj.status,
        "message": obj.message,
        "sent_at": obj.sent_at,
        "metadata": obj.metadata,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: int, db: Session = Depends(get_db)) -> None:
    obj = db.get(Alert, alert_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(obj)
    db.commit()
    return None
