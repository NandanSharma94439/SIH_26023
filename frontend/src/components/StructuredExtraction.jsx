import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Database,
  Layers,
  FileSpreadsheet,
  FileText,
  Search,
  RefreshCw,
  Play,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  MapPin,
  Flame,
  Pickaxe,
  TrendingUp,
  Filter
} from 'lucide-react';
import api from '../services/api';

const TABS = [
  { id: 'boreholes', label: 'Borehole Logs', icon: MapPin },
  { id: 'seams', label: 'Coal Seams', icon: Layers },
  { id: 'proximate', label: 'Proximate Analysis', icon: Flame },
  { id: 'mines', label: 'Mines & Projects', icon: Pickaxe },
  { id: 'metrics', label: 'Geological Metrics', icon: TrendingUp },
];

export default function StructuredExtraction() {
  const [activeTab, setActiveTab] = useState('boreholes');
  const [status, setStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);

  // Entities state across all categories
  const [boreholes, setBoreholes] = useState([]);
  const [seams, setSeams] = useState([]);
  const [proximate, setProximate] = useState([]);
  const [mines, setMines] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [dataLoading, setDataLoading] = useState(false);

  // Search & filter
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedEvidence, setExpandedEvidence] = useState({});

  // Extraction actions & document scope
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  // viewScope: 'selected' (Current Document - default) | 'all' (All Documents)
  const [viewScope, setViewScope] = useState('selected');
  const [extracting, setExtracting] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);

  // Fetch telemetry status
  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    const res = await api.getExtractionStatus();
    if (res.success) {
      setStatus(res.data);
    }
    setStatusLoading(false);
  }, []);

  // Fetch documents for the extraction dropdown (deduplicated by filename)
  const fetchDocuments = useCallback(async () => {
    const res = await api.listDocuments();
    if (res.success && res.data && res.data.length > 0) {
      // Deduplicate documents by filename so clean list is shown in select dropdown
      const uniqueDocs = [];
      const seenNames = new Set();
      for (const d of res.data) {
        const name = d.filename || d.original_filename;
        if (!seenNames.has(name)) {
          seenNames.add(name);
          uniqueDocs.push(d);
        }
      }
      setDocuments(uniqueDocs);
      if (!selectedDocId || !uniqueDocs.some((d) => d.id === selectedDocId)) {
        setSelectedDocId(uniqueDocs[0].id);
      }
    }
  }, [selectedDocId]);

  // Fetch all records across all categories so tabs & counts update instantaneously
  const fetchAllRecords = useCallback(async () => {
    setDataLoading(true);
    try {
      const [bRes, sRes, pRes, mRes, gRes] = await Promise.all([
        api.getBoreholes(),
        api.getSeams(),
        api.getProximateAnalyses(),
        api.getMines(),
        api.getMetrics(),
      ]);
      if (bRes.success && bRes.data) setBoreholes(bRes.data);
      if (sRes.success && sRes.data) setSeams(sRes.data);
      if (pRes.success && pRes.data) setProximate(pRes.data);
      if (mRes.success && mRes.data) setMines(mRes.data);
      if (gRes.success && gRes.data) setMetrics(gRes.data);
    } catch (err) {
      console.error('Failed to load extraction records:', err);
    } finally {
      setDataLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchDocuments();
    fetchAllRecords();
  }, [fetchStatus, fetchDocuments, fetchAllRecords]);

  // Selected document object
  const selectedDoc = useMemo(() => {
    return documents.find((d) => d.id === selectedDocId) || null;
  }, [documents, selectedDocId]);

  // Scope filter: matches by document_id AND/OR source_document filename
  const isDocMatch = useCallback(
    (record) => {
      if (viewScope === 'all') return true;
      if (!selectedDoc) return true;
      return (
        (record.document_id && record.document_id === selectedDoc.id) ||
        (record.source_document &&
          (record.source_document === selectedDoc.filename ||
            record.source_document === selectedDoc.original_filename))
      );
    },
    [viewScope, selectedDoc]
  );

  // Scoped entity collections
  const scopedBoreholes = useMemo(() => boreholes.filter(isDocMatch), [boreholes, isDocMatch]);
  const scopedSeams = useMemo(() => seams.filter(isDocMatch), [seams, isDocMatch]);
  const scopedProximate = useMemo(() => proximate.filter(isDocMatch), [proximate, isDocMatch]);
  const scopedMines = useMemo(() => mines.filter(isDocMatch), [mines, isDocMatch]);
  const scopedMetrics = useMemo(() => metrics.filter(isDocMatch), [metrics, isDocMatch]);

  // Display collections with text search
  const displayedBoreholes = useMemo(
    () =>
      scopedBoreholes.filter(
        (b) => !searchTerm || JSON.stringify(b).toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [scopedBoreholes, searchTerm]
  );
  const displayedSeams = useMemo(
    () =>
      scopedSeams.filter(
        (s) => !searchTerm || JSON.stringify(s).toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [scopedSeams, searchTerm]
  );
  const displayedProximate = useMemo(
    () =>
      scopedProximate.filter(
        (p) => !searchTerm || JSON.stringify(p).toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [scopedProximate, searchTerm]
  );
  const displayedMines = useMemo(
    () =>
      scopedMines.filter(
        (m) => !searchTerm || JSON.stringify(m).toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [scopedMines, searchTerm]
  );
  const displayedMetrics = useMemo(
    () =>
      scopedMetrics.filter(
        (g) => !searchTerm || JSON.stringify(g).toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [scopedMetrics, searchTerm]
  );

  // Scoped count badges for entity tabs
  const tabCounts = useMemo(
    () => ({
      boreholes: scopedBoreholes.length,
      seams: scopedSeams.length,
      proximate: scopedProximate.length,
      mines: scopedMines.length,
      metrics: scopedMetrics.length,
    }),
    [scopedBoreholes, scopedSeams, scopedProximate, scopedMines, scopedMetrics]
  );

  // Total scoped entity count for telemetry cards
  const totalScopedEntities = useMemo(
    () =>
      scopedBoreholes.length +
      scopedSeams.length +
      scopedProximate.length +
      scopedMines.length +
      scopedMetrics.length,
    [scopedBoreholes, scopedSeams, scopedProximate, scopedMines, scopedMetrics]
  );

  // Handle single document extraction
  const handleExtractSingle = async () => {
    if (!selectedDocId) return;
    setExtracting(true);
    setActionMessage(null);
    const res = await api.extractDocument(selectedDocId);
    setExtracting(false);
    if (res.success) {
      setActionMessage({
        type: 'success',
        text: `Successfully extracted ${res.data.filename}: ${JSON.stringify(res.data.extracted_counts)}`,
      });
      // Default to "Current Document" scope upon successful extraction
      setViewScope('selected');
      fetchStatus();
      fetchAllRecords();
    } else {
      setActionMessage({
        type: 'error',
        text: res.error || 'Extraction failed.',
      });
    }
  };

  // Handle bulk document extraction
  const handleExtractAll = async () => {
    setExtracting(true);
    setActionMessage(null);
    const res = await api.extractAllDocuments();
    setExtracting(false);
    if (res.success) {
      setActionMessage({
        type: 'success',
        text: `Bulk extraction complete: ${res.data.total_entities_extracted} entities extracted across ${res.data.successful_documents} documents.`,
      });
      fetchStatus();
      fetchAllRecords();
    } else {
      setActionMessage({
        type: 'error',
        text: res.error || 'Bulk extraction failed.',
      });
    }
  };

  const toggleEvidence = (id) => {
    setExpandedEvidence((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <div className="structured-extraction-container" id="structured-extraction-module">
      {/* 1. Header & Hero Telemetry Strip */}
      <div className="module-hero card">
        <div className="hero-content">
          <div className="analytics-eyebrow">
            <span className="eyebrow-dot" />
            CMPDI STRUCTURED REPOSITORY
          </div>
          <h2 className="hero-title">Structured Mining Data Extraction</h2>
          <p className="hero-description">
            Schema-guided extraction of coal seams, borehole stratigraphy, proximate analysis
            parameters, and mining feasibility metrics with verified document and page-level provenance.
          </p>
        </div>

        {/* Telemetry Stat Cards reflecting selected scope */}
        <div className="telemetry-stat-grid">
          <div className="stat-card">
            <span className="stat-label">TOTAL ENTITIES</span>
            <span className="stat-value text-cyan">
              {statusLoading || dataLoading
                ? '...'
                : viewScope === 'selected'
                ? totalScopedEntities
                : status?.total_entities_count ?? totalScopedEntities}
            </span>
            <span className="stat-subtext">
              {viewScope === 'selected'
                ? `Current: ${selectedDoc?.filename || 'Selected File'}`
                : `Across ${status?.total_documents_extracted ?? 0} Docs`}
            </span>
          </div>

          <div className="stat-card">
            <span className="stat-label">BOREHOLE LOGS</span>
            <span className="stat-value text-amber">
              {dataLoading ? '...' : tabCounts.boreholes}
            </span>
            <span className="stat-subtext">Collar & Depths</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">COAL SEAMS</span>
            <span className="stat-value text-emerald">
              {dataLoading ? '...' : tabCounts.seams}
            </span>
            <span className="stat-subtext">Thickness & Reserves</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">PROXIMATE & GCV</span>
            <span className="stat-value text-orange">
              {dataLoading ? '...' : tabCounts.proximate}
            </span>
            <span className="stat-subtext">Quality Grades</span>
          </div>
        </div>
      </div>

      {/* 2. Action Toolbar: Document Selector & Extraction Trigger */}
      <div className="extraction-toolbar card">
        <div className="toolbar-left">
          <div className="doc-select-group">
            <label htmlFor="extract-doc-select" className="input-label">
              Select Ingested Document:
            </label>
            <select
              id="extract-doc-select"
              value={selectedDocId}
              onChange={(e) => {
                setSelectedDocId(e.target.value);
                // Immediately default to "Current Document" when user selects a document
                setViewScope('selected');
              }}
              className="select-input"
              disabled={extracting || documents.length === 0}
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.file_type.toUpperCase()}, {d.total_pages} p.)
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleExtractSingle}
            disabled={extracting || !selectedDocId}
            className="btn btn-primary"
            id="btn-extract-single"
          >
            <Play size={14} className={extracting ? 'animate-spin' : ''} />
            {extracting ? 'Extracting...' : 'Extract Document'}
          </button>

          <button
            onClick={handleExtractAll}
            disabled={extracting || documents.length === 0}
            className="btn btn-outline"
            id="btn-extract-all"
          >
            <RefreshCw size={14} className={extracting ? 'animate-spin' : ''} />
            Extract All Processed Documents
          </button>
        </div>

        <div className="toolbar-right">
          <button
            onClick={() => {
              fetchStatus();
              fetchAllRecords();
            }}
            className="btn btn-icon"
            title="Refresh Records"
          >
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {/* Action Notification Banner */}
      {actionMessage && (
        <div className={`alert-banner alert-${actionMessage.type}`}>
          {actionMessage.type === 'success' ? (
            <CheckCircle2 className="icon-md" />
          ) : (
            <AlertCircle className="icon-md" />
          )}
          <div className="alert-content">{actionMessage.text}</div>
        </div>
      )}

      {/* 3. Scope Indicator Bar: Explicit Document Filtering Mode & Indicator */}
      <div className="scope-indicator-bar card" id="scope-indicator-bar">
        <div className="scope-indicator-left">
          <div className="scope-badge-group">
            <span className={`scope-pill ${viewScope === 'selected' ? 'active' : ''}`}>
              <Filter size={14} className={viewScope === 'selected' ? 'text-amber' : 'text-muted'} />
              {viewScope === 'selected' ? (
                <>
                  <strong>Current Document:</strong> {selectedDoc?.filename || 'None Selected'}
                </>
              ) : (
                <>
                  <strong>All Documents:</strong> Showing Cumulative Records
                </>
              )}
            </span>
            <span className="scope-subtext">
              {viewScope === 'selected'
                ? 'Showing records from this document only'
                : `Showing cumulative database records across all ${
                    status?.total_documents_extracted || documents.length
                  } extracted files`}
            </span>
          </div>
        </div>

        <div className="scope-indicator-right">
          <span className="scope-toggle-label">Scope:</span>
          <div className="view-mode-toggle" role="group" aria-label="Extraction Scope">
            <button
              type="button"
              className={`mode-toggle-btn ${viewScope === 'selected' ? 'active' : ''}`}
              onClick={() => setViewScope('selected')}
              id="scope-toggle-current"
              title="Show records from currently selected document only"
            >
              Current Document
            </button>
            <button
              type="button"
              className={`mode-toggle-btn ${viewScope === 'all' ? 'active' : ''}`}
              onClick={() => setViewScope('all')}
              id="scope-toggle-all"
              title="Show records across all documents"
            >
              All Documents
            </button>
          </div>
        </div>
      </div>

      {/* 4. Entity Tab Switcher with Scoped Count Badges */}
      <div className="entity-tabs-container">
        <div className="entity-tabs">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const count = tabCounts[tab.id] ?? 0;
            const isSelected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setSearchTerm('');
                }}
                className={`entity-tab-btn ${isSelected ? 'active' : ''}`}
                id={`tab-${tab.id}`}
              >
                <Icon size={16} className={`tab-icon ${tab.color}`} />
                <span className="tab-label">{tab.label}</span>
                <span className="tab-count-badge">{count}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Search Filter */}
        <div className="tab-search-box">
          <Search size={14} className="text-muted" />
          <input
            type="text"
            placeholder={`Filter ${TABS.find((t) => t.id === activeTab)?.label}...`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="tab-search-input"
          />
        </div>
      </div>

      {/* 5. Entity Relational Tables with Verbatim Evidence Dropdown */}
      <div className="entity-table-card card">
        {dataLoading ? (
          <div className="table-loading">
            <RefreshCw className="animate-spin text-cyan" size={24} />
            <p>Loading relational records...</p>
          </div>
        ) : (
          <div className="table-wrapper">
            {/* --- A. BOREHOLES TAB --- */}
            {activeTab === 'boreholes' && (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Borehole ID</th>
                    <th>Mine / Project</th>
                    <th>Collar Elevation</th>
                    <th>Total Depth</th>
                    <th>Lithology Summary</th>
                    <th>Source Provenance</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedBoreholes.map((b) => (
                    <React.Fragment key={b.id}>
                      <tr>
                        <td className="font-semibold text-cyan">{b.borehole_id}</td>
                        <td>{b.mine_project || <span className="text-muted">—</span>}</td>
                        <td>
                          {b.collar_elevation != null ? (
                            `${b.collar_elevation} m RL`
                          ) : (
                            <span className="text-muted">—</span>
                          )}
                        </td>
                        <td className="font-mono">
                          {b.total_depth != null ? `${b.total_depth} m` : <span className="text-muted">—</span>}
                        </td>
                        <td className="text-sm max-w-xs truncate" title={b.lithology || ''}>
                          {b.lithology || <span className="text-muted">—</span>}
                        </td>
                        <td>
                          <span className="provenance-tag">
                            <FileText size={12} strokeWidth={1.8} aria-hidden="true" />
                            <span>{b.source_document} (p. {b.source_page})</span>
                          </span>
                        </td>
                        <td>
                          <button
                            onClick={() => toggleEvidence(b.id)}
                            className="btn-link"
                            title="Toggle source evidence"
                          >
                            {expandedEvidence[b.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />} Evidence
                          </button>
                        </td>
                      </tr>
                      {expandedEvidence[b.id] && (
                        <tr className="evidence-row">
                          <td colSpan={7}>
                            <div className="evidence-box">
                              <span className="evidence-title">Verbatim Source Evidence (Page {b.source_page}):</span>
                              <p className="evidence-quote">“{b.evidence_text}”</p>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                  {displayedBoreholes.length === 0 && (
                    <tr>
                      <td colSpan={7} className="table-empty">
                        <div className="empty-scoped-state">
                          <AlertCircle size={20} className="empty-scoped-icon text-muted" />
                          <div className="empty-scoped-content">
                            <div className="empty-scoped-title">
                              {viewScope === 'selected'
                                ? 'No records extracted from this document.'
                                : 'No borehole records extracted yet.'}
                            </div>
                            {viewScope === 'selected' && (
                              <div className="empty-scoped-desc">
                                0 borehole logs found in {selectedDoc?.filename}. Switch scope to "All Documents"
                                to view records from other files.
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}

            {/* --- B. COAL SEAMS TAB --- */}
            {activeTab === 'seams' && (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Seam Code / Name</th>
                    <th>Borehole</th>
                    <th>Depth From (m)</th>
                    <th>Depth To (m)</th>
                    <th>Thickness (m)</th>
                    <th>CIL Grade</th>
                    <th>Category</th>
                    <th>Reserves (MT)</th>
                    <th>Source Provenance</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedSeams.map((s) => (
                    <React.Fragment key={s.id}>
                      <tr>
                        <td className="font-semibold text-amber">{s.seam_id}</td>
                        <td className="font-mono">{s.borehole_id || <span className="text-muted">—</span>}</td>
                        <td className="font-mono">{s.depth_from != null ? s.depth_from : <span className="text-muted">—</span>}</td>
                        <td className="font-mono">{s.depth_to != null ? s.depth_to : <span className="text-muted">—</span>}</td>
                        <td className="font-mono font-semibold text-emerald">
                          {s.thickness != null ? `${s.thickness} m` : <span className="text-muted">—</span>}
                        </td>
                        <td>{s.coal_grade ? <span className="badge badge-subtle">{s.coal_grade}</span> : <span className="text-muted">—</span>}</td>
                        <td>{s.category ? <span className="badge badge-cyan">{s.category}</span> : <span className="text-muted">—</span>}</td>
                        <td className="font-mono">
                          {s.gross_reserves_mt != null ? `${s.gross_reserves_mt} MT` : <span className="text-muted">—</span>}
                        </td>
                        <td>
                          <span className="provenance-tag">
                            <FileText size={12} strokeWidth={1.8} aria-hidden="true" />
                            <span>{s.source_document} (p. {s.source_page})</span>
                          </span>
                        </td>
                        <td>
                          <button
                            onClick={() => toggleEvidence(s.id)}
                            className="btn-link"
                            title="Toggle source evidence"
                          >
                            {expandedEvidence[s.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />} Evidence
                          </button>
                        </td>
                      </tr>
                      {expandedEvidence[s.id] && (
                        <tr className="evidence-row">
                          <td colSpan={10}>
                            <div className="evidence-box">
                              <span className="evidence-title">Verbatim Source Evidence (Page {s.source_page}):</span>
                              <p className="evidence-quote">“{s.evidence_text}”</p>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                  {displayedSeams.length === 0 && (
                    <tr>
                      <td colSpan={10} className="table-empty">
                        <div className="empty-scoped-state">
                          <AlertCircle size={20} className="empty-scoped-icon text-muted" />
                          <div className="empty-scoped-content">
                            <div className="empty-scoped-title">
                              {viewScope === 'selected'
                                ? 'No records extracted from this document.'
                                : 'No coal seam records extracted yet.'}
                            </div>
                            {viewScope === 'selected' && (
                              <div className="empty-scoped-desc">
                                0 coal seams found in {selectedDoc?.filename}. Switch scope to "All Documents"
                                to view records from other files.
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}

            {/* --- C. PROXIMATE ANALYSIS TAB --- */}
            {activeTab === 'proximate' && (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Seam Code</th>
                    <th>Borehole</th>
                    <th>Moisture %</th>
                    <th>Ash %</th>
                    <th>Volatile Matter %</th>
                    <th>Fixed Carbon %</th>
                    <th>Gross Calorific Value</th>
                    <th>Source Provenance</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedProximate.map((p) => (
                    <React.Fragment key={p.id}>
                      <tr>
                        <td className="font-semibold text-amber">{p.seam_id || <span className="text-muted">—</span>}</td>
                        <td className="font-mono">{p.borehole_id || <span className="text-muted">—</span>}</td>
                        <td className="font-mono">{p.moisture_percent != null ? `${p.moisture_percent}%` : <span className="text-muted">—</span>}</td>
                        <td className="font-mono font-semibold text-orange">
                          {p.ash_percent != null ? `${p.ash_percent}%` : <span className="text-muted">—</span>}
                        </td>
                        <td className="font-mono">{p.volatile_matter_percent != null ? `${p.volatile_matter_percent}%` : <span className="text-muted">—</span>}</td>
                        <td className="font-mono">{p.fixed_carbon_percent != null ? `${p.fixed_carbon_percent}%` : <span className="text-muted">—</span>}</td>
                        <td className="font-mono font-semibold text-emerald">
                          {p.gross_calorific_value != null ? `${p.gross_calorific_value} ${p.units || 'kcal/kg'}` : <span className="text-muted">—</span>}
                        </td>
                        <td>
                          <span className="provenance-tag">
                            <FileText size={12} strokeWidth={1.8} aria-hidden="true" />
                            <span>{p.source_document} (p. {p.source_page})</span>
                          </span>
                        </td>
                        <td>
                          <button
                            onClick={() => toggleEvidence(p.id)}
                            className="btn-link"
                            title="Toggle source evidence"
                          >
                            {expandedEvidence[p.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />} Evidence
                          </button>
                        </td>
                      </tr>
                      {expandedEvidence[p.id] && (
                        <tr className="evidence-row">
                          <td colSpan={9}>
                            <div className="evidence-box">
                              <span className="evidence-title">Verbatim Source Evidence (Page {p.source_page}):</span>
                              <p className="evidence-quote">“{p.evidence_text}”</p>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                  {displayedProximate.length === 0 && (
                    <tr>
                      <td colSpan={9} className="table-empty">
                        <div className="empty-scoped-state">
                          <AlertCircle size={20} className="empty-scoped-icon text-muted" />
                          <div className="empty-scoped-content">
                            <div className="empty-scoped-title">
                              {viewScope === 'selected'
                                ? 'No records extracted from this document.'
                                : 'No proximate quality analysis records extracted yet.'}
                            </div>
                            {viewScope === 'selected' && (
                              <div className="empty-scoped-desc">
                                0 proximate analysis records found in {selectedDoc?.filename}. Switch scope to "All Documents"
                                to view records from other files.
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}

            {/* --- D. MINES & PROJECTS TAB --- */}
            {activeTab === 'mines' && (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Project Name</th>
                    <th>Subsidiary</th>
                    <th>Location / Block</th>
                    <th>Target Production</th>
                    <th>Stripping Ratio</th>
                    <th>Life of Mine</th>
                    <th>Source Provenance</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedMines.map((m) => (
                    <React.Fragment key={m.id}>
                      <tr>
                        <td className="font-semibold text-emerald-400">{m.project_name}</td>
                        <td>{m.subsidiary || <span className="text-muted">—</span>}</td>
                        <td>{m.location || m.block_name || <span className="text-muted">—</span>}</td>
                        <td className="font-mono font-semibold text-cyan">
                          {m.target_production != null ? `${m.target_production} ${m.target_production_unit || 'MTPA'}` : <span className="text-muted">—</span>}
                        </td>
                        <td className="font-mono text-amber">
                          {m.stripping_ratio != null ? `${m.stripping_ratio} : 1` : <span className="text-muted">—</span>}
                        </td>
                        <td>{m.life_of_mine_years != null ? `${m.life_of_mine_years} Yrs` : <span className="text-muted">—</span>}</td>
                        <td>
                          <span className="provenance-tag">
                            <FileText size={12} strokeWidth={1.8} aria-hidden="true" />
                            <span>{m.source_document} (p. {m.source_page})</span>
                          </span>
                        </td>
                        <td>
                          <button
                            onClick={() => toggleEvidence(m.id)}
                            className="btn-link"
                            title="Toggle source evidence"
                          >
                            {expandedEvidence[m.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />} Evidence
                          </button>
                        </td>
                      </tr>
                      {expandedEvidence[m.id] && (
                        <tr className="evidence-row">
                          <td colSpan={8}>
                            <div className="evidence-box">
                              <span className="evidence-title">Verbatim Source Evidence (Page {m.source_page}):</span>
                              <p className="evidence-quote">“{m.evidence_text}”</p>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                  {displayedMines.length === 0 && (
                    <tr>
                      <td colSpan={8} className="table-empty">
                        <div className="empty-scoped-state">
                          <AlertCircle size={20} className="empty-scoped-icon text-muted" />
                          <div className="empty-scoped-content">
                            <div className="empty-scoped-title">
                              {viewScope === 'selected'
                                ? 'No records extracted from this document.'
                                : 'No mine or project records extracted yet.'}
                            </div>
                            {viewScope === 'selected' && (
                              <div className="empty-scoped-desc">
                                0 mine/project records found in {selectedDoc?.filename}. Switch scope to "All Documents"
                                to view records from other files.
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}

            {/* --- E. GEOLOGICAL METRICS TAB --- */}
            {activeTab === 'metrics' && (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Metric Name</th>
                    <th>Value</th>
                    <th>Unit</th>
                    <th>Year / Period</th>
                    <th>Category</th>
                    <th>Source Provenance</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedMetrics.map((g) => (
                    <React.Fragment key={g.id}>
                      <tr>
                        <td className="font-semibold text-blue-400">{g.metric_name}</td>
                        <td className="font-mono font-semibold text-cyan">
                          {g.metric_value != null ? g.metric_value.toLocaleString() : <span className="text-muted">—</span>}
                        </td>
                        <td>{g.unit ? <span className="badge badge-subtle">{g.unit}</span> : <span className="text-muted">—</span>}</td>
                        <td>{g.year_period || <span className="text-muted">—</span>}</td>
                        <td>{g.category ? <span className="badge badge-cyan">{g.category}</span> : <span className="text-muted">—</span>}</td>
                        <td>
                          <span className="provenance-tag">
                            <FileText size={12} strokeWidth={1.8} aria-hidden="true" />
                            <span>{g.source_document} (p. {g.source_page})</span>
                          </span>
                        </td>
                        <td>
                          <button
                            onClick={() => toggleEvidence(g.id)}
                            className="btn-link"
                            title="Toggle source evidence"
                          >
                            {expandedEvidence[g.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />} Evidence
                          </button>
                        </td>
                      </tr>
                      {expandedEvidence[g.id] && (
                        <tr className="evidence-row">
                          <td colSpan={7}>
                            <div className="evidence-box">
                              <span className="evidence-title">Verbatim Source Evidence (Page {g.source_page}):</span>
                              <p className="evidence-quote">“{g.evidence_text}”</p>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                  {displayedMetrics.length === 0 && (
                    <tr>
                      <td colSpan={7} className="table-empty">
                        <div className="empty-scoped-state">
                          <AlertCircle size={20} className="empty-scoped-icon text-muted" />
                          <div className="empty-scoped-content">
                            <div className="empty-scoped-title">
                              {viewScope === 'selected'
                                ? 'No records extracted from this document.'
                                : 'No geological report metrics extracted yet.'}
                            </div>
                            {viewScope === 'selected' && (
                              <div className="empty-scoped-desc">
                                0 geological metrics found in {selectedDoc?.filename}. Switch scope to "All Documents"
                                to view records from other files.
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
