"""FastAPI application entrypoint.

Security posture:
  * CORS is restricted to the configured frontend origin(s).
  * A per-client rate limit is applied to every route (slowapi).
  * All DB access is parameterized (see ``app.crud``).
  * No secrets are read here; configuration comes from the environment.

On startup the database is created (if needed) and seeded from the committed
``data/processed`` artifacts, so the API can serve without any live API call.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routers import explain, indicators, meta
from app.config import settings
from app.ratelimit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import here to keep import-time side effects out of module load.
    from app.seed import init_and_seed

    try:
        loaded = init_and_seed()
        print(f"[startup] database ready ({loaded} observations seeded).")
    except Exception as exc:  # pragma: no cover - defensive boot logging
        print(f"[startup] WARNING: could not seed database: {exc}")
    yield


app = FastAPI(
    title="Pulse API",
    version="0.1.0",
    description=(
        "A public mental-health & well-being observatory. Serves only "
        "aggregate, country-level, properly-licensed data."
    ),
    lifespan=lifespan,
)

# --- Rate limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# --- CORS (locked to configured origins) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(meta.router, prefix="/api")
app.include_router(indicators.router, prefix="/api")
app.include_router(explain.router, prefix="/api")


@app.get("/api", tags=["meta"])
def api_root() -> dict:
    return {
        "name": "Pulse API",
        "version": app.version,
        "docs": "/docs",
        "endpoints": [
            "/api/health",
            "/api/sources",
            "/api/summary",
            "/api/indicators",
            "/api/indicators/{key}",
            "/api/indicators/{key}/countries",
            "/api/indicators/{key}/series",
            "/api/explain",
        ],
        "crisis_resources": {
            "us_988": "Call or text 988 (Suicide & Crisis Lifeline, US)",
            "international": "https://findahelpline.com",
        },
        "data_ethics": "Aggregate, public, licensed data only. No individual-level data.",
    }
