from __future__ import annotations

"""
Seed the database with minimal sample data for Local Sniper Agent.

Usage:
  python scripts/seed_data.py
"""

from pathlib import Path
import sys
from datetime import datetime, timezone

# Ensure project root is on sys.path when running directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.database import get_engine, session_scope  # noqa: E402
from src.models import Base  # noqa: E402
from src.models.listing import Listing  # noqa: E402
from src.models.deal import Deal  # noqa: E402
from src.models.alert import Alert  # noqa: E402
from src.models.trend import Trend  # noqa: E402


def ensure_tables() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def seed_listings() -> None:
    from sqlalchemy import select

    with session_scope() as db:
        # Avoid duplicates on reruns by external_id unique constraint
        samples = [
            {
                "source": "craigslist",
                "external_id": "sample-craig-001",
                "title": "iPhone 13 128GB - Excellent",
                "description": "Lightly used, includes box and charger.",
                "price": 350.00,
                "currency": "USD",
                "url": "https://www.craigslist.org/sample/iphone-13-001",
                "location": "US-TX",
                "category": "electronics",
                "posted_at": datetime.now(timezone.utc),
                "seller_contact": None,
                "is_active": True,
                "metadata": {"condition": "excellent"},
            },
            {
                "source": "offerup",
                "external_id": "sample-ou-ps5-001",
                "title": "PlayStation 5 Disc - Like New",
                "description": "Includes controller and HDMI cable.",
                "price": 400.00,
                "currency": "USD",
                "url": "https://offerup.com/item/detail/sample-ps5-001",
                "location": "US-TX",
                "category": "gaming",
                "posted_at": datetime.now(timezone.utc),
                "seller_contact": None,
                "is_active": True,
                "metadata": {"extras": "1 controller"},
            },
            {
                "source": "facebook",
                "external_id": "sample-fb-rtx3060-001",
                "title": "RTX 3060 GPU",
                "description": "Works great, upgraded to 4070.",
                "price": 180.00,
                "currency": "USD",
                "url": "https://www.facebook.com/marketplace/item/sample-rtx3060-001",
                "location": "US-TX",
                "category": "pc-parts",
                "posted_at": datetime.now(timezone.utc),
                "seller_contact": None,
                "is_active": True,
                "metadata": {"brand": "NVIDIA"},
            },
        ]

        created, skipped = 0, 0
        for data in samples:
            stmt = select(Listing).where(
                Listing.source == data["source"], Listing.external_id == data["external_id"]
            )
            existing = db.execute(stmt).scalars().first()
            if existing:
                skipped += 1
                continue
            obj = Listing(**data)
            db.add(obj)
            created += 1

        print(f"Listings: created={created}, skipped={skipped}")


def main() -> None:
    ensure_tables()
    seed_listings()
    print("Seeding complete.")


if __name__ == "__main__":
    main()
