"""
Database setup using SQLAlchemy 2.0 style.

- Engine/session factory configured from Config
- Dependency helpers for FastAPI
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import cfg

_engine = None
_SessionLocal: Optional[sessionmaker] = None


def _build_db_url() -> str:
    db = cfg.database()
    user = db.get("user", "postgres")
    password = db.get("password", "")
    host = db.get("host", "localhost")
    port = db.get("port", 5432)
    name = db.get("name", "sniper_agent")
    # psycopg2 driver
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        url = _build_db_url()
        _engine = create_engine(url, echo=False, pool_pre_ping=True, future=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_session_factory() -> sessionmaker:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.
    """
    SessionLocal = get_session_factory()
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# FastAPI dependency
def get_db() -> Generator[Session, None, None]:
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
