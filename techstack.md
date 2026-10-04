# GeoMine Intelligence — Technology Stack Specification

**Platform:** GeoMine Intelligence (CMPDI / Coal India Limited AI Exploration & Analysis Platform)  
**Document:** Technology Stack & Engineering Specifications (`techstack.md`)  
**Version:** 1.2 · 2026 Production Specification  

---

## 1. Architectural Overview

GeoMine Intelligence is engineered as a decoupled, high-performance client-server intelligence platform:
- **Client (Frontend):** Ultra-responsive Single Page Application (SPA) powered by React 19, Vite 8, GSAP animation orchestration, Lenis virtual smooth scrolling, and an industrial geological design system.
- **Server (Backend):** High-throughput, asynchronous REST API powered by Python 3.14 / 3.11+, FastAPI, Uvicorn, and Pydantic v2.
- **Data & Intelligence Layer:** SHA-256 deduplicated canonical document registry, FAISS dense vector retrieval database, and schema-guided relational mining extraction tables.

---

## 2. Frontend Technology Stack

| Layer / Concern | Technology | Version | Purpose & Rationale |
| :--- | :--- | :--- | :--- |
| **UI Framework** | **React** | `^19.2.8` | High-performance component-driven interface, concurrent rendering, and hooks architecture (`useMemo`, `useCallback`). |
| **DOM Engine** | **ReactDOM** | `^19.2.8` | Web client reconciliation and DOM management. |
| **Build Tooling & Bundler** | **Vite** | `^8.3.0` | Sub-second Hot Module Replacement (HMR), tree-shaking, and production Rollup/Rolldown minification. |
| **Animation & Choreography** | **GSAP (GreenSock)** | `^3.15.0` | Frame-rate independent kinematic choreography, staggered module entrance transitions (`animatePageEntrance`), and tactile hover lifts. |
| **Smooth Scrolling** | **Lenis** | `^1.3.26` | Studio Freight virtual smooth-scroll engine delivering momentum-based navigation across dense tables while respecting OS reduced-motion settings. |
| **Data Visualization** | **Recharts** | `^3.10.1` | Declarative SVG charting library powering Coal Grade distributions, Subsidiary Project breakdowns, and Borehole Depth analytics. |
| **Iconography** | **Lucide React** | `^1.48.0` | Comprehensive, consistent SVG icon set calibrated at `1.8` stroke width to maintain industrial design rigor. |
| **Linter & Static Analysis** | **Oxlint** | `^1.81.0` | Rust-based ultra-fast linter for JSX/JS code quality and static bug prevention. |
| **Styling & CSS Architecture** | **Vanilla CSS Design Tokens** | Native CSS3 | Bespoke tokens system avoiding generic UI framework bloat (no Tailwind/Bootstrap). Custom HSL variables, 3-tier frosted glass surfaces, and 5-tier umber elevation shadows. |

---

## 3. Backend Technology Stack

| Layer / Concern | Technology | Version | Purpose & Rationale |
| :--- | :--- | :--- | :--- |
| **Runtime Language** | **Python** | `3.14 / 3.11+` | Enterprise backend computing, scientific data manipulation, and AI interoperability. |
| **Web Framework** | **FastAPI** | `>=0.110.0` | Async ASGI framework with native OpenAPI 3.0 docs (`/docs`), automated validation, and dependency injection. |
| **ASGI Web Server** | **Uvicorn** | `>=0.28.0` | High-concurrency production ASGI server with auto-reload capabilities (`uvicorn.workers.UvicornWorker`). |
| **Data Validation & Schemas** | **Pydantic** | `>=2.6.0` | Strict schema serialization, input sanitization, and model-level validation for all API inputs and outputs. |
| **Environment Management** | **Python-Dotenv** | `>=1.0.0` | 12-factor application configuration loaded securely from `.env`. |
| **File Multipart Ingestion** | **Python-Multipart** | `>=0.0.9` | Streaming multi-file uploads for geological PDF, DOCX, and XLSX exploration records. |
| **HTTP Client** | **HTTPX** | `>=0.27.0` | Async HTTP client for outbound microservice and telemetry communications. |
| **Spreadsheet Parsing** | **OpenPyXL** | `>=3.1.2` | Excel table parser for complex borehole collars, drilling logs, and seam thickness spreadsheets. |
| **PDF Report Generation** | **ReportLab** | `>=4.1.0` | Programmatic PDF compiler for formatted geological summary exports. |

---

## 4. Artificial Intelligence, Vector & Data Layer

| Component | Technology | Implementation Details |
| :--- | :--- | :--- |
| **Dense Vector Index** | **FAISS (Facebook AI Similarity Search)** | In-memory `IndexFlatL2` / cosine index indexing **125 canonical vectors** for low-latency semantic search over borehole stratigraphy. |
| **Deduplication Engine** | **Cryptographic SHA-256** | File hash checksumming ensuring zero duplicate uploads and deterministic vector indexes across repeated ingestion runs. |
| **Retrieval Engine (RAG)** | **Hybrid Dense Retrieval** | High-precision cosine similarity query matching against chunked geological literature with strict verbatim evidence ranking. |
| **Topic Intelligence** | **TF-IDF & Domain Clustering** | Statistical term-frequency inverse-document-frequency ranking + domain-calibrated clustering into 6 core geological and mining topics. Zero external heavy dependencies. |
| **Provenance Tracking** | **Character & Page Attribution** | Complete character offset and page-level source references attached to every extracted entity and RAG answer. |
| **Structured Relational Store** | **SQLite / Relational Schema** | Local zero-maintenance persistence for 5 core mining entities: Borehole Logs, Coal Seams, Proximate Analyses, Mine Projects, and Geological Metrics. |

---

## 5. Design Tokens & Visual Hierarchy

The application avoids generic AI SaaS templates, implementing an industrial geological design language:

```css
/* Core Color Palette Tokens */
--stratum-base-light: #f5f1e8;    /* Sedimentary stratum linen / parchment */
--stratum-base-dark:  #171311;    /* Deep mineral slate / bituminous coal */
--stratum-accent:     #c87a32;    /* Calcined clay / warm amber */
--stratum-teal:       #4a8fa8;    /* Mineral oxidation cyan */
--stratum-emerald:    #4a9e72;    /* Ore grade emerald */

/* 5-Tier Umber Elevation Shadows */
--shadow-xs: 0 1px 2px rgba(23, 19, 17, 0.05);
--shadow-sm: 0 2px 4px rgba(23, 19, 17, 0.08);
--shadow-md: 0 4px 12px rgba(23, 19, 17, 0.10);
--shadow-lg: 0 8px 24px rgba(23, 19, 17, 0.14);
--shadow-xl: 0 16px 40px rgba(23, 19, 17, 0.20);

/* Frosted Glass Layers */
--glass-surface: rgba(245, 241, 232, 0.82);
--glass-border:  rgba(140, 110, 80, 0.18);
--glass-blur:    blur(16px);
```

### Typography Hierarchy:
- **Primary Technical UI:** `Instrument Sans`, `Inter`, system-ui.
- **Borehole & Metrics Mono:** `JetBrains Mono`, `SF Mono`, monospace.
- **Display Headlines:** `Syne`, `Outfit`, sans-serif.

---

## 6. Testing & Quality Assurance Suite

| Test Suite / Checker | Tool | Coverage & Status |
| :--- | :--- | :--- |
| **Backend Integration & Unit Tests** | **Pytest** | **33/33 Tests Passing** across API routing, health checks, document deduplication, extraction normalization, and RAG retrieval. |
| **Frontend Production Compilation** | **Vite / Rollup** | **0 Errors, 0 Warnings** via `npm run build`. |
| **Static Code Quality** | **Oxlint** | Linter verification across all React components and utility services. |
| **Live Telemetry Monitoring** | **FastAPI Health Endpoint** | Auto-polled `/api/v1/health` verifying multi-subsystem uptime every 30 seconds. |

---

## 7. Topology & Runtime Ports

```
┌─────────────────────────────────┐       HTTP / JSON        ┌─────────────────────────────────┐
│        React 19 Frontend        │ ───────────────────────> │         FastAPI Backend         │
│     http://localhost:5173       │ <─────────────────────── │      http://127.0.0.1:8000      │
└─────────────────────────────────┘      (CORS Enabled)      └─────────────────────────────────┘
                 │                                                            │
                 ▼                                                            ▼
      Vite Development Server                                      Uvicorn ASGI Web Server
   GSAP + Lenis Kinematic Engine                                FAISS Vector Store + SQLite DB
```
