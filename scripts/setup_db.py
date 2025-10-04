from __future__ import annotations

"""
Create database tables for Local Sniper Agent.

Usage:
  - With Docker Compose running (Postgres service): python scripts/setup_db.py
  - Or with local env configured via .env / config.yaml

This script imports models to ensure SQLAlchemy registers all tables,
then calls Base.metadata.create_all(engine).
"""

from pathlib import Path
import sys

# Ensure project root is on sys.path when running directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.database import get_engine  # noqa: E402
from src.models import Base  # noqa: E402

# Import all model modules so tables are registered on Base.metadata
from src.models import listing as _listing  # noqa: F401,E402
from src.models import deal as _deal  # noqa: F401,E402
from src.models import alert as _alert  # noqa: F401,E402
from src.models import trend as _trend  # noqa: F401,E402


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    main()
