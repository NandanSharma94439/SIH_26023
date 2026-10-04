import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Sparkles,
  Database,
  Layers,
  FileText,
  FileSpreadsheet,
  BarChart3,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ExternalLink,
  Cpu,
  Clock,
  HelpCircle,
  ShieldCheck,
  Table as TableIcon,
  X
} from 'lucide-react';
import api from '../services/api';

const SAMPLE_QUERIES = [
  {
    title: 'Drilling Target (PDF Table)',
    query: "What was CMPDI's drilling target and actual achievement in 2006-07?",
    icon: BarChart3,
  },
  {
    title: 'Geological Reports (PDF Table)',
    query: 'How many geological reports and project reports were submitted in 2006-07?',
    icon: FileText,
  },
  {
    title: 'Borehole Logging (XLSX)',
    query: 'What are the borehole depth intervals and lithology descriptions in the borehole logging sheet?',
    icon: Layers,
  },
  {
    title: 'Mine Feasibility (DOCX)',
    query: 'What is the target annual production and stripping ratio in the feasibility study?',
    icon: FileSpreadsheet,
  },
  {
    title: 'Scanned Log (OCR)',
    query: 'What is the collar elevation and total depth of Borehole BH-204 in Jharia Coalfield?',
    icon: Search,
  },
  {
    title: 'Insufficient Evidence Test',
    query: 'What is the uranium isotope concentration in Seam IX at Raniganj?',
    icon: HelpCircle,
  },
];

export default function RAGAssistant() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [status, setStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [expandedSources, setExpandedSources] = useState({});

  // Fetch RAG and FAISS telemetry status
  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    const res = await api.getRagStatus();
    if (res.success) {
      setStatus(res.data);
    }
    setStatusLoading(false);
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Execute Grounded Query
  const handleQuery = async (queryText = query) => {
    const activeQuery = (queryText || '').trim();
    if (!activeQuery) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const res = await api.queryRAG(activeQuery, topK);
    setLoading(false);

    if (res.success) {
      setResult(res.data);
      // Auto-expand first source
      if (res.data.sources && res.data.sources.length > 0) {
        setExpandedSources({ [res.data.sources[0].chunk_id]: true });
      }
    } else {
      setError(res.error || 'Query failed. Please verify backend status.');
    }
  };

  // Bulk index all processed documents
  const handleIndexAll = async () => {
    setIndexing(true);
    setError(null);
    const res = await api.indexAllDocuments();
    setIndexing(false);

    if (res.success) {
      fetchStatus();
    } else {
      setError(res.error || 'Failed to index documents into FAISS.');
    }
  };

  const toggleSourceExpand = (chunkId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [chunkId]: !prev[chunkId],
    }));
  };

  return (
    <div className="rag-container" id="rag-assistant-view">
      {/* 1. Header & Knowledge Base Status Strip */}
      <div className="rag-header-strip">
        <div className="rag-header-info">
          <div className="analytics-eyebrow">
            <span className="eyebrow-dot" />
            FAISS RETRIEVAL · GEMINI EMBEDDINGS
          </div>
          <h2 className="rag-title">Geological Knowledge Assistant</h2>
          <p className="rag-subtitle">
            Grounded semantic search across CMPDI geological reports, borehole core logs,
            proximate analysis, and feasibility studies with page-level citations.
          </p>
        </div>

        <div className="rag-telemetry-panel">
          <div className="rag-stat-card">
            <div className="rag-stat-label">FAISS Vectors</div>
            <div className="rag-stat-val text-amber">
              {statusLoading ? '...' : (status?.vector_count ?? 0)}
            </div>
          </div>
          <div className="rag-stat-card">
            <div className="rag-stat-label">Indexed Docs</div>
            <div className="rag-stat-val text-emerald">
              {statusLoading ? '...' : (status?.indexed_documents_count ?? 0)}
            </div>
          </div>
          <div className="rag-stat-card">
            <div className="rag-stat-label">Gemini API</div>
            <div className="rag-stat-val">
              {status?.gemini_configured ? (
                <span className="status-pill status-pill-online">Ready</span>
              ) : (
                <span className="status-pill status-pill-offline">Missing Key</span>
              )}
            </div>
          </div>
          <button
            id="rag-index-all-btn"
            className="btn btn-secondary btn-sm"
            onClick={handleIndexAll}
            disabled={indexing}
            title="Index all processed documents into FAISS vector store"
          >
            <RefreshCw className={`icon-sm ${indexing ? 'spin' : ''}`} />
            {indexing ? 'Indexing...' : 'Index All'}
          </button>
        </div>
      </div>

      {/* 2. API Key Warning Banner if Unconfigured */}
      {status && !status.gemini_configured && (
        <div className="alert-banner alert-warning" id="gemini-key-warning">
          <AlertCircle className="icon-md" />
          <div className="alert-content">
            <strong>Gemini API Key Required:</strong> Add your Google Gemini API key to{' '}
            <code>backend/.env</code> as <code>GEMINI_API_KEY=your_key</code> to enable real
            embedding vectorization ({status?.embedding_model || 'Gemini Embeddings'}) and grounded LLM answers.
          </div>
        </div>
      )}

      {/* 3. Query Input Console */}
      <div className="rag-search-box card">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleQuery();
          }}
          className="rag-form"
        >
          <div className="rag-input-wrapper">
            <Search className="rag-search-icon" />
            <input
              id="rag-query-input"
              type="text"
              className="rag-input"
              placeholder="Ask any question about geological reports, borehole depths, seam reserves, or targets..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
            {query && (
              <button
                type="button"
                className="rag-clear-btn"
                onClick={() => setQuery('')}
                aria-label="Clear query"
              >
                <X size={14} aria-hidden="true" />
              </button>
            )}
          </div>

          <div className="rag-controls">
            <div className="rag-topk-select">
              <label htmlFor="rag-topk-select">Evidence Chunks:</label>
              <select
                id="rag-topk-select"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                disabled={loading}
              >
                <option value={3}>Top 3</option>
                <option value={5}>Top 5</option>
                <option value={8}>Top 8</option>
              </select>
            </div>

            <button
              id="rag-submit-btn"
              type="submit"
              className="btn btn-primary"
              disabled={loading || !query.trim()}
            >
              {loading ? (
                <>
                  <RefreshCw className="icon-sm spin" />
                  Synthesizing...
                </>
              ) : (
                <>
                  <Sparkles className="icon-sm" />
                  Ask Knowledge Base
                </>
              )}
            </button>
          </div>
        </form>

        {/* 4. Suggested Mining Queries */}
        <div className="rag-sample-queries">
          <span className="sample-queries-label">Sample Questions:</span>
          <div className="sample-queries-list">
            {SAMPLE_QUERIES.map((sample, idx) => {
              const SampleIcon = sample.icon;
              return (
                <button
                  key={idx}
                  className="sample-query-pill"
                  onClick={() => {
                    setQuery(sample.query);
                    handleQuery(sample.query);
                  }}
                  disabled={loading}
                >
                  <SampleIcon size={13} strokeWidth={1.8} className="sample-icon" aria-hidden="true" />
                  <span className="sample-title">{sample.title}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 5. Error State Banner */}
      {error && (
        <div className="alert-banner alert-danger" id="rag-error-banner">
          <AlertCircle className="icon-md" />
          <div className="alert-content">
            <strong>Query Error:</strong> {error}
          </div>
        </div>
      )}

      {/* 6. Grounded Answer Card */}
      {result && (
        <div className="rag-results-container" id="rag-results-panel">
          <div className="card answer-card">
            <div className="answer-header">
              <div className="answer-title-group">
                <ShieldCheck className="icon-md text-emerald" />
                <h3 className="answer-title">Grounded AI Answer</h3>
                {result.evidence_found ? (
                  <span className="badge badge-success">
                    <CheckCircle2 className="icon-xs inline-icon" /> Supported by Evidence
                  </span>
                ) : (
                  <span className="badge badge-warning">
                    <HelpCircle className="icon-xs inline-icon" /> Insufficient Evidence
                  </span>
                )}
              </div>

              <div className="answer-meta-group">
                <span className="meta-chip">
                  <Cpu className="icon-xs" /> {result.model_used}
                </span>
                <span className="meta-chip">
                  <Clock className="icon-xs" /> {result.latency_ms} ms
                </span>
                <span className="meta-chip">
                  <Layers className="icon-xs" /> {result.sources_count} source chunks
                </span>
              </div>
            </div>

            <div className="answer-body" id="rag-answer-text">
              {result.answer.split('\n\n').map((paragraph, pIdx) => (
                <p key={pIdx}>{paragraph}</p>
              ))}
            </div>

            {!result.evidence_found && (
              <div className="insufficient-evidence-note">
                <AlertCircle className="icon-sm text-amber" />
                <span>
                  The assistant adhered to strict anti-hallucination rules and confirmed that
                  no supported facts exist in the indexed documents for this query.
                </span>
              </div>
            )}
          </div>

          {/* 7. Source Citations & Evidence Chunks */}
          <div className="sources-section">
            <div className="sources-header">
              <h4 className="sources-title">
                Page-Level Citations & Document Evidence ({result.sources.length})
              </h4>
              <span className="sources-subtext">
                Ranked by cosine similarity against {status?.embedding_model || 'Gemini Embeddings'}
              </span>
            </div>

            <div className="sources-grid">
              {result.sources.map((source, sIdx) => {
                const isExpanded = !!expandedSources[source.chunk_id];
                const scorePercent = Math.round(source.score * 100);

                return (
                  <div
                    key={source.chunk_id || sIdx}
                    className={`source-card card ${isExpanded ? 'source-card-expanded' : ''}`}
                    id={`source-card-${sIdx}`}
                  >
                    <div
                      className="source-card-header"
                      onClick={() => toggleSourceExpand(source.chunk_id)}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="source-info">
                        <div className="source-badges">
                          <span className="source-index-badge">#{sIdx + 1}</span>
                          <span className="source-file-badge">
                            {source.source_type === 'table' ? (
                              <TableIcon className="icon-xs" />
                            ) : (
                              <FileText className="icon-xs" />
                            )}
                            {source.filename}
                          </span>
                          <span className="badge badge-accent">Page {source.page_number}</span>
                          <span className="badge badge-subtle">{source.source_type.toUpperCase()}</span>
                          {source.section && (
                            <span className="badge badge-outline">{source.section}</span>
                          )}
                        </div>
                      </div>

                      <div className="source-score-wrapper">
                        <div className="score-label">
                          <span>Match:</span>
                          <strong>{scorePercent}%</strong>
                        </div>
                        <div className="score-bar-bg">
                          <div
                            className="score-bar-fill"
                            style={{ width: `${Math.min(100, Math.max(0, scorePercent))}%` }}
                          />
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="icon-sm text-subtle" />
                        ) : (
                          <ChevronDown className="icon-sm text-subtle" />
                        )}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="source-evidence-body">
                        <div className="evidence-header">
                          <span className="evidence-label">EXACT EXTRACTED EVIDENCE:</span>
                        </div>
                        <pre className="evidence-snippet">{source.text}</pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
