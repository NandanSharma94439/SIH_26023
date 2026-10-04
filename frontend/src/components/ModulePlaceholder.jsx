import React from 'react';
import { ArrowRight, Server, ChevronLeft } from 'lucide-react';

const MODULE_DETAILS = {
  ingestion: {
    title: 'Document Intelligence',
    service: 'backend/app/services/documents/ & backend/app/services/ocr/',
    desc: 'High-throughput upload pipeline for CMPDI Geological Reports, borehole lithology sheets, and mining PDFs. Integrates PyMuPDF with OCR fallback (Tesseract/EasyOCR) for historical scans.',
    deliverables: [
      'Multi-part file upload with strict MIME verification',
      'Dual extraction: PyMuPDF for native vector text, Tesseract for scanned legacy logs',
      'Page-level bounding boxes and detected table structures',
      'Local disk isolation under storage/uploads/',
    ],
  },
  rag: {
    title: 'Knowledge Assistant',
    service: 'backend/app/services/rag/',
    desc: 'Conversational assistant with strict page-level source attribution. Uses domain-specific geological chunking and FAISS local vector indices powered by Gemini text-embedding-004.',
    deliverables: [
      'Geological domain chunker (preserves seam, borehole, and stratigraphic headers)',
      'Vector indexing via FAISS (IndexFlatIP)',
      'Backend-only Gemini API integration (no client key exposure)',
      'Citation engine linking answers to exact document page and coordinate boxes',
    ],
  },
  extraction: {
    title: 'Structured Data Extraction',
    service: 'backend/app/services/extraction/',
    desc: 'Automated entity extraction pipeline converting geological narratives and tables into structured database models (SQLite / extraction.db) adhering to ISP and UNFC mining standards.',
    deliverables: [
      'Pydantic schemas for Coal Seams (thickness, depth, parting)',
      'Borehole Lithology Logs (collar coordinates, RL, seam intersections)',
      'Proximate Analysis (Ash%, Moisture%, Volatile Matter, GCV)',
      'Overburden stripping ratio & reserve calculations',
    ],
  },
  reports: {
    title: 'Geological Reports',
    service: 'backend/app/services/reports/',
    desc: 'Automated document synthesis for CMPDI planners. Compiles structured metrics into standardized CMPDI formats with multi-format export (Markdown, PDF, Excel).',
    deliverables: [
      'CMPDI Geological Summary Report generator',
      'Multi-document seam correlation assessment',
      'Statutory compliance and audit checklist builder',
      'Direct export to Markdown, PDF, and XLSX',
    ],
  },
  analytics: {
    title: 'Mining Analytics',
    service: 'frontend/src/components/analytics/ (Recharts)',
    desc: 'Interactive data visualization module. Renders borehole stratigraphy cross-sections, seam thickness histograms, and coal grade distributions.',
    deliverables: [
      'Interactive Borehole Stratigraphy Column Visualizer',
      'Seam Thickness Distribution Histograms',
      'Proximate Analysis GCV vs Ash Content Scatter Plots',
      'Stripping Ratio Forecast Curves',
    ],
  },
};

export default function ModulePlaceholder({ moduleId, onBackToTelemetry }) {
  const details = MODULE_DETAILS[moduleId] || {
    title: 'Module',
    service: 'backend/app/services/',
    desc: 'This module is part of the platform architecture.',
    deliverables: [],
  };

  return (
    <div className="module-placeholder glass-panel">
      <div className="placeholder-header">
        <span className="badge badge-success">Operational</span>
        <h2 className="placeholder-title">{details.title}</h2>
        <p className="placeholder-desc">{details.desc}</p>
      </div>

      <div className="placeholder-service-info">
        <div className="service-info-row">
          <Server size={14} className="info-icon" aria-hidden="true" />
          <span className="service-info-label">Service path:</span>
          <code>{details.service}</code>
        </div>
      </div>

      <div className="placeholder-deliverables">
        <h4 className="deliverables-heading">Capabilities</h4>
        <div className="deliverables-grid">
          {details.deliverables.map((item, i) => (
            <div key={i} className="deliverable-item">
              <ArrowRight size={13} className="deliverable-arrow" aria-hidden="true" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="placeholder-footer">
        <button className="back-btn" onClick={onBackToTelemetry}>
          <ChevronLeft size={14} aria-hidden="true" />
          <span>Return to Platform Overview</span>
        </button>
      </div>
    </div>
  );
}
