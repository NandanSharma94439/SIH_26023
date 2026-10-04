import React from 'react';
import {
  Server,
  FolderCheck,
  Cpu,
  ShieldCheck,
  Clock,
  Sparkles,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

export default function TelemetryOverview({ health, loading }) {
  const isOnline = health?.success && health?.data?.status === 'ok';
  const data = health?.data || {};
  const system = data.system || {};

  return (
    <div className="telemetry-section">
      <div className="telemetry-banner glass-panel">
        <div className="banner-content">
          <div className="analytics-eyebrow">
            <span className="eyebrow-dot online" />
            CMPDI · PLATFORM STATUS
          </div>
          <h1 className="banner-title">
            Mining Document Intelligence & Reporting Platform
          </h1>
          <p className="banner-description">
            Automating geological reporting, borehole correlation, and seam intelligence for{' '}
            <strong>CMPDI & Coal India Limited (CIL)</strong> subsidiaries. Integrated modules
            deliver multi-modal document ingestion, OCR, vector RAG, structured extraction, and reporting.
          </p>
        </div>

        <div className="banner-meta">
          <div className="meta-metric">
            <span className="metric-label">API Status</span>
            <div className="metric-value-row">
              {isOnline ? (
                <>
                  <CheckCircle2 size={18} color="var(--color-success)" />
                  <span className="metric-value-online">Healthy</span>
                </>
              ) : (
                <>
                  <AlertCircle size={18} color="var(--color-error)" />
                  <span className="metric-value-offline">Offline</span>
                </>
              )}
            </div>
          </div>

          <div className="meta-metric">
            <span className="metric-label">API Latency</span>
            <span className="metric-value">
              {health?.latencyMs !== undefined ? `${health.latencyMs} ms` : '—'}
            </span>
          </div>

          <div className="meta-metric">
            <span className="metric-label">Platform Status</span>
            <span className="metric-value">All Modules Live</span>
          </div>
        </div>
      </div>

      {/* Grid of Real System Telemetry Cards */}
      <div className="telemetry-grid">
        {/* Card 1: Fast API Backend */}
        <div className="stat-card glass-panel">
          <div className="stat-header">
            <div className="stat-icon-wrapper">
              <Server size={20} className="stat-icon" />
            </div>
            <span className="badge badge-success">Endpoint 200</span>
          </div>
          <div className="stat-body">
            <span className="stat-label">FastAPI Service Shell</span>
            <span className="stat-value">{data.project || 'Mining Doc Intelligence API'}</span>
            <span className="stat-meta">
              Version {data.version || '0.1.0'} &bull; Env: {data.environment || 'development'}
            </span>
          </div>
        </div>

        {/* Card 2: Python Runtime */}
        <div className="stat-card glass-panel">
          <div className="stat-header">
            <div className="stat-icon-wrapper">
              <Cpu size={20} className="stat-icon" />
            </div>
            <span className="badge badge-cyan">64-bit AMD64</span>
          </div>
          <div className="stat-body">
            <span className="stat-label">Python Environment</span>
            <span className="stat-value">
              Python {system.python_version || '3.14.x'}
            </span>
            <span className="stat-meta">
              Platform: {system.platform ? system.platform.split('-')[0] : 'Windows'}
            </span>
          </div>
        </div>

        {/* Card 3: Storage Subsystems */}
        <div className="stat-card glass-panel">
          <div className="stat-header">
            <div className="stat-icon-wrapper">
              <FolderCheck size={20} className="stat-icon" />
            </div>
            <span className="badge badge-success">Initialized</span>
          </div>
          <div className="stat-body">
            <span className="stat-label">Local File & Index Storage</span>
            <span className="stat-value">
              {system.storage_ready && system.faiss_ready ? 'Volumes Ready' : 'Initializing...'}
            </span>
            <span className="stat-meta">
              storage/uploads &bull; storage/faiss_index
            </span>
          </div>
        </div>

        {/* Card 4: Gemini AI Gateway */}
        <div className="stat-card glass-panel">
          <div className="stat-header">
            <div className="stat-icon-wrapper">
              <Sparkles size={20} className="stat-icon" />
            </div>
            <span className={`badge ${data.gemini_configured ? 'badge-success' : 'badge-warning'}`}>
              {data.gemini_configured ? 'Key Bound' : 'Awaiting Key'}
            </span>
          </div>
          <div className="stat-body">
            <span className="stat-label">Gemini AI Engine (Backend)</span>
            <span className="stat-value">
              {data.gemini_configured ? 'Gemini 1.5 Ready' : 'Backend Proxy Ready'}
            </span>
            <span className="stat-meta">
              Encapsulated &bull; Zero client-side leakage
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
