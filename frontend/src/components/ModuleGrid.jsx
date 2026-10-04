import React from 'react';
import {
  Files,
  Search,
  MessageSquare,
  Database,
  FileBarChart,
  BarChart3,
  ShieldCheck,
} from 'lucide-react';

const MODULE_META = {
  documents: {
    icon: Files,
    tech: 'PyMuPDF / Multi-part Upload',
    folder: 'backend/app/services/documents/',
    label: 'Document Intelligence',
  },
  ocr: {
    icon: Search,
    tech: 'PyMuPDF + Tesseract / EasyOCR',
    folder: 'backend/app/services/ocr/',
    label: 'Document Intelligence',
  },
  rag: {
    icon: MessageSquare,
    tech: 'FAISS + Gemini Embeddings',
    folder: 'backend/app/services/rag/',
    label: 'Knowledge Assistant',
  },
  extraction: {
    icon: Database,
    tech: 'Pydantic v2 + SQLite / extraction.db',
    folder: 'backend/app/services/extraction/',
    label: 'Structured Data',
  },
  reports: {
    icon: FileBarChart,
    tech: 'Standardized CMPDI Synthesizer',
    folder: 'backend/app/services/reports/',
    label: 'Geological Reports',
  },
  analytics: {
    icon: BarChart3,
    tech: 'Recharts + ACID Relational Store',
    folder: 'backend/app/services/extraction/',
    label: 'Mining Analytics',
  },
};

export default function ModuleGrid({ modules = {} }) {
  const moduleEntries = Object.entries(modules);

  return (
    <div className="module-section">
      <div className="section-header">
        <div>
          <h2 className="section-title">Backend Architecture</h2>
          <p className="section-subtitle">
            Five service directories — all operational
          </p>
        </div>
        <span className="badge badge-success">5 Services Active</span>
      </div>

      <div className="module-grid">
        {moduleEntries.map(([key, mod]) => {
          const meta = MODULE_META[key] || {
            icon: ShieldCheck,
            tech: 'FastAPI Service',
            folder: `backend/app/services/${key}/`,
            label: mod.name,
          };
          const Icon = meta.icon;

          return (
            <div key={key} className="module-card glass-panel">
              <div className="module-card-header">
                <div className="module-icon-wrap">
                  <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
                </div>
                <div className="module-badge-stack">
                  <span className="badge badge-success">{mod.status}</span>
                </div>
              </div>

              <div className="module-card-content">
                <h3 className="module-title">{mod.name}</h3>
                <p className="module-desc">{mod.description}</p>
              </div>

              <div className="module-card-footer">
                <div className="module-tech-tag">
                  <span className="tech-label">Engine:</span>
                  <span className="tech-value">{meta.tech}</span>
                </div>
                <div className="module-folder-tag">
                  <code>{meta.folder}</code>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
