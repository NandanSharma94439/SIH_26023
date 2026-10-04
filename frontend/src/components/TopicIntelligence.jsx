import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  BookOpen,
  Tag,
  BarChart2,
  FileText,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Layers,
} from 'lucide-react';
import api from '../services/api';
import { animatePageEntrance, animateStaggerEntrance, isReducedMotion } from '../services/motion';

/* ──────────────────────────────────────────────────────────────────────────
   SVG Word Cloud — lightweight, no external dep, fully responsive
   Renders keyword bubbles in a radial spiral layout sized by relevance.
   ────────────────────────────────────────────────────────────────────────── */
function WordCloudSVG({ words }) {
  const containerRef = useRef(null);
  const [dims, setDims] = useState({ w: 720, h: 340 });

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      const { width } = entries[0].contentRect;
      setDims({ w: width, h: Math.max(260, Math.min(360, width * 0.45)) });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const placed = useMemo(() => {
    if (!words || !words.length) return [];
    const cx = dims.w / 2;
    const cy = dims.h / 2;
    const top = words.slice(0, 50);
    const maxVal = Math.max(...top.map((w) => w.value), 1);
    const minVal = Math.min(...top.map((w) => w.value), 0);
    const range = Math.max(maxVal - minVal, 1);

    const fontSize = (v) => 10 + 26 * ((v - minVal) / range);

    // Approximate text width in SVG
    const approxW = (text, fs) => text.length * fs * 0.55;
    const approxH = (fs) => fs * 1.3;

    const placed = [];
    const rects = []; // bounding boxes of placed items

    const overlaps = (x, y, w, h) => {
      for (const r of rects) {
        if (
          x < r.x + r.w + 6 &&
          x + w + 6 > r.x &&
          y < r.y + r.h + 4 &&
          y + h + 4 > r.y
        ) return true;
      }
      return false;
    };

    // Color palette aligned with design system
    const PALETTE = [
      'var(--stratum-teal)',
      'var(--stratum-accent)',
      'var(--text-secondary)',
      'var(--stratum-emerald)',
      'var(--color-amber)',
    ];

    let angle = 0;
    let radius = 0;
    let step = 0;
    const goldenAngle = 2.399963; // radians

    for (const word of top) {
      const fs = fontSize(word.value);
      const tw = approxW(word.text, fs);
      const th = approxH(fs);

      let placed_x = 0;
      let placed_y = 0;
      let found = false;

      for (let attempt = 0; attempt < 300; attempt++) {
        const x = cx + radius * Math.cos(angle) - tw / 2;
        const y = cy + radius * Math.sin(angle) - th / 2;

        if (
          x >= 4 &&
          y >= 4 &&
          x + tw <= dims.w - 4 &&
          y + th <= dims.h - 4 &&
          !overlaps(x, y, tw, th)
        ) {
          placed_x = x;
          placed_y = y;
          found = true;
          break;
        }
        angle += goldenAngle;
        radius = 5 + step * 2.2;
        step++;
      }

      if (found) {
        rects.push({ x: placed_x, y: placed_y, w: tw, h: th });
        placed.push({
          text: word.text,
          x: placed_x + tw / 2,
          y: placed_y + th / 2 + fs * 0.35,
          fontSize: fs,
          color: PALETTE[placed.length % PALETTE.length],
          count: word.count,
          value: word.value,
        });
      }
    }
    return placed;
  }, [words, dims]);

  return (
    <div ref={containerRef} className="word-cloud-container" aria-label="Keyword word cloud visualization">
      {placed.length === 0 ? (
        <div className="word-cloud-empty">
          <Tag size={28} className="text-muted" />
          <p>No word cloud data available.</p>
        </div>
      ) : (
        <svg
          viewBox={`0 0 ${dims.w} ${dims.h}`}
          width="100%"
          height={dims.h}
          className="word-cloud-svg"
          aria-hidden="true"
        >
          {placed.map((item, i) => (
            <text
              key={i}
              x={item.x}
              y={item.y}
              fontSize={item.fontSize}
              fill={item.color}
              textAnchor="middle"
              className="word-cloud-word"
              opacity={0.85 + 0.15 * (item.value / 100)}
            >
              <title>{item.text} — {item.count} occurrences</title>
              {item.text}
            </text>
          ))}
        </svg>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
   Topic Card
   ────────────────────────────────────────────────────────────────────────── */
function TopicCard({ topic, index }) {
  const [expanded, setExpanded] = useState(false);

  const scorePercent = Math.round(topic.score * 100);
  const scoreClass =
    scorePercent >= 70 ? 'score-high' : scorePercent >= 40 ? 'score-mid' : 'score-low';

  return (
    <div className="topic-card card scroll-reveal" style={{ animationDelay: `${index * 40}ms` }}>
      <div className="topic-card-header">
        <div className="topic-card-meta">
          <span className="topic-rank">#{index + 1}</span>
          <div className="topic-name-group">
            <h3 className="topic-name">{topic.name}</h3>
            <span className="topic-doc-count">
              {topic.document_count} {topic.document_count === 1 ? 'source' : 'sources'}
            </span>
          </div>
        </div>
        <div className="topic-score-group">
          <span className={`topic-score-badge ${scoreClass}`}>{scorePercent}%</span>
          <div className="topic-score-bar" aria-label={`Relevance ${scorePercent}%`}>
            <div
              className={`topic-score-fill ${scoreClass}`}
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>
      </div>

      <div className="topic-keywords-row">
        {topic.keywords.slice(0, 6).map((kw) => (
          <span key={kw} className="topic-keyword-chip">{kw}</span>
        ))}
      </div>

      {topic.document_names && topic.document_names.length > 0 && (
        <div className="topic-sources-section">
          <button
            className="btn-link topic-sources-toggle"
            onClick={() => setExpanded((p) => !p)}
            aria-expanded={expanded}
          >
            {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            Sources ({topic.document_names.length})
          </button>
          {expanded && (
            <ul className="topic-sources-list">
              {topic.document_names.map((name) => (
                <li key={name} className="topic-source-item">
                  <FileText size={11} aria-hidden="true" />
                  <span>{name}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
   Keyword Table Row
   ────────────────────────────────────────────────────────────────────────── */
function KeywordRow({ kw, rank }) {
  const relevancePct = Math.round(kw.relevance * 100);
  return (
    <tr className="keyword-row">
      <td className="keyword-rank font-mono text-muted">{rank}</td>
      <td className="keyword-word">
        <span className="keyword-chip">{kw.word}</span>
      </td>
      <td className="keyword-count font-mono">{kw.count.toLocaleString()}</td>
      <td className="keyword-relevance">
        <div className="kw-relevance-bar-wrap">
          <div
            className="kw-relevance-bar"
            style={{ width: `${relevancePct}%` }}
            aria-label={`${relevancePct}%`}
          />
          <span className="kw-relevance-label font-mono">{relevancePct}%</span>
        </div>
      </td>
      <td className="keyword-docs text-muted text-sm">
        {kw.documents.slice(0, 2).join(', ')}
        {kw.documents.length > 2 && <span> +{kw.documents.length - 2}</span>}
      </td>
    </tr>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
   Main Component
   ────────────────────────────────────────────────────────────────────────── */
export default function TopicIntelligence() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scope, setScope] = useState('all');
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const containerRef = useRef(null);
  const topicsRef = useRef(null);

  // Load documents for scope selector
  useEffect(() => {
    api.listDocuments().then((res) => {
      if (res.success && res.data) {
        const unique = [];
        const seen = new Set();
        for (const d of res.data) {
          const name = d.filename || d.original_filename;
          if (!seen.has(name)) { seen.add(name); unique.push(d); }
        }
        setDocuments(unique);
        if (unique.length > 0) setSelectedDocId(unique[0].id);
      }
    });
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params = scope === 'selected' && selectedDocId
      ? { document_id: selectedDocId }
      : {};
    const res = await api.getTopicSummary(params);
    if (res.success) {
      setData(res.data);
    } else {
      setError(res.error || 'Failed to load topic analysis.');
    }
    setLoading(false);
  }, [scope, selectedDocId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Animate entrance when data loads
  useEffect(() => {
    if (data && containerRef.current && !isReducedMotion()) {
      animatePageEntrance(containerRef.current);
    }
  }, [data]);

  useEffect(() => {
    if (data && topicsRef.current && !isReducedMotion()) {
      animateStaggerEntrance(topicsRef.current, '.topic-card');
    }
  }, [data]);

  // ── Derived / Memoized
  const topTopic = data?.topics?.[0] ?? null;
  const keywordCount = data?.total_keywords_extracted ?? 0;
  const docCount = data?.total_documents_analyzed ?? 0;
  const topicCount = data?.total_topics_detected ?? 0;

  // ── Render helpers
  const renderScopeBar = () => (
    <div className="topic-scope-bar card">
      <div className="scope-indicator-left">
        <span className="scope-toggle-label">Scope:</span>
        <div className="view-mode-toggle" role="group" aria-label="Analysis Scope">
          <button
            type="button"
            className={`mode-toggle-btn ${scope === 'all' ? 'active' : ''}`}
            onClick={() => setScope('all')}
            id="topic-scope-all"
          >
            All Documents
          </button>
          <button
            type="button"
            className={`mode-toggle-btn ${scope === 'selected' ? 'active' : ''}`}
            onClick={() => setScope('selected')}
            id="topic-scope-selected"
            disabled={documents.length === 0}
          >
            Current Document
          </button>
        </div>
      </div>
      {scope === 'selected' && documents.length > 0 && (
        <div className="scope-indicator-right">
          <select
            className="select-input"
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            id="topic-doc-select"
            aria-label="Select document"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>{d.filename}</option>
            ))}
          </select>
        </div>
      )}
      <button
        className="btn btn-icon"
        onClick={fetchData}
        title="Refresh analysis"
        disabled={loading}
        id="topic-refresh-btn"
      >
        <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
      </button>
    </div>
  );

  const renderSkeleton = () => (
    <div className="topic-skeleton">
      <div className="skeleton-strip skeleton-w-full skeleton-h-32" />
      <div className="skeleton-row">
        <div className="skeleton-strip skeleton-w-half skeleton-h-24" />
        <div className="skeleton-strip skeleton-w-half skeleton-h-24" />
      </div>
      {[1, 2, 3].map((i) => (
        <div key={i} className="skeleton-strip skeleton-full skeleton-h-16" />
      ))}
    </div>
  );

  const renderError = () => (
    <div className="alert-banner alert-error">
      <AlertCircle size={18} />
      <div className="alert-content">
        <strong>Analysis Failed:</strong> {error}
      </div>
      <button className="btn btn-outline btn-sm" onClick={fetchData}>Retry</button>
    </div>
  );

  const renderEmpty = () => (
    <div className="topic-empty-state card">
      <Layers size={36} className="text-muted" />
      <h3>No Documents Processed</h3>
      <p>Upload and ingest geological documents in the Document Intelligence module to generate topic analysis.</p>
    </div>
  );

  return (
    <div className="topic-intelligence-container" id="topic-intelligence-module" ref={containerRef}>
      {/* 1. Hero */}
      <div className="module-hero card">
        <div className="hero-content">
          <div className="analytics-eyebrow">
            <span className="eyebrow-dot" />
            CMPDI AUTOMATED TOPIC IDENTIFICATION
          </div>
          <h2 className="hero-title">Topic Intelligence</h2>
          <p className="hero-description">
            Automatically identify dominant themes and terminology across geological and
            mining documents. Keyword relevance is computed using TF-IDF scoring over the
            full document corpus. Topics are matched against geological and mining domain
            clusters derived from actual document content.
          </p>
        </div>

        {/* Overview metrics */}
        {!loading && data && (
          <div className="telemetry-stat-grid">
            <div className="stat-card">
              <span className="stat-label">DOCUMENTS ANALYZED</span>
              <span className="stat-value text-cyan">{docCount}</span>
              <span className="stat-subtext">{scope === 'all' ? 'Full Corpus' : 'Selected File'}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">TOPICS DETECTED</span>
              <span className="stat-value text-amber">{topicCount}</span>
              <span className="stat-subtext">Geological Domains</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">KEYWORDS EXTRACTED</span>
              <span className="stat-value text-emerald">{keywordCount}</span>
              <span className="stat-subtext">Ranked by TF-IDF</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">TOP TOPIC</span>
              <span className="stat-value text-orange" style={{ fontSize: 'var(--font-size-sm)', lineHeight: 1.3 }}>
                {data?.top_topic ?? '—'}
              </span>
              <span className="stat-subtext">Highest Relevance</span>
            </div>
          </div>
        )}
      </div>

      {/* 2. Scope Bar */}
      {renderScopeBar()}

      {/* 3. Body */}
      {loading && renderSkeleton()}
      {!loading && error && renderError()}
      {!loading && !error && (!data || docCount === 0) && renderEmpty()}

      {!loading && !error && data && docCount > 0 && (
        <>
          {/* 4. Word Cloud */}
          <div className="card topic-section">
            <div className="section-header">
              <h3 className="section-title">
                <Tag size={16} aria-hidden="true" />
                Keyword Word Cloud
              </h3>
              <span className="section-subtitle text-muted">
                Word size reflects TF-IDF relevance — derived from real document content
              </span>
            </div>
            <WordCloudSVG words={data.word_cloud} />
          </div>

          {/* 5. Detected Topics */}
          <div className="topic-section">
            <div className="section-header section-header-standalone">
              <h3 className="section-title">
                <Layers size={16} aria-hidden="true" />
                Detected Topics
              </h3>
              <span className="section-subtitle text-muted">
                {topicCount} geological and mining domain topics identified
              </span>
            </div>
            <div className="topic-cards-grid" ref={topicsRef}>
              {data.topics.map((topic, i) => (
                <TopicCard key={topic.name} topic={topic} index={i} />
              ))}
              {data.topics.length === 0 && (
                <div className="card topic-empty-inline">
                  <AlertCircle size={18} className="text-muted" />
                  <p>No topics detected from the current document scope.</p>
                </div>
              )}
            </div>
          </div>

          {/* 6. Keyword Intelligence Table */}
          <div className="card topic-section">
            <div className="section-header">
              <h3 className="section-title">
                <BarChart2 size={16} aria-hidden="true" />
                Keyword Intelligence
              </h3>
              <span className="section-subtitle text-muted">
                Top {data.top_keywords.length} keywords ranked by TF-IDF relevance score
              </span>
            </div>
            <div className="table-wrapper">
              <table className="data-table keyword-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Keyword</th>
                    <th>Frequency</th>
                    <th>Relevance</th>
                    <th>Sources</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_keywords.map((kw, i) => (
                    <KeywordRow key={kw.word} kw={kw} rank={i + 1} />
                  ))}
                  {data.top_keywords.length === 0 && (
                    <tr>
                      <td colSpan={5} className="table-empty">
                        <div className="empty-scoped-state">
                          <AlertCircle size={18} className="empty-scoped-icon text-muted" />
                          <div className="empty-scoped-content">
                            <div className="empty-scoped-title">No keywords extracted.</div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
