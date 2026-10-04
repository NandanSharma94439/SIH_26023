import React from 'react';
import { CheckCircle2, ArrowRight } from 'lucide-react';

const MILESTONES = [
  {
    id: 'platform',
    title: 'Platform Foundation',
    subtitle: 'Monorepo, FastAPI, React 19, Vite',
    items: [
      'Clean monorepo layout (frontend/, backend/, docs/)',
      'FastAPI /api/health endpoint & CORS setup',
      'React 19 dashboard shell & typed API client',
      'Security-hardened configuration & modular service architecture',
    ],
  },
  {
    id: 'ingestion',
    title: 'Document Intelligence',
    subtitle: 'Multi-modal parser, OCR pipeline',
    items: [
      'Multi-part upload with MIME verification',
      'PyMuPDF extraction — bounding boxes, text spans, tables',
      'OCR fallback (Tesseract / EasyOCR) for scanned borehole logs',
      'Character-doubling normalization for legacy CMPDI PDFs',
    ],
  },
  {
    id: 'rag',
    title: 'Knowledge Assistant',
    subtitle: 'FAISS vector index, grounded RAG',
    items: [
      'Domain-aware semantic chunking (seams, stratigraphy, boreholes)',
      'Gemini text-embedding-004 integration',
      'FAISS local vector index with metadata mapping',
      'Conversational RAG with strict page-level citations',
    ],
  },
  {
    id: 'extraction',
    title: 'Structured Data Extraction',
    subtitle: 'Relational mining entity store',
    items: [
      'Pydantic schemas for seams, boreholes, proximate analysis',
      'Gemini structured JSON extraction',
      'SQLite persistence layer (extraction.db)',
      'Validation against ISP / UNFC mining reserves standards',
    ],
  },
  {
    id: 'reports',
    title: 'Geological Reports',
    subtitle: 'CMPDI automated reporting engine',
    items: [
      'CMPDI Geological Summary templates',
      'Multi-document seam correlation memos',
      'Automated export — Markdown, styled PDF, Excel workbooks',
    ],
  },
  {
    id: 'analytics',
    title: 'Mining Analytics',
    subtitle: 'Seam & drill visualizations',
    items: [
      'Borehole lithology stratigraphy chart',
      'Coal seam thickness distribution histograms',
      'Proximate analysis ash / moisture / GCV comparison',
    ],
  },
];

export default function RoadmapView() {
  return (
    <div className="roadmap-section glass-panel">
      <div className="section-header">
        <div>
          <h2 className="section-title">Platform Architecture</h2>
          <p className="section-subtitle">
            Six integrated modules — all operational
          </p>
        </div>
        <span className="badge badge-success">6 Modules Operational</span>
      </div>

      <div className="roadmap-timeline">
        {MILESTONES.map((m, idx) => (
          <div key={m.id} className="timeline-step completed">
            <div className="timeline-marker">
              <CheckCircle2 size={18} className="marker-icon completed" aria-hidden="true" />
              {idx < MILESTONES.length - 1 && <div className="timeline-line" />}
            </div>

            <div className="timeline-content">
              <div className="timeline-header">
                <span className="badge badge-success">Live</span>
                <div>
                  <h4 className="timeline-title">{m.title}</h4>
                  <p className="timeline-subtitle">{m.subtitle}</p>
                </div>
              </div>

              <ul className="timeline-list">
                {m.items.map((it, i) => (
                  <li key={i} className="timeline-item">
                    <ArrowRight size={11} className="bullet-arrow" aria-hidden="true" />
                    <span>{it}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
