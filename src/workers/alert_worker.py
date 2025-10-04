from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..core.config import cfg
from ..utils.logger import get_logger
from ..models.alert import Alert
from ..models.deal import Deal

log = get_logger()


def _enabled_channels() -> List[str]:
    """
    Read enabled channels from config:
      alerts:
        enabled_channels: ["email", "sms", "slack"]
    Defaults to ["email"] if not configured.
    """
    alerts_cfg = cfg.get("alerts", {}) or {}
    chans = alerts_cfg.get("enabled_channels", ["email"])
    if not isinstance(chans, list):
        return ["email"]
    # normalize
    out = []
    for c in chans:
        s = str(c).strip().lower()
        if s in {"email", "sms", "slack"}:
            out.append(s)
    return out or ["email"]


def _send_email_alert(alert: Alert) -> bool:
    """
    Placeholder email sender. Wire up SendGrid later using cfg.get('alerts', {}).get('sendgrid', {...}).
    """
    log.info("Sending EMAIL alert for deal_id=%s: %s", alert.deal_id, (alert.message or "").strip())
    return True


def _send_sms_alert(alert: Alert) -> bool:
    """
    Placeholder SMS sender. Wire up Twilio later using cfg.get('alerts', {}).get('twilio', {...}).
    """
    log.info("Sending SMS alert for deal_id=%s: %s", alert.deal_id, (alert.message or "").strip())
    return True


def _send_slack_alert(alert: Alert) -> bool:
    """
    Placeholder Slack sender. Wire up Slack SDK later using cfg.get('alerts', {}).get('slack', {...}).
    """
    log.info("Sending SLACK alert for deal_id=%s: %s", alert.deal_id, (alert.message or "").strip())
    return True


def _send_alert(alert: Alert) -> bool:
    if alert.channel == "email":
        return _send_email_alert(alert)
    if alert.channel == "sms":
        return _send_sms_alert(alert)
    if alert.channel == "slack":
        return _send_slack_alert(alert)
    log.warning("Unknown alert channel=%s for alert id=%s", alert.channel, alert.id)
    return False


def _alert_exists(db: Session, deal_id: int, channel: str) -> bool:
    stmt = select(Alert).where(and_(Alert.deal_id == deal_id, Alert.channel == channel, Alert.status == "sent"))
    return db.execute(stmt).scalars().first() is not None


def _build_message_for_deal(deal: Deal) -> str:
    parts = [
        f"Deal #{deal.id} - status={deal.status} score={deal.score}",
        f"margin=${(deal.estimated_margin or 0):.2f} ({deal.currency or ''})",
    ]
    if getattr(deal, "listing", None) is not None:
        lst = deal.listing  # type: ignore[attr-defined]
        parts.append(f"title={getattr(lst, 'title', None) or ''}")
        parts.append(f"url={getattr(lst, 'url', None) or ''}")
        parts.append(f"price={getattr(lst, 'price', None)} {getattr(lst, 'currency', '')}")
    if deal.notes:
        parts.append(f"notes={deal.notes}")
    return " | ".join(parts)


def process_alerts(db: Session) -> Dict[str, int]:
    """
    Create and send alerts for deals that meet thresholds.
    Deals are considered 'eligible' by the analysis worker.
    For each enabled channel, create an Alert if one hasn't already been sent,
    attempt delivery, and update statuses accordingly.
    """
    channels = _enabled_channels()
    created = 0
    sent = 0
    failed = 0

    # Load eligible deals and joined listing relationship (lazy load is fine)
    stmt = select(Deal).where(Deal.status == "eligible").order_by(Deal.created_at.desc())
    deals = db.execute(stmt).scalars().all()

    for deal in deals:
        for ch in channels:
            try:
                if _alert_exists(db, deal.id, ch):
                    continue

                message = _build_message_for_deal(deal)
                alert = Alert(deal_id=deal.id, channel=ch, status="pending", message=message)
                db.add(alert)
                db.flush()  # assign id
                created += 1

                ok = _send_alert(alert)
                if ok:
                    alert.status = "sent"
                    sent += 1
                else:
                    alert.status = "failed"
                    failed += 1
            except Exception as e:
                log.warning("Alert processing failed for deal_id=%s channel=%s: %s", deal.id, ch, e)
                failed += 1

    db.commit()
    log.info("Alert worker: created=%d, sent=%d, failed=%d", created, sent, failed)
    return {"created": created, "sent": sent, "failed": failed}
