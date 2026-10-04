"""
Mining Document Intelligence & Reporting Platform
SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)
Main FastAPI Application Entrypoint
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.documents import router as documents_router
from app.api.routes.rag import router as rag_router
from app.api.routes.extraction import router as extraction_router
from app.api.routes.reports import router as reports_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.topics import router as topics_router
from app.api.routes.benchmarks import router as benchmarks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure necessary storage and FAISS directories exist
    settings.ensure_directories()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware for React frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(extraction_router)
app.include_router(reports_router)
app.include_router(analytics_router)
app.include_router(topics_router)
app.include_router(benchmarks_router)


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """Root endpoint providing platform meta and quick links."""
    return JSONResponse(
        content={
            "platform": "Mining Document Intelligence & Reporting Platform",
            "problem_statement": "SIH 2026 - PS 26023 (CMPDI / Coal India Limited)",
            "status": "online",
            "phase": "Phase 5 & 6 - Automated Geological Reporting & Analytics Operational",
            "health_endpoint": "/api/health",
            "documents_endpoint": "/api/documents",
            "rag_endpoint": "/api/rag/query",
            "rag_status": "/api/rag/status",
            "extraction_status": "/api/extraction/status",
            "reports_status": "/api/reports/status",
            "analytics_summary": "/api/analytics/summary",
            "analytics_drilling": "/api/analytics/drilling",
            "analytics_resources": "/api/analytics/resources",
            "analytics_projects": "/api/analytics/projects",
            "analytics_quality": "/api/analytics/quality",
            "analytics_metrics": "/api/analytics/metrics",
            "analytics_comparison": "/api/analytics/comparison",
            "topics_summary": "/api/topics/summary",
            "topics_word_cloud": "/api/topics/word-cloud",
            "documentation": "/docs",
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
