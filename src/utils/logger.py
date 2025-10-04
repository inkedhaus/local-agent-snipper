from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logger(
    name: str = "sniper",
    level: Optional[str] = None,
    log_dir: str = "logs",
) -> logger.__class__:
    """
    Configure Loguru logger with sane defaults:
    - Console sink
    - Rotating file sink
    Environment overrides:
      LOG_LEVEL, LOG_DIR, LOG_NAME
    """
    level = level or os.getenv("LOG_LEVEL", "INFO")
    log_dir = os.getenv("LOG_DIR", log_dir)
    name = os.getenv("LOG_NAME", name)

    Path(log_dir).mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
    )
    logger.add(
        Path(log_dir) / f"{name}.log",
        level=level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    logger.debug("Logger initialized (level={}, dir={}, name={})", level, log_dir, name)
    return logger


def get_logger() -> logger.__class__:
    """
    Return the configured logger. If not configured, set up with defaults.
    """
    if not logger._core.handlers:  # type: ignore[attr-defined]
        setup_logger()
    return logger
