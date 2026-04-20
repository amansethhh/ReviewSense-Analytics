import logging
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.dependencies import load_artifacts
from app.routes import predict, bulk, language, metrics, feedback
from app.metrics_store import metrics_store

# ── Logging setup ──────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("reviewsense.main")

# O8: Cleanup interval (seconds) — runs every 10 minutes
_CLEANUP_INTERVAL_SECONDS: int = 600


# ── O8: Periodic stale job cleanup ────────────────────────

async def _periodic_job_cleanup():
    """
    O8: Background asyncio task that runs every 10 minutes
    and removes completed/failed bulk jobs older than 30
    minutes from the in-memory job store.

    Active jobs (queued/processing) are never evicted.
    This prevents unbounded memory growth on long-running
    servers without affecting active jobs.
    """
    from app.routes.bulk import cleanup_stale_jobs

    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)
        try:
            removed = cleanup_stale_jobs()
            if removed > 0:
                logger.info(
                    f"[CLEANUP] Removed {removed} stale "
                    f"bulk job(s) from memory"
                )
        except Exception as e:
            logger.warning(
                f"[CLEANUP] Job cleanup failed: {e}"
            )


# ── Lifespan (replaces deprecated @app.on_event) ──────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("[STARTUP] ReviewSense API starting up...")
    settings = get_settings()
    logger.info(f"   Root dir:  {settings.src_dir.parent}")
    logger.info(f"   Model dir: {settings.model_dir}")
    logger.info(f"   Src dir:   {settings.src_dir}")
    # load_artifacts()  # MOVED: Now loads lazily on first request via dependencies.py

    # ── O1: Cold-start warmup ──────────────────────────────
    # WARMUP REMOVED: Render Free Tier (512MB RAM) will OOM
    # or timeout if we load massive PyTorch models before 
    # Uvicorn binds the port. Models will now load lazily 
    # on the first prediction request.
    logger.info("[WARMUP] Skipped to prevent OOM during startup")

    # ── GAP 3-E: Pre-warm Google probe cache ───────────────
    try:
        from app.routes.metrics import (
            _get_google_reachable)
        await _get_google_reachable()
        logger.info("  ✓ Google Translate probe warmed")
    except Exception as e:
        logger.warning(
            f"  ✗ Google probe warmup failed: {e}")

    # ── O8: Start periodic job cleanup ─────────────────────
    cleanup_task = asyncio.create_task(
        _periodic_job_cleanup()
    )
    logger.info(
        f"[CLEANUP] Periodic job cleanup started "
        f"(every {_CLEANUP_INTERVAL_SECONDS}s)"
    )

    logger.info("[SUCCESS] Startup complete - API ready")
    yield
    # SHUTDOWN
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("[SHUTDOWN] ReviewSense API shutting down")


# ── App instance ───────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "ReviewSense Analytics REST API. "
        "Sentiment analysis, LIME explainability, "
        "ABSA, sarcasm detection, and multilingual support."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ───────────────────────────────────────────────────
# IMPORTANT: Never use allow_origins=["*"] in production.
# Origins are loaded from settings (defined in config.py
# and overridable via .env ALLOWED_ORIGINS).

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://reviewsense-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Phase 2, Part 2: Latency monitoring middleware ─────────

@app.middleware("http")
async def add_process_time_header(request: Request,
                                   call_next):
    """
    Records request latency, adds X-Process-Time-Ms header,
    logs method/path/status/latency, and feeds metrics_store
    for runtime percentile computation.
    """
    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = round(
        (time.perf_counter() - start) * 1000, 2
    )
    response.headers["X-Process-Time-Ms"] = str(latency_ms)
    logger.info(
        f"{request.method} {request.url.path} "
        f"— {latency_ms}ms — {response.status_code}"
    )
    # Feed metrics store (fail-safe — never crash middleware)
    try:
        metrics_store.record_request(
            request.url.path,
            latency_ms,
            response.status_code,
        )
    except Exception:
        pass
    return response


# ── Global exception handler ───────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request,
                                    exc: Exception):
    logger.error(
        f"Unhandled exception on "
        f"{request.method} {request.url.path}: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else
                      "An unexpected error occurred.",
            "code": 500,
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request,
                               exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": str(exc),
            "code": 422,
        }
    )


# ── Routers ────────────────────────────────────────────────

app.include_router(
    predict.router,
    prefix="/predict",
    tags=["Prediction"],
)
app.include_router(
    bulk.router,
    prefix="/bulk",
    tags=["Bulk Analysis"],
)
app.include_router(
    language.router,
    prefix="/language",
    tags=["Language Analysis"],
)
app.include_router(
    metrics.router,
    prefix="/metrics",
    tags=["Model Metrics"],
)
app.include_router(
    feedback.router,
    prefix="/feedback",
    tags=["Feedback"],
)


# ── Health + root ──────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "ReviewSense Analytics API",
        "version": settings.app_version,
        "status":  "online",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
