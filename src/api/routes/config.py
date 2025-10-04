from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...core.config import cfg

router = APIRouter()


def _sanitize_config(data: Dict[str, Any]) -> Dict[str, Any]:
    redacted_keys = {"password", "api_key", "token", "secret", "webhook_url"}
    def redact(obj: Any) -> Any:
        if isinstance(obj, dict):
            new: Dict[str, Any] = {}
            for k, v in obj.items():
                if k.lower() in redacted_keys:
                    new[k] = "***redacted***"
                else:
                    new[k] = redact(v)
            return new
        if isinstance(obj, list):
            return [redact(x) for x in obj]
        return obj

    data_copy = deepcopy(data)
    return redact(data_copy)  # type: ignore[return-value]


@router.get("/", tags=["config"])
def get_config() -> JSONResponse:
    data = cfg.data()
    sanitized = _sanitize_config(data)
    return JSONResponse({"config": sanitized, "source_path": str(cfg.source_path)})
