import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  FileSpreadsheet,
  FileText,
  Download,
  Play,
  AlertCircle,
  CheckCircle2,
  BookOpen,
  Layers,
  MapPin,
  Pickaxe,
  Flame,
  Quote,
} from 'lucide-react';
import api from '../services/api';

const REPORT_TYPES = [
  {
    id: 'cmpdi_geological_summary',
    label: 'Geological Summary',
    description: 'CMPDI-style project, borehole, seam, quality, and metric compilation.',
  },
  {
    id: 'reserve_reconciliation_memo',
    label: 'Reserve Reconciliation',
    description: 'Seam-by-seam gross vs extractable reserves with recovery only when source values exist.',
  },
];

const SCOPE_OPTIONS = [
  { id: 'document', label: 'Current Document' },
  { id: 'project', label: 'Project / Mine' },
  { id: 'all', label: 'All Available Structured Data' },
];

function formatStat(value, suffix = '') {
  if (value === null || value === undefined || value === '') return 'N/A';
  return `${value}${suffix}`;
}

function triggerBlobDownload(blob, filename) {
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(href);
}

export default function GeologicalReports() {
  const [reportType, setReportType] = useState('cmpdi_geological_summary');
  const [scope, setScope] = useState('document');
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [projectName, setProjectName] = useState('');
  const [mines, setMines] = useState([]);
  const [status, setStatus] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [exporting, setExporting] = useState(null);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [previewTab, setPreviewTab] = useState('sections');

  const fetchBootstrap = useCallback(async () => {
    const [statusRes, docsRes, minesRes] = await Promise.all([
      api.getReportsStatus(),
      api.listDocuments(),
      api.getMines(),
    ]);
    if (statusRes.success) setStatus(statusRes.data);
    if (docsRes.success && Array.isArray(docsRes.data)) {
      const uniqueDocs = [];
      const seen = new Set();
      for (const d of docsRes.data) {
        const name = d.filename || d.original_filename;
        if (!seen.has(name)) {
          seen.add(name);
          uniqueDocs.push(d);
        }
      }
      setDocuments(uniqueDocs);
      if (uniqueDocs.length > 0) {
        setSelectedDocId((prev) =>
          uniqueDocs.some((d) => d.id === prev) ? prev : uniqueDocs[0].id
        );
      }
    }
    if (minesRes.success && Array.isArray(minesRes.data)) {
      setMines(minesRes.data);
    }
  }, []);

  useEffect(() => {
    fetchBootstrap();
  }, [fetchBootstrap]);

  const selectedDoc = useMemo(
    () => documents.find((d) => d.id === selectedDocId) || null,
    [documents, selectedDocId]
  );

  const projectOptions = useMemo(() => {
    const names = new Set();
    mines.forEach((m) => {
      if (m.project_name) names.add(m.project_name);
    });
    return Array.from(names).sort();
  }, [mines]);

  useEffect(() => {
    if (scope === 'project' && !projectName && projectOptions.length > 0) {
      setProjectName(projectOptions[0]);
    }
  }, [scope, projectName, projectOptions]);

  const buildPayload = useCallback(() => {
    const payload = { report_type: reportType, scope };
    if (scope === 'document') {
      if (selectedDoc) {
        payload.source_document = selectedDoc.filename || selectedDoc.original_filename;
        payload.document_id = selectedDoc.id;
      }
    } else if (scope === 'project') {
      payload.project_name = projectName;
    }
    return payload;
  }, [reportType, scope, selectedDoc, projectName]);

  const canGenerate = useMemo(() => {
    if (scope === 'document') return Boolean(selectedDoc);
    if (scope === 'project') return Boolean(projectName && projectName.trim());
    return true;
  }, [scope, selectedDoc, projectName]);

  const handleGenerate = async () => {
    if (!canGenerate) return;
    setGenerating(true);
    setError(null);
    const payload = buildPayload();
    const endpoint =
      reportType === 'reserve_reconciliation_memo'
        ? api.generateReserveReconciliation(payload)
        : api.generateGeologicalSummary(payload);
    const res = await endpoint;
    setGenerating(false);
    if (res.success) {
      setReport(res.data);
      setPreviewTab('sections');
    } else {
      setReport(null);
      setError(typeof res.error === 'string' ? res.error : 'Report generation failed.');
    }
  };

  const handleExport = async (format) => {
    if (!canGenerate) return;
    setExporting(format);
    setError(null);
    const res = await api.exportReport(format, buildPayload());
    setExporting(null);
    if (res.success) {
      triggerBlobDownload(res.blob, res.filename);
    } else {
      setError(typeof res.error === 'string' ? res.error : 'Export failed.');
    }
  };

  const stats = report?.summary_statistics || {};
  const isAggregated = report?.metadata?.scope === 'all';

  return (
    <div className="structured-extraction-container geological-reports-container" id="geological-reports-module">
      <div className="module-hero card">
        <div className="hero-content">
          <div className="analytics-eyebrow">
            <span className="eyebrow-dot" />
            CMPDI REPORTING ENGINE
          </div>
          <h2 className="hero-title">Automated Geological Reporting</h2>
          <p className="hero-description">
            Compile verified mines, boreholes, seams, proximate analyses, and geological metrics
            into CMPDI-standard reports with export to PDF, Excel, and Markdown.
          </p>
        </div>
        <div className="telemetry-stat-grid">
          <div className="stat-card">
            <span className="stat-label">STRUCTURED ENTITIES</span>
            <span className="stat-value text-cyan">
              {status?.total_structured_entities_available ?? '—'}
            </span>
            <span className="stat-subtext">Relational records</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">TEMPLATES</span>
            <span className="stat-value text-amber">
              {status?.report_templates?.length ?? 2}
            </span>
            <span className="stat-subtext">Summary + Reconciliation</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">EXPORTS</span>
            <span className="stat-value text-emerald">
              {(status?.export_formats || ['pdf', 'excel', 'markdown']).length}
            </span>
            <span className="stat-subtext">PDF, Excel, Markdown</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">ENGINE</span>
            <span className="stat-value text-orange">
              {status?.is_ready ? 'Ready' : '...'}
            </span>
            <span className="stat-subtext">{status?.engine_version || 'CMPDI Engine'}</span>
          </div>
        </div>
      </div>

      <div className="extraction-toolbar card reports-controls">
        <div className="toolbar-left reports-control-grid">
          <div className="doc-select-group">
            <label className="input-label" htmlFor="report-type-select">Report Type</label>
            <select
              id="report-type-select"
              className="select-input"
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            >
              {REPORT_TYPES.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div className="doc-select-group">
            <label className="input-label">Data Scope</label>
            <div className="view-mode-toggle">
              {SCOPE_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  className={`mode-toggle-btn ${scope === opt.id ? 'active' : ''}`}
                  onClick={() => setScope(opt.id)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {scope === 'document' && (
            <div className="doc-select-group">
              <label className="input-label" htmlFor="report-doc-select">Current Document</label>
              <select
                id="report-doc-select"
                className="select-input"
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
              >
                {documents.length === 0 && <option value="">No ingested documents</option>}
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.filename || d.original_filename}
                  </option>
                ))}
              </select>
            </div>
          )}

          {scope === 'project' && (
            <div className="doc-select-group">
              <label className="input-label" htmlFor="report-project-select">Project / Mine</label>
              <select
                id="report-project-select"
                className="select-input"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
              >
                {projectOptions.length === 0 && <option value="">No extracted projects</option>}
                {projectOptions.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <button
          type="button"
          className="browse-btn"
          onClick={handleGenerate}
          disabled={!canGenerate || generating}
          id="generate-report-btn"
        >
          <Play size={16} />
          {generating ? 'Generating…' : 'Generate Report'}
        </button>
      </div>

      <p className="scope-subtext reports-type-hint">
        {REPORT_TYPES.find((t) => t.id === reportType)?.description}
        {scope === 'all' && ' This run will be clearly labelled as an aggregated multi-document report.'}
      </p>

      {error && (
        <div className="upload-alert alert-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {!report && !generating && !error && (
        <div className="empty-scoped-state card">
          <FileSpreadsheet size={32} className="empty-scoped-icon" />
          <div className="empty-scoped-content">
            <div className="empty-scoped-title">No report generated yet</div>
            <p className="empty-scoped-desc">
              Choose a template and scope, then generate. Reports consume only existing structured
              records and keep provenance on every factual table.
            </p>
          </div>
        </div>
      )}

      {report && (
        <>
          {isAggregated && (
            <div className="scope-indicator-bar">
              <div className="scope-indicator-left">
                <span className="scope-pill active">AGGREGATED REPORT</span>
                <span className="scope-subtext">
                  Compiled from all available structured data — not a single-document extract.
                </span>
              </div>
            </div>
          )}

          <div className="module-hero card report-result-header">
            <div className="hero-content">
              <div className="hero-badge-group">
                <span className="badge badge-success">
                  <CheckCircle2 size={12} /> Generated
                </span>
                <span className="badge badge-subtle">{report.metadata.scope?.toUpperCase()}</span>
                <span className="badge badge-cyan">{report.metadata.scope_target}</span>
              </div>
              <h3 className="hero-title">{report.metadata.title}</h3>
              <p className="hero-description">
                {report.metadata.organization}
                {report.metadata.subsidiary ? ` · ${report.metadata.subsidiary}` : ''}
                {' · '}
                {report.metadata.total_records_used} structured records
                {' · '}
                {report.provenance_sources?.length || 0} provenance citations
              </p>
            </div>
            <div className="report-export-actions">
              <button type="button" className="back-btn" onClick={() => handleExport('pdf')} disabled={!!exporting}>
                <Download size={14} /> {exporting === 'pdf' ? 'PDF…' : 'Download PDF'}
              </button>
              <button type="button" className="back-btn" onClick={() => handleExport('excel')} disabled={!!exporting}>
                <FileSpreadsheet size={14} /> {exporting === 'excel' ? 'Excel…' : 'Download Excel'}
              </button>
              <button type="button" className="back-btn" onClick={() => handleExport('markdown')} disabled={!!exporting}>
                <FileText size={14} /> {exporting === 'markdown' ? 'Markdown…' : 'Download Markdown'}
              </button>
            </div>
          </div>

          <div className="telemetry-stat-grid">
            <div className="stat-card">
              <span className="stat-label"><Pickaxe size={12} /> MINES / PROJECTS</span>
              <span className="stat-value text-emerald">{formatStat(stats.total_mines_projects)}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label"><MapPin size={12} /> BOREHOLES</span>
              <span className="stat-value text-cyan">{formatStat(stats.total_boreholes_logged)}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label"><Layers size={12} /> SEAMS</span>
              <span className="stat-value text-amber">{formatStat(stats.total_seams_analyzed)}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label"><Flame size={12} /> GROSS RESERVES</span>
              <span className="stat-value text-orange">{formatStat(stats.total_gross_reserves_mt, ' MT')}</span>
            </div>
          </div>

          <div className="entity-tabs-container">
            <div className="entity-tabs">
              <button
                type="button"
                className={`entity-tab-btn ${previewTab === 'sections' ? 'active' : ''}`}
                onClick={() => setPreviewTab('sections')}
              >
                <BookOpen size={14} /> Report Preview
              </button>
              <button
                type="button"
                className={`entity-tab-btn ${previewTab === 'provenance' ? 'active' : ''}`}
                onClick={() => setPreviewTab('provenance')}
              >
                <Quote size={14} /> Provenance
                <span className="tab-count-badge">{report.provenance_sources?.length || 0}</span>
              </button>
              <button
                type="button"
                className={`entity-tab-btn ${previewTab === 'markdown' ? 'active' : ''}`}
                onClick={() => setPreviewTab('markdown')}
              >
                <FileText size={14} /> Markdown
              </button>
            </div>
          </div>

          {previewTab === 'sections' && (
            <div className="report-preview-stack">
              {(report.sections || []).map((section) => (
                <div key={section.section_id} className="card report-section-card">
                  <h4 className="report-section-title">{section.title}</h4>
                  {section.summary_text && (
                    <p className="report-section-summary">{section.summary_text}</p>
                  )}
                  {section.headers && section.rows && section.rows.length > 0 ? (
                    <div className="table-responsive-wrapper">
                      <table className="extracted-table">
                        <thead>
                          <tr>
                            {section.headers.map((h) => (
                              <th key={h}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {section.rows.map((row, rIdx) => (
                            <tr key={`${section.section_id}-${rIdx}`}>
                              {row.map((cell, cIdx) => (
                                <td key={`${section.section_id}-${rIdx}-${cIdx}`}>{cell ?? 'N/A'}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="empty-scoped-state">
                      <div className="empty-scoped-title">No records in this category</div>
                      <p className="empty-scoped-desc">
                        The selected scope has no structured records for this section. Values were not invented.
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {previewTab === 'provenance' && (
            <div className="card report-section-card">
              <h4 className="report-section-title">Source documents, pages, and evidence</h4>
              {(!report.provenance_sources || report.provenance_sources.length === 0) ? (
                <p className="empty-scoped-desc">No provenance citations for this scope.</p>
              ) : (
                <div className="table-responsive-wrapper">
                  <table className="extracted-table">
                    <thead>
                      <tr>
                        <th>Source Document</th>
                        <th>Page</th>
                        <th>Entity</th>
                        <th>Evidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.provenance_sources.map((p, idx) => (
                        <tr key={`${p.document_id}-${p.entity_id}-${idx}`}>
                          <td>{p.source_document}</td>
                          <td>{p.source_page}</td>
                          <td>{p.entity_type}</td>
                          <td className="evidence-cell">{p.evidence_text || 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {previewTab === 'markdown' && (
            <div className="card report-section-card">
              <pre className="markdown-preview">{report.markdown_content}</pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}
