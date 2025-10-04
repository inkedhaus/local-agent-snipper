from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

try:
    # Optional: try to include routers if/when they exist
    from .routes import listings as listings_routes  # type: ignore
    from .routes import deals as deals_routes  # type: ignore
    from .routes import alerts as alerts_routes  # type: ignore
    from .routes import config as config_routes  # type: ignore
except Exception:
    listings_routes = None  # type: ignore[assignment]
    deals_routes = None  # type: ignore[assignment]
    alerts_routes = None  # type: ignore[assignment]
    config_routes = None  # type: ignore[assignment]

from ..core.config import cfg


def create_app() -> FastAPI:
    app = FastAPI(
        title=cfg.app().get("name", "Local Sniper Agent"),
        version=cfg.app().get("version", "0.1.0"),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Healthcheck
    @app.get("/health", tags=["system"])
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "service": cfg.app().get("name", "sniper")})

    # Root
    @app.get("/", tags=["system"])
    def root() -> JSONResponse:
        return JSONResponse({"message": "Local Sniper Agent API"})

    # Conditionally include routers when they are implemented
    if listings_routes and hasattr(listings_routes, "router"):
        app.include_router(listings_routes.router, prefix="/listings", tags=["listings"])
    if deals_routes and hasattr(deals_routes, "router"):
        app.include_router(deals_routes.router, prefix="/deals", tags=["deals"])
    if alerts_routes and hasattr(alerts_routes, "router"):
        app.include_router(alerts_routes.router, prefix="/alerts", tags=["alerts"])
    if config_routes and hasattr(config_routes, "router"):
        app.include_router(config_routes.router, prefix="/config", tags=["config"])

    return app


app = create_app()
