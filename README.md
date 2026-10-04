# Mining Document Intelligence & Reporting Platform
### Smart India Hackathon (SIH) 2026 — Problem Statement 26023
**Organization**: Ministry of Coal / Central Mine Planning & Design Institute (CMPDI) / Coal India Limited (CIL)  
**Problem Statement Title**: *AI-Powered Geological, Mining and other Reporting Solution for CMPDI/CIL subsidiaries*

---

## 📌 Project Overview

Geological exploration and mining planning generate vast volumes of complex technical documentation: **Geological Reports (GRs)**, **Borehole Geophysical & Lithology Logs**, **Project Feasibility Reports (PRs)**, and **Mine Closure & Statutory Compliance Plans**.

The **Mining Document Intelligence & Reporting Platform** is an enterprise-grade AI solution engineered to:
1. **Ingest & Parse**: Process digital and scanned geological documents with native PDF parsing and OCR fallback.
2. **Search with Grounding (RAG)**: Provide conversational search with strict, verifiable page- and paragraph-level citations.
3. **Extract Structured Mining Metrics**: Automatically extract seam thicknesses, borehole collar coordinates, proximate analysis (Ash%, Moisture%, VM%, GCV), and reserve classifications (ISP/UNFC).
4. **Automate Reporting**: Generate standardized CMPDI geological reports, seam correlation memos, and compliance summaries with multi-format export (PDF, Markdown, Excel).

---

## 🏗️ Architecture Principle: Modular Pipeline

The system is designed with strict modular separation so that each subsystem can be developed, tested, and updated independently without cascading breaks:

```
[Document Ingestion] ➡️ [OCR & Parsing] ➡️ [Chunking & Embeddings] ➡️ [FAISS Vector Search] ➡️ [Grounded RAG] ➡️ [Structured Extraction] ➡️ [Report Generation]
```

Detailed architectural blueprints and milestone plans are documented in [`docs/architecture.md`](docs/architecture.md).

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
|:---|:---|:---|
| **Frontend** | React 19 + Vite + Vanilla CSS | Modern, responsive dashboard shell & data visualizer |
| **Backend API** | Python 3.10+ / FastAPI / Pydantic v2 | High-performance asynchronous REST API gateway |
| **AI / LLM** | Google Gemini 1.5 Pro & Flash (Backend Only) | Semantic synthesis, grounded citations, structured JSON extraction |
| **Embeddings** | Google Gemini `text-embedding-004` | 768-dimensional geological semantic representations |
| **Vector Search** | FAISS (Facebook AI Similarity Search) | High-speed local similarity search & vector persistence |
| **Document Processing** | PyMuPDF (fitz) + Tesseract/EasyOCR | Native vector PDF extraction + scanned legacy log OCR fallback |
| **Database** | PostgreSQL / Supabase | Relational storage for structured mining entities & borehole logs |
| **Analytics / Charts** | Recharts | Seam thickness histograms & borehole lithology visualization |

---

## 📂 Repository Structure

```
SIH-26023/
├── .env.example                     # Global environment configuration template
├── .gitignore                        # Security rules for secrets, uploads, indices, caches
├── README.md                         # Project documentation and setup guide
├── docs/
│   └── architecture.md               # End-to-end architecture & milestone sequence
├── backend/
│   ├── .env                          # Local environment variables (ignored by git)
│   ├── .env.example                  # Backend environment template
│   ├── requirements.txt              # Core and staged Python dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entrypoint, CORS, lifespan hooks
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py             # Settings management & directory bootstrap
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       └── health.py         # GET /api/health endpoint
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── health.py             # Pydantic schemas for telemetry responses
│   │   └── services/                 # Modular service architecture
│   │       ├── __init__.py
│   │       ├── documents/            # Milestone 2: File ingestion & validation
│   │       ├── ocr/                  # Milestone 2: PyMuPDF & OCR fallback
│   │       ├── rag/                  # Milestone 3: FAISS & Gemini RAG
│   │       ├── extraction/           # Milestone 4: Structured mining data
│   │       └── reports/              # Milestone 5: Geological report synthesis
│   └── storage/                      # Local runtime storage (ignored by git)
│       ├── uploads/                  # Raw ingested files
│       ├── processed/                # Normalized text & bounding box JSONs
│       └── faiss_index/              # Persisted vector index & metadata
└── frontend/
    ├── .env                          # Frontend environment config
    ├── .env.example                  # Frontend environment template
    ├── package.json                  # React 19, Vite, Lucide-react, Recharts
    ├── vite.config.js                # Vite build configuration
    ├── index.html                    # HTML5 entrypoint with Google Fonts
    └── src/
        ├── main.jsx                  # React DOM mount
        ├── App.jsx                   # Dashboard shell & telemetry state
        ├── App.css                   # Responsive layout & component styles
        ├── index.css                 # Industrial dark design tokens & utilities
        ├── services/
        │   └── api.js                # Frontend API client layer
        └── components/
            ├── Header.jsx            # Live telemetry ping & branding
            ├── Sidebar.jsx           # Milestone navigation
            ├── TelemetryOverview.jsx # Live /api/health telemetry cards
            ├── ModuleGrid.jsx        # Backend subsystem status cards
            ├── RoadmapView.jsx       # 6-phase sprint timeline
            └── ModulePlaceholder.jsx # Upcoming milestone inspection views
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: Version 3.10 to 3.14
- **Node.js**: Version 18.0 or higher
- **npm**: Version 9.0 or higher

---

### 2. Backend Setup & Run

1. Open a terminal in the project root:
   ```bash
   cd backend
   ```

2. (Optional) Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment settings:
   ```bash
   cp .env.example .env
   # Edit .env to set your GEMINI_API_KEY when ready for Phase 3
   ```

5. Launch the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. Verify backend status:
   - Health endpoint: [http://localhost:8000/api/health](http://localhost:8000/api/health)
   - Interactive Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc alternative docs: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 3. Frontend Setup & Run

1. Open a second terminal in the project root:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Verify environment configuration:
   ```bash
   cp .env.example .env
   # Default points to VITE_API_BASE_URL=http://localhost:8000
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

The dashboard shell will immediately connect to `http://localhost:8000/api/health`, measuring latency and rendering real-time system telemetry and module readiness.

---

## 🗺️ Milestone Roadmap

| Milestone | Stage | Description | Status |
|:---|:---|:---|:---|
| **Phase 1** | **Monorepo & API Foundation** | Clean monorepo structure, FastAPI health check, React dashboard shell, modular service stubs, documentation. | **Active / Complete** |
| **Phase 2** | **Document Ingestion & OCR** | PDF/DOCX multi-part upload, PyMuPDF parsing, OCR fallback pipeline for scanned historical borehole logs. | Planned Next |
| **Phase 3** | **FAISS Vector Index & RAG** | Domain-aware chunking, Gemini `text-embedding-004`, FAISS indexing, conversational Q&A with page-level citations. | Milestone 3 |
| **Phase 4** | **Structured Mining Extraction** | Pydantic schemas for coal seam metrics, borehole logs, proximate analysis; PostgreSQL persistence. | Milestone 4 |
| **Phase 5** | **Automated Reporting Engine** | Standardized CMPDI Geological Summary templates, multi-document synthesis, PDF/Excel export. | Milestone 5 |
| **Phase 6** | **Analytics & Visualizations** | Recharts visual analytics (borehole lithology visualizer, seam thickness distributions), production hardening. | Milestone 6 |

---

## 🔒 Security & PSU Compliance

- **Zero Client-Side LLM Leakage**: The Gemini API key and credentials remain strictly on the FastAPI server. The React client never contacts AI APIs directly.
- **Local Storage Isolation**: Raw geological logs and vector indices are stored in local, git-ignored directories (`storage/`).
- **Deterministic Citations**: The RAG prompt contract enforces that every answer must provide verifiable page and coordinate citations from ingested documents.
