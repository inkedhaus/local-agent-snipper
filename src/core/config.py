"""
Configuration loader for Local Sniper Agent.

- Loads environment variables from .env (if present)
- Loads YAML config from config/config.yaml (overrideable via SNIPER_CONFIG_PATH)
- Provides simple accessors for nested sections
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

try:
    # Optional: load .env if available
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # dotenv is optional; ignore if unavailable
    pass


class Config:
    _instance: Optional["Config"] = None

    def __init__(self, data: Dict[str, Any], source_path: Path) -> None:
        self._data = data
        self._source_path = source_path

    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from YAML file and environment overrides.
        Environment variable SNIPER_CONFIG_PATH can override the default path.
        """
        if cls._instance is not None:
            return cls._instance

        default_path = Path("config/config.yaml")
        config_path_str = os.getenv("SNIPER_CONFIG_PATH", str(default_path))
        config_path = Path(config_path_str)

        if not config_path.exists():
            # Provide a safe default minimal configuration if file isn't present yet.
            default_data: Dict[str, Any] = {
                "app": {
                    "name": "Local Sniper Agent",
                    "version": "0.1.0",
                    "environment": "development",
                    "log_level": "INFO",
                },
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "sniper_agent",
                    "user": "postgres",
                    "password": os.getenv("DB_PASSWORD", None),
                },
                "redis": {"host": "localhost", "port": 6379, "db": 0},
                "location": {"zip_code": "00000", "radius_miles": 50},
                "thresholds": {
                    "min_discount_percent": 20,
                    "min_margin_percent": 15,
                    "min_demand_score": 0.7,
                    "min_composite_score": 0.75,
                },
            }
            cls._instance = cls(default_data, config_path)
            return cls._instance

        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Environment overrides (simple example for DB password)
        db = data.setdefault("database", {})
        db.setdefault("password", os.getenv("DB_PASSWORD"))

        cls._instance = cls(data, config_path)
        return cls._instance

    @property
    def source_path(self) -> Path:
        return self._source_path

    def data(self) -> Dict[str, Any]:
        return self._data

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a top-level key.
        """
        return self._data.get(key, default)

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a nested section as a dict. Returns empty dict if missing.
        """
        value = self._data.get(section)
        return value if isinstance(value, dict) else {}

    # Convenience helpers
    def app(self) -> Dict[str, Any]:
        return self.get_section("app")

    def database(self) -> Dict[str, Any]:
        return self.get_section("database")

    def redis(self) -> Dict[str, Any]:
        return self.get_section("redis")

    def thresholds(self) -> Dict[str, Any]:
        return self.get_section("thresholds")

    def location(self) -> Dict[str, Any]:
        return self.get_section("location")


# Eagerly load a singleton instance for simple imports
cfg = Config.load()
