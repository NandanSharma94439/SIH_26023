# Mining Document Intelligence & Reporting Platform
## System Architecture & Technical Specification
### SIH 2026 — Problem Statement 26023 (CMPDI / Coal India Limited)

---

## 1. Executive Summary & Problem Context

In the mining and geological sector—specifically for **Coal India Limited (CIL)** and its exploration and planning subsidiary, the **Central Mine Planning & Design Institute (CMPDI)**—thousands of complex technical reports are produced and archived annually. These include:
- **Geological Reports (GRs)** with extensive stratigraphic columns, coal seam lithology, and borehole descriptions.
- **Borehole Geophysical Logs** recording gamma-ray, density, and resistivity traces alongside lithological logs.
- **Project Reports (PRs)** detailing opencast/underground mine design, stripping ratios, stripping limits, and equipment allocation.
- **Environmental & Mine Closure Plans** outlining statutory compliance, afforestation, land reclamation, and monitoring logs.

### Key Operational Challenges
1. **Unstructured & Scanned Legacy Data**: Decades of historical exploration records exist in scanned PDFs, degraded printouts, and varied tabular formats.
2. **Manual Seam Correlation**: Correlating coal seams (e.g., Seam I through Seam X) across hundreds of boreholes requires tedious manual cross-referencing.
3. **Information Silos**: Planners must manually extract proximate analysis (Ash%, Moisture%, Volatile Matter, GCV) and calculate reserves according to Indian Standard Procedure (ISP) or UNFC classifications.
4. **Auditability & Traceability**: Mining reporting demands 100% auditable citations linking every extracted metric to the exact source page, borehole collar ID, or tabular cell.

The **Mining Document Intelligence & Reporting Platform** is designed to solve these challenges through a modular, enterprise-grade architecture.

---

## 2. System Architecture Blueprint

```
+-----------------------------------------------------------------------------------+
|                           FRONTEND CLIENT TIER                                    |
|  React 19 + Vite + Modern Vanilla CSS (SPA)                                       |
|  - Minimal Professional Dashboard Shell                                           |
|  - Live Backend Service Health Telemetry                                          |
|  - Document Management & Viewer (PDF bounding-box highlights)                     |
|  - Conversational RAG Query Console with Page-Level Citations                     |
|  - Structured Mining Data Inspector & Recharts Analytics                          |
|  - Automated CMPDI/CIL Report Generator & Export Center                            |
+----------------------------------------+------------------------------------------+
                                         | REST API (HTTP / JSON / Multi-part)
                                         v
+-----------------------------------------------------------------------------------+
|                            BACKEND API TIER (FastAPI)                             |
|  FastAPI Application Server + Pydantic v2 + CORS Middleware + Uvicorn Worker      |
|  - /api/health (System status, environment, module telemetry)                     |
|  - /api/v1/documents (Ingestion, validation, storage)                             |
|  - /api/v1/ocr (PyMuPDF parser, table extractor, Tesseract fallback)              |
|  - /api/v1/rag (FAISS similarity search, Gemini grounded answer generation)       |
|  - /api/v1/extraction (Structured seam, borehole & proximate analysis extraction) |
|  - /api/v1/reports (CMPDI report synthesis, PDF/Excel/Markdown generator)         |
+----------------------------------------+------------------------------------------+
                                         |
     +-------------------+---------------+-------------------+-------------------+
     |                   |                                   |                   |
     v                   v                                   v                   v
+------------+  +--------------------+             +------------------+  +----------------+
| Document   |  | OCR & Parser       |             | RAG & Vector     |  | Structured     |
| Ingestion  |  | Service (ocr/)     |             | Service (rag/)   |  | Extraction     |
| Service    |  |                    |             |                  |  | Service        |
|            |  | - PyMuPDF (fitz)   |             | - Semantic Chunk |  |                |
| - File val |  | - Native text      |             | - Gemini Embed   |  | - Seam Metrics |
| - MIME chk |  | - Table detection  |             | - FAISS Index    |  | - Borehole Logs|
| - Metadata |  | - OCR Fallback     |             | - Citation Track |  | - Proximate A. |
+-----+------+  +---------+----------+             +--------+---------+  +-------+--------+
      |                   |                                 |                    |
      v                   v                                 v                    v
+-----------------------------------------------------------------------------------+
|                             DATA & PERSISTENCE TIER                               |
|  1. Local / Cloud Object Storage: Raw PDFs, Scanned Logs, Exported Reports        |
|  2. FAISS Vector Database: High-dimensional embeddings with chunk metadata       |
|  3. Relational DB (SQLite / extraction.db): Structured entities, borehole records      |
|  4. Gemini LLM API (Backend Only): text-embedding-004 & Gemini 1.5 Pro/Flash      |
+-----------------------------------------------------------------------------------+
```

---

## 3. Modular Service Architecture

The system enforces strict separation of concerns across 5 core backend service modules:

### 3.1 Document Ingestion Service (`app/services/documents/`)
- **Purpose**: Secure ingestion, validation, and storage of geological documents.
- **Accepted Formats**: Digital PDF, scanned PDF, DOCX, XLSX, TIFF, PNG/JPEG.
- **Responsibilities**:
  - File signature & MIME-type verification (preventing malicious extension spoofing).
  - Storage partitioning (`storage/uploads/{doc_id}/raw_file`).
  - Metadata indexing (filename, file size, SHA256 checksum, upload timestamp, doc classification).

### 3.2 OCR & Document Parser Service (`app/services/ocr/`)
- **Purpose**: Multi-modal document parsing with high-accuracy fallback.
- **Pipeline**:
  1. **Primary Layer (PyMuPDF / fitz)**: Extracts digital vector text, character coordinates, and tabular bounding boxes with sub-millimeter precision.
  2. **Heuristic Quality Check**: Evaluates text density and extraction completeness. If a page has < 50 characters or is an image layer, triggers fallback.
  3. **Fallback Layer (Tesseract / EasyOCR)**: Converts page image to grayscale, applies Otsu thresholding and noise removal, and performs OCR tailored to tabular geological logs.
  4. **Output Representation**: Standardized JSON list of pages with bounding boxes, text spans, and recognized tabular grids.

### 3.2.1 PDF Table Extraction & Character-Doubling Normalization Layer
- **Root Cause Analysis (`find_tables()` vs `get_text("text")`)**:
  Certain enterprise/legacy mining PDFs (such as CMPDI's `accounts0607.pdf`) contain duplicate, overlapping vector text objects placed for faux-bolding, ink-stroke thickening, or print registration (e.g., overlapping text blocks at coordinates $x=105.62$ and $x=108.12$).
  - When extracting raw page text (`page.get_text("text")` or `page.get_text("blocks")`), PyMuPDF's layout engine performs de-duplication across overlapping glyphs, producing clean text (`GEOLOGICAL REPORTS`, `CMPDI`).
  - However, PyMuPDF's table extraction engine (`page.find_tables().tables[].extract()`) queries raw glyph objects within cell bounding boxes without de-duplicating overlapping text streams. As a result, characters from both overlapping layers are interleaved sequentially into doubled strings:
    - `GGEEOOLLOOGGIICCAALL RREEPPOORRTTSS` instead of `GEOLOGICAL REPORTS`
    - `AAggeennccyy` instead of `Agency`
    - `CCMMPPDDII` instead of `CMPDI`
    - `11,,9922,,000000` instead of `1,92,000`
    - `110033%%` instead of `103%`
    - `771155` instead of `715`
- **Post-Extraction Normalization Strategy (`app/services/documents/table_normalization.py`)**:
  To resolve this artifact safely without altering the underlying PDF or breaking raw text/OCR:
  1. **Strict Doubling Invariant**: A token is recognized as character-doubled if and only if it has an even length and satisfies `token[::2] == token[1::2]`.
  2. **Collapse Mechanism**: Collapses valid doubled tokens by taking every second character (`token[::2]`).
  3. **Zero False Positives on Legitimate Words**: Words with naturally repeated letters are mathematically immune:
     - `SUCCESS`: length 7 (odd $\implies$ never matches).
     - `COAL`: length 4, `COAL[::2] = "CA" != "OL" = COAL[1::2]` ($\implies$ never matches).
     - `COMMITTEE`: length 9 (odd $\implies$ never matches).
     - `BOOKKEEPER`: length 10, `"BOKEE" != "OKPER"` ($\implies$ never matches).
     - `SEAM`, `MINE`, `ASH`, `DRILLING`, `BOREHOLE`, `CALORIFIC` are all fully preserved.
  4. **Punctuation & Layout Handling**: Inspects leading/trailing punctuation so formatted values (`CCMMPPDDII:`, `11,,9922,,000000`, `110033%%`, `((mmeettrree))`, `GGoovvttss..`, `BBEE|`) collapse cleanly while preserving inter-word whitespace (`re.split(r'(\s+)', line)`) and multiline linebreaks (`\n`).
  5. **Table-Aware Context Protection**: Protects legitimate numeric values and codes (`11`, `22`, `1100`, `BH-01`, `Seam II`, `64.50`) in clean tables.
  6. **Isolation**: Applied exclusively to extracted table headers and cells. Original stored PDFs, OCR fallbacks, text blocks, and native page text extractions remain completely unaltered.

### 3.3 RAG Knowledge Base & Vector Search Service (`app/services/rag/`)
- **Purpose**: Searchable domain-aware knowledge base answering geological, mining, and operational queries with strict page-level source citations.
- **Components & Pipeline**:
  1. **Domain-Aware Semantic Chunking (`DomainAwareChunker`)**:
     - Consumes pre-processed document pages directly from the repository (`storage/processed/{doc_id}.json`) without re-parsing raw files.
     - **Tabular Data Preservation**: Formats table grids row-by-row, keeping column headers explicitly paired with cell values (`Col1: Val1 | Col2: Val2`), preventing cell value detachment from headers.
     - **Section & Header Tracking**: Automatically detects geological headings (e.g., `1.0 INTRODUCTION & STRATIGRAPHY`, `PART: B ANNUAL PERFORMANCE OVERVIEW`, `BOREHOLE LOG`) and keeps them bound to downstream narrative blocks.
     - **Chunk Size & Overlap**: Default 800 characters with 150-character sliding-window overlap respecting sentence boundaries (`CHUNK_SIZE`, `CHUNK_OVERLAP`).
     - **Metadata Payload**: `chunk_id`, `document_id`, `filename`, `file_type`, `page_number`, `section`, `source_type` (`text`, `table`, `ocr`), `dimensions`, `bbox`.
  2. **Gemini Embedding Service (`GeminiEmbeddingService`)**:
     - Generates 768-dimensional dense vectors using Google Gemini `text-embedding-004` through the `google.genai` SDK.
     - Credentials kept strictly backend-side via `GEMINI_API_KEY`.
     - Zero-mock policy: Returns explicit configuration errors (`HTTP 400`) if the API key is not configured, preventing synthetic data leakage.
  3. **Persistent FAISS Vector Store (`FAISSVectorStore`)**:
     - In-memory `faiss.IndexFlatIP` utilizing L2-normalized vectors for exact Cosine Similarity calculations.
     - Serialized to disk under `storage/faiss_index/mining_docs.index` with metadata in `mining_docs_metadata.pkl`.
     - Automatically restores existing indexes on backend startup.
     - Document-level replacement & deduplication using `faiss.IDSelectorBatch` to prevent vector duplication upon document updates.
  4. **Grounded Synthesis Engine (`GroundedRAGService`)**:
     - System prompt strictly enforces factual grounding against retrieved document chunks:
       - *"Answer ONLY using facts, figures, dates, and measurements directly present in the supplied Document Evidence."*
       - *"Never invent facts, borehole IDs, seam names, or metrics."*
       - *"Cite sources in brackets like [Filename, Page X] directly after each factual statement."*
       - *"If the provided evidence does not contain the answer, explicitly state: 'The requested information was not found in the indexed documents.'"*
     - Generates answers using `gemini-1.5-flash` at low temperature ($T=0.1$) for deterministic factuality.
  5. **REST API Interface (`app/api/routes/rag.py`)**:
     - `POST /api/rag/query`: Semantic retrieval and grounded synthesis with source evidence.
     - `POST /api/rag/index/{document_id}`: Vectorizes and indexes a single processed document.
     - `POST /api/rag/index-all`: Bulk vectorizes all registered processed documents.
     - `GET /api/rag/status`: Real-time vector count, dimensions, model info, and configuration telemetry.
  6. **Interactive UI (`frontend/src/components/RAGAssistant.jsx`)**:
     - Natural-language query bar with sample mining question pills.
     - Grounded AI response card with evidence support status badge (`Supported by Evidence` / `Insufficient Evidence`).
     - Interactive source cards with cosine match percentage, page badge, source type, and expandable evidence snippet.
     - Live knowledge base telemetry strip with "Index All" trigger.

### 3.4 Structured Mining Extraction Service (`app/services/extraction/`)
- **Purpose**: Schema-guided, validated extraction of domain-specific mining entities into persistent relational models with strict document/page provenance.
- **Components & Pipeline**:
  1. **Pydantic Domain Schemas (`app/schemas/extraction.py`)**:
     - **Coal Seam**: `seam_id`, `borehole_id`, `depth_from`, `depth_to`, `thickness`, `coal_grade`, `category`, `gross_reserves_mt`, `extractable_reserves_mt`.
     - **Borehole Logs**: `borehole_id`, `mine_project`, `latitude`, `longitude`, `collar_elevation`, `total_depth`, `lithology`.
     - **Proximate Analysis**: `seam_id`, `borehole_id`, `moisture_percent`, `ash_percent`, `volatile_matter_percent`, `fixed_carbon_percent`, `gross_calorific_value`, `units`.
     - **Mines & Projects**: `project_name`, `subsidiary`, `location`, `block_name`, `target_production`, `target_production_unit`, `stripping_ratio`, `life_of_mine_years`.
     - **Geological Metrics**: `metric_name`, `metric_value`, `unit`, `year_period`, `category`.
     - **Provenance Guarantee**: Every entity enforces mandatory `document_id`, `source_document`, `source_page`, `evidence_text`, and `extraction_timestamp`.
  2. **Extraction Engine (`StructuredMiningExtractorService`)**:
     - Evaluates processed document representations (`storage/processed/*.json`) without re-parsing raw PDFs.
     - Selects domain-relevant candidate pages based on mining keyword density and table structure.
     - Calls Gemini with deterministic zero-temperature JSON mode (`response_mime_type="application/json"`).
     - Performs strict Pydantic validation, safe numeric extraction (`_clean_float`), and verifies that extracted entities match verbatim text on the cited page.
  3. **Relational Database Store (`app/services/extraction/db.py`)**:
     - Manages SQLite relational schema across 5 normalized tables (`mines_projects`, `boreholes`, `coal_seams`, `proximate_analyses`, `geological_metrics`).
     - Prevents duplicate records on document reprocessing by atomically purging previous extractions before inserting new validated records.
  4. **REST API Interface (`app/api/routes/extraction.py`)**:
     - `POST /api/extraction/document/{document_id}`: Extracts structured entities for a single document.
     - `POST /api/extraction/all`: Batch extracts across all registered documents.
     - `GET /api/extraction/status`: Telemetry of entity counts and processed documents.
     - `GET /api/extraction/boreholes`: List borehole logs with search and document filters.
     - `GET /api/extraction/seams`: List coal seams with stratigraphy and reserves.
     - `GET /api/extraction/proximate-analysis`: List coal quality and GCV parameters.
     - `GET /api/extraction/mines`: List feasibility and mining projects.
     - `GET /api/extraction/metrics`: List exploration statistics and departmental targets.
  5. **Frontend Extraction Console (`frontend/src/components/StructuredExtraction.jsx`)**:
     - Telemetry strip displaying total entities and breakdown counts.
     - Tabbed navigation across all 5 domain categories.
     - Filter and search bar.
     - Relational tables with formatted units, badges, and expandable verbatim evidence quotes.
     - Document extraction picker and bulk extraction controls.

### 3.5 Geological Report Generator Service (`app/services/reports/`)
- **Purpose**: Standardized, automated document synthesis for CMPDI and CIL subsidiary planning departments.
- **Capabilities**:
  - Standardized CMPDI Geological Summary Report.
  - Seam-by-seam reserve reconciliation memo.
  - Statutory mine compliance & closure status checklist.
  - Multi-format generation: Markdown, styled HTML/PDF, and structured XLSX spreadsheets.

---

## 4. Frontend Architecture & Shell

Built with React 19 and Vite using vanilla CSS for maximum design freedom and zero bloated CSS dependencies.
- **Dashboard Shell**: Clean, high-density industrial mining UI themed with deep slate (`#0B0F19`), rich dark charcoal (`#111827`), amber ore accents (`#F59E0B`), and emerald telemetry badges (`#10B981`).
- **Telemetry System**: Live polling of backend `/api/health` displaying active microservices, latency, and system environment.
- **Navigation Hub**: Modular tabs mapped directly to milestone delivery stages:
  - System Overview & Live Telemetry (Phase 1)
  - Document Repository & Ingestion (Phase 2)
  - Search & Grounded RAG Assistant (Phase 3)
  - Structured Seam & Borehole Extraction (Phase 4)
  - Automated Geological Reporting (Phase 5)
  - Analytics & Seam Visualizer (Phase 6)

---

## 5. Milestone Sequence & Roadmap

| Milestone | Stage | Key Deliverables | Status |
|:---|:---|:---|:---|
| **Phase 1** | **Monorepo & API Shell** | Monorepo layout (`frontend/`, `backend/`, `docs/`), FastAPI `/api/health`, minimal professional dashboard shell, API service layer, `.gitignore`, architecture documentation. | **Complete / Operational** |
| **Phase 2** | **Document Ingestion & Multi-Modal Parser** | Multi-part upload (`/api/documents/upload`), PyMuPDF native parser, OCR fallback, DOCX & XLSX multi-sheet extractors, SQLite metadata registry, table normalization layer, drag/drop frontend inspector. | **Complete / Operational** |
| **Phase 3** | **Vector Knowledge Base & Grounded RAG** | Domain-aware chunking, Gemini embedding pipeline (`gemini-embedding-001`), FAISS persistent vector store, grounded Q&A with strict page citations (`gemini-3.5-flash-lite`), RAGAssistant frontend console. | **Complete / Operational** |
| **Phase 4** | **Structured Mining Data Extraction** | Pydantic domain schemas (Seams, Boreholes, Proximate, Mines, Metrics), Gemini structured JSON extraction, relational SQLite storage with deduplication, extraction REST API, StructuredExtraction frontend console. | **Complete / Operational** |
| **Phase 5** | **Automated Reporting Engine** | CMPDI geological report generator, multi-document synthesis, PDF/Excel export pipeline. | Planned Next |
| **Phase 6** | **Analytics & Production Hardening** | Recharts visual analytics (borehole lithology visualizer, seam thickness distributions), caching, Dockerization, and end-to-end evaluation. | Milestone 6 |

---

## 6. Security, Privacy & PSU Governance Principles

1. **Air-Gap & Backend Encapsulation**: Gemini API keys and cloud credentials reside strictly on the backend server. The frontend client never has direct access to AI provider endpoints.
2. **Deterministic Citations**: Hallucination mitigation is built into the RAG prompt contract. Any response lacking verified page grounding is rejected.
3. **Local Storage Isolation**: Raw geological surveys, confidential borehole logs, and FAISS indices are isolated in local ignored storage (`storage/`) and protected against accidental commits.
