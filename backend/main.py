"""
MANAS FastAPI application entry point.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import time

from configs.settings import get_settings
from backend.api.routes import (
    datasets, regions, analyses, literature, health, ingestion
)

from contextlib import asynccontextmanager

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("manas")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"MANAS {settings.app_version} starting in {settings.environment} mode")
    if settings.environment == "development":
        from backend.database.session import create_tables
        create_tables()
        logger.info("Database tables verified/created.")
    yield

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="MANAS API",
    description=(
        "मनस् — Computational Brain Disease Mapping. "
        "Research-grade API for Alzheimer's disease regional analysis."
    ),
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
        "http://localhost:3005", "http://127.0.0.1:3005",
        "https://manas-wheat.vercel.app",
    ],
    allow_origin_regex=r"^(https?://(localhost|127\.0\.0\.1)(:\d+)?|https://.*\.vercel\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{(time.time() - start):.4f}s"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. This has been logged.",
            "detail": str(exc) if settings.debug else None,
        },
    )


# Register routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(regions.router, prefix="/api/regions", tags=["Brain Regions"])
app.include_router(analyses.router, prefix="/api/analyses", tags=["Analyses"])
app.include_router(analyses.router, prefix="/api/analysis", include_in_schema=False)
app.include_router(literature.router, prefix="/api/literature", tags=["Literature"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["Ingestion"])




@app.get("/", include_in_schema=False)
async def root():
    return {
        "project": "MANAS — मनस्",
        "description": "Computational Brain Disease Mapping",
        "version": settings.app_version,
        "disclaimer": (
            "MANAS is a computational research platform. Results represent "
            "statistical analyses of research datasets and should not be "
            "interpreted as medical diagnosis, treatment advice, or proof "
            "of biological causation."
        ),
        "docs": "/api/docs",
    }
