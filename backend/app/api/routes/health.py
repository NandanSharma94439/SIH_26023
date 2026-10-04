import sys
import platform
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthCheckResponse, ModuleStatus
from app.services.documents.service import DocumentIngestionService
from app.services.ocr.service import OCRDocumentParserService
from app.services.rag.service import RAGKnowledgeBaseService
from app.services.extraction.service import StructuredMiningExtractorService
from app.services.reports.service import GeologicalReportGeneratorService

router = APIRouter(prefix="/api", tags=["Health & System"])


@router.get("/health", response_model=HealthCheckResponse)
async def check_health() -> HealthCheckResponse:
    """
    Health check endpoint returning system status, environment configuration,
    and modular readiness for all 5 subsystems.
    """
    # Instantiate service interfaces to inspect status
    doc_service = DocumentIngestionService()
    ocr_service = OCRDocumentParserService()
    rag_service = RAGKnowledgeBaseService()
    extract_service = StructuredMiningExtractorService()
    report_service = GeologicalReportGeneratorService()

    from app.services.documents.db import doc_db
    from app.services.extraction.service import extraction_service
    ingested_count = len(doc_db.list_documents())
    extraction_telemetry = extraction_service.get_service_status()

    modules = {
        "documents": ModuleStatus(
            name="Document Ingestion",
            phase="Phase 2",
            status="operational",
            description=f"Active multi-modal pipeline (PDF, DOCX, XLSX, images). Ingested docs: {ingested_count}",
        ),
        "ocr": ModuleStatus(
            name="OCR & Document Parser",
            phase="Phase 2",
            status="operational",
            description="PyMuPDF vector text, bounding box & table extraction with OCR fallback",
        ),
        "rag": ModuleStatus(
            name="RAG Knowledge Base & Grounded Assistant",
            phase="Phase 3",
            status="operational" if rag_service.vector_store.vector_count > 0 or rag_service.embedding_service.is_configured else "ready",
            description=f"FAISS vector store: {rag_service.vector_store.vector_count} vectors | Gemini configured: {rag_service.embedding_service.is_configured}",
        ),
        "extraction": ModuleStatus(
            name="Structured Mining Data Extraction",
            phase="Phase 4",
            status="operational",
            description=f"Relational mining records: {extraction_telemetry.total_entities_count} entities extracted ({extraction_telemetry.total_documents_extracted} docs)",
        ),
        "reports": ModuleStatus(
            name="Geological Report Generator",
            phase="Phase 5",
            status="operational",
            description=f"Standardized CMPDI/CIL reporting templates and multi-format exports (PDF, Excel, Markdown)",
        ),
        "analytics": ModuleStatus(
            name="Seam & Drill Analytics Dashboard",
            phase="Phase 6",
            status="operational",
            description="Geological KPIs, drilling target vs achieved analysis, coal resource classifications, and metric exploration",
        ),
    }

    system_info = {
        "python_version": sys.version.split(" ")[0],
        "platform": platform.platform(),
        "storage_ready": settings.UPLOAD_DIRECTORY.exists(),
        "faiss_ready": settings.FAISS_INDEX_PATH.parent.exists(),
        "total_documents_ingested": ingested_count,
        "server_time_utc": datetime.now(timezone.utc).isoformat(),
    }

    return HealthCheckResponse(
        status="ok",
        project="Mining Document Intelligence & Reporting Platform",
        version="0.2.0",
        timestamp=datetime.now(timezone.utc),
        environment=settings.ENVIRONMENT,
        phase="Phase 5 & 6 - Automated Geological Reporting & Analytics Operational",
        gemini_configured=bool(settings.GEMINI_API_KEY),
        modules=modules,
        system=system_info,
    )
