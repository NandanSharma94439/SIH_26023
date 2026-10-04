import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  BarChart3,
  Layers,
  Pickaxe,
  TrendingUp,
  FileSpreadsheet,
  FileText,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  ChevronRight,
  Database,
  Compass,
  Flame,
  Activity,
  ArrowRight,
  RefreshCw,
  FolderOpen,
  PieChart as PieIcon,
  Table as TableIcon,
  SlidersHorizontal,
  Info,
  X,
  Check
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import api from '../services/api';

const COLORS = [
  '#6b4e3d', // Coffee / Walnut brand
  '#57706d', // Geological Stratum Teal
  '#98624c', // Iron Oxide Terracotta
  '#71806a', // Geological Sage
  '#a96545', // Warm Ochre
  '#8b6a54', // Coffee Light
  '#6d7475', // Slate Blue
  '#30251f', // Deep Espresso
];

/**
 * Shorten organization / subsidiary names for clean single-line Y-axis display.
 * Retains recognized operational abbreviations (CMPDI, CCL, WCL, SECL, MCL, BCCL, NCL, etc.)
 */
function formatSubsidiaryLabel(rawName) {
  if (!rawName || typeof rawName !== 'string') return '';
  const trimmed = rawName.trim();

  // Known CIL subsidiary direct mappings
  const knownMap = {
    'central mine planning & design institute limited (cmpdi)': 'CMPDI',
    'central mine planning and design institute limited (cmpdi)': 'CMPDI',
    'central mine planning & design institute limited': 'CMPDI',
    'central mine planning and design institute limited': 'CMPDI',
    'central mine planning & design institute': 'CMPDI',
    'central coalfields limited (ccl)': 'CCL',
    'central coalfields limited': 'CCL',
    'western coalfields limited (wcl)': 'WCL',
    'western coalfields limited': 'WCL',
    'south eastern coalfields limited (secl)': 'SECL',
    'south eastern coalfields limited': 'SECL',
    'mahanadi coalfields limited (mcl)': 'MCL',
    'mahanadi coalfields limited': 'MCL',
    'northern coalfields limited (ncl)': 'NCL',
    'northern coalfields limited': 'NCL',
    'bharat coking coal limited (bccl)': 'BCCL',
    'bharat coking coal limited': 'BCCL',
    'eastern coalfields limited (ecl)': 'ECL',
    'eastern coalfields limited': 'ECL',
    'coal india limited (cil)': 'CIL',
    'coal india limited': 'CIL',
    'cmpdi / cil': 'CMPDI / CIL',
    'cmpdi/cil': 'CMPDI / CIL',
  };

  const lower = trimmed.toLowerCase();
  if (knownMap[lower]) {
    return knownMap[lower];
  }

  // If rawName contains an abbreviation in parentheses e.g. "Institute Name (ABC)"
  const parenMatch = trimmed.match(/\(([A-Z0-9&/-]{2,10})\)/i);
  if (parenMatch && parenMatch[1]) {
    return parenMatch[1].toUpperCase();
  }

  // If already short, keep it as-is
  if (trimmed.length <= 14) {
    return trimmed;
  }

  // Intelligent truncation for unknown entities (18-22 chars max)
  return trimmed.slice(0, 20) + '...';
}

/**
 * Return the full professional name for tooltip display.
 */
function getFullSubsidiaryName(rawName) {
  if (!rawName || typeof rawName !== 'string') return '';
  const trimmed = rawName.trim();

  const fullMap = {
    'ccl': 'Central Coalfields Limited (CCL)',
    'wcl': 'Western Coalfields Limited (WCL)',
    'secl': 'South Eastern Coalfields Limited (SECL)',
    'mcl': 'Mahanadi Coalfields Limited (MCL)',
    'ncl': 'Northern Coalfields Limited (NCL)',
    'bccl': 'Bharat Coking Coal Limited (BCCL)',
    'ecl': 'Eastern Coalfields Limited (ECL)',
    'cmpdi': 'Central Mine Planning & Design Institute Limited (CMPDI)',
    'cmpdi / cil': 'CMPDI / Coal India Limited (CIL)',
    'cmpdi/cil': 'CMPDI / Coal India Limited (CIL)',
    'cil': 'Coal India Limited (CIL)',
  };

  const lower = trimmed.toLowerCase();
  if (fullMap[lower]) {
    return fullMap[lower];
  }

  return trimmed;
}

/**
 * Custom tick renderer for Subsidiary Y-Axis:
 * Strict single-line, nowrap, IBM Plex Sans 12px, font-weight 500
 */
const renderSubsidiaryYTick = ({ x, y, payload }) => {
  const shortLabel = formatSubsidiaryLabel(payload?.value || '');
  return (
    <text
      x={x}
      y={y}
      dy={4}
      textAnchor="end"
      fill="var(--text-muted)"
      style={{
        fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif",
        fontSize: '12px',
        fontWeight: 500,
        whiteSpace: 'nowrap',
      }}
    >
      {shortLabel}
    </text>
  );
};

export default function MiningAnalytics({ onNavigateToReports }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Analytics Datasets
  const [summary, setSummary] = useState(null);
  const [drilling, setDrilling] = useState(null);
  const [resources, setResources] = useState(null);
  const [projectsData, setProjectsData] = useState(null);
  const [qualityData, setQualityData] = useState(null);
  const [metricsData, setMetricsData] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);

  // Filters for sub-views
  const [projectSubFilter, setProjectSubFilter] = useState('all');
  const [projectSearch, setProjectSearch] = useState('');
  const [metricCatFilter, setMetricCatFilter] = useState('all');
  const [metricUnitFilter, setMetricUnitFilter] = useState('all');
  const [metricSearch, setMetricSearch] = useState('');

  // Provenance Modal
  const [provenanceModal, setProvenanceModal] = useState(null);

  // Fetch document list on mount
  useEffect(() => {
    async function loadDocs() {
      const res = await api.listDocuments();
      if (res.success && Array.isArray(res.data)) {
        const unique = [];
        const seen = new Set();
        for (const d of res.data) {
          const name = d.filename || d.original_filename;
          if (name && !seen.has(name)) {
            seen.add(name);
            unique.push(d);
          }
        }
        setDocuments(unique);
      }
    }
    loadDocs();
  }, []);

  // Fetch all analytics for selected scope
  const fetchAnalytics = useCallback(async (scopeDoc) => {
    setLoading(true);
    setError(null);
    try {
      const docParam = scopeDoc === 'all' ? {} : { source_document: scopeDoc };

      const [sumRes, drillRes, resRes, projRes, qualRes, metRes, compRes] = await Promise.all([
        api.getAnalyticsSummary(docParam),
        api.getDrillingAnalytics(docParam),
        api.getResourceAnalytics(docParam),
        api.getProjectAnalytics({ ...docParam, subsidiary: projectSubFilter !== 'all' ? projectSubFilter : undefined, search: projectSearch || undefined }),
        api.getCoalQualityAnalytics(docParam),
        api.getGeologicalMetricsExplorer({
          ...docParam,
          category: metricCatFilter !== 'all' ? metricCatFilter : undefined,
          unit: metricUnitFilter !== 'all' ? metricUnitFilter : undefined,
          search: metricSearch || undefined,
          limit: 150
        }),
        api.getCrossDocumentComparison(),
      ]);

      if (sumRes.success) setSummary(sumRes.data);
      if (drillRes.success) setDrilling(drillRes.data);
      if (resRes.success) setResources(resRes.data);
      if (projRes.success) setProjectsData(projRes.data);
      if (qualRes.success) setQualityData(qualRes.data);
      if (metRes.success) setMetricsData(metRes.data);
      if (compRes.success) setComparisonData(compRes.data);
    } catch (err) {
      setError(err.message || 'Failed to load mining analytics.');
    } finally {
      setLoading(false);
    }
  }, [projectSubFilter, projectSearch, metricCatFilter, metricUnitFilter, metricSearch]);

  // Refetch when scope changes
  useEffect(() => {
    fetchAnalytics(selectedDoc);
  }, [selectedDoc, fetchAnalytics]);

  // Open provenance helper
  const openProvenance = (title, prov) => {
    if (!prov) return;
    setProvenanceModal({
      title,
      source_document: prov.source_document || selectedDoc,
      source_page: prov.source_page || 1,
      evidence_text: prov.evidence_text || 'Verified against canonical extraction database.',
    });
  };

  // Prepare chart data for drilling target vs achievement
  const drillingChartData = useMemo(() => {
    if (!drilling?.targets_vs_achievements) return [];
    return drilling.targets_vs_achievements
      .filter(item => item.achieved !== null || item.target !== null)
      .map(item => ({
        agency: item.agency
          .replace(/\s*\((Departmental|Contractual)\)/i, '')
          .replace(' Departmental', '')
          .replace(' Contractual', ''),
        fullAgency: item.agency,
        Achieved: item.achieved || 0,
        Target: item.target || 0,
        unit: item.unit,
        pct: item.achievement_pct,
        provenance: item.provenance,
      }));
  }, [drilling]);

  // Prepare chart data for resource categories
  const resourceChartData = useMemo(() => {
    if (!resources?.resource_categories) return [];
    return resources.resource_categories.map(c => ({
      name: c.category,
      value: c.value,
      unit: c.unit,
      provenance: c.provenance,
    }));
  }, [resources]);

  // Prepare subsidiary breakdown chart data
  const subsidiaryChartData = useMemo(() => {
    if (!projectsData?.subsidiary_breakdown) return [];
    return projectsData.subsidiary_breakdown.map((s, idx) => ({
      name: s.subsidiary, // RAW original name preserved for tooltip
      shortName: formatSubsidiaryLabel(s.subsidiary),
      count: s.count,
      color: COLORS[idx % COLORS.length],
    }));
  }, [projectsData]);

  // Dynamic active subsidiary list for chart subtitle
  const activeSubsidiaryList = useMemo(() => {
    if (!projectsData?.subsidiary_breakdown) return 'CMPDI, CCL, WCL, SECL, MCL';
    const names = projectsData.subsidiary_breakdown
      .map((s) => formatSubsidiaryLabel(s.subsidiary))
      .filter(Boolean);
    return [...new Set(names)].join(', ');
  }, [projectsData]);

  // Dynamic total count for chart badge
  const totalProjectsCount = useMemo(() => {
    if (projectsData?.total_projects !== undefined && projectsData?.total_projects !== null) {
      return projectsData.total_projects;
    }
    return subsidiaryChartData.reduce((acc, curr) => acc + (curr.count || 0), 0);
  }, [projectsData, subsidiaryChartData]);

  // Prepare promotional block chart data
  const promoBlockChartData = useMemo(() => {
    if (!drilling?.promotional_drilling_by_block) return [];
    return drilling.promotional_drilling_by_block.map(b => ({
      block: b.block_name,
      metres: b.drilling_metres,
      provenance: b.provenance,
    }));
  }, [drilling]);

  return (
    <div className="analytics-container">
      {/* Top Banner & Control Toolbar */}
      <div className="analytics-header-card">
        <div className="analytics-header-left">
          <div className="analytics-eyebrow">
            <span className="eyebrow-dot" />
            CMPDI EXPLORATION INTELLIGENCE
          </div>
          <h2 className="analytics-title">Geological & Drilling Analytics</h2>
          <p className="analytics-subtitle">
            Executive exploration intelligence, drilling target vs. achievement analysis, coal resource classifications, and metric auditing with verified document provenance.
          </p>
        </div>

        <div className="analytics-header-actions">
          {/* Document Scope Selector */}
          <div className="analytics-scope-picker">
            <label className="picker-label">
              <FolderOpen size={14} className="picker-icon" />
              Document Scope:
            </label>
            <select
              className="analytics-select"
              value={selectedDoc}
              onChange={(e) => setSelectedDoc(e.target.value)}
              id="analytics-doc-scope-select"
            >
              <option value="all">Cumulative (All Indexed Documents)</option>
              {documents.map((d) => {
                const name = d.filename || d.original_filename;
                return (
                  <option key={d.id || name} value={name}>
                    {name} ({d.file_type ? d.file_type.toUpperCase() : 'DOC'})
                  </option>
                );
              })}
            </select>
          </div>

          <button
            className="action-button button-secondary"
            onClick={() => fetchAnalytics(selectedDoc)}
            disabled={loading}
            title="Refresh analytics data"
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            Refresh
          </button>

          {onNavigateToReports && (
            <button
              className="action-button button-primary"
              onClick={() => onNavigateToReports(selectedDoc)}
              title="Generate Geological Report for this scope"
            >
              <FileSpreadsheet size={14} />
              Open Geological Report
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="analytics-kpi-grid">
        {/* KPI 1: Mines & Projects */}
        <div className="kpi-card" id="kpi-mines-projects">
          <div className="kpi-card-header">
            <span className="kpi-label">Mines & Projects</span>
            <Pickaxe size={18} className="kpi-icon text-amber" />
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value">{summary ? summary.total_mines_projects : '...'}</span>
            <span className="kpi-unit">records</span>
          </div>
          <div className="kpi-footer">
            <span className="kpi-subtext">Verified mining units</span>
            {summary?.provenance_map && Object.keys(summary.provenance_map).length > 0 && (
              <button
                className="kpi-prov-btn"
                onClick={() => openProvenance('Mines & Projects', { source_document: selectedDoc, source_page: 10, evidence_text: `${summary.total_mines_projects} mine/project records extracted from ${selectedDoc}.` })}
              >
                Provenance
              </button>
            )}
          </div>
        </div>

        {/* KPI 2: Geological Metrics */}
        <div className="kpi-card" id="kpi-geological-metrics">
          <div className="kpi-card-header">
            <span className="kpi-label">Geological Metrics</span>
            <Activity size={18} className="kpi-icon text-cyan" />
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value">{summary ? summary.total_geological_metrics : '...'}</span>
            <span className="kpi-unit">metrics</span>
          </div>
          <div className="kpi-footer">
            <span className="kpi-subtext">Verified parameters</span>
            <button
              className="kpi-prov-btn"
              onClick={() => openProvenance('Geological Metrics', { source_document: selectedDoc, source_page: 9, evidence_text: `${summary?.total_geological_metrics} metrics cataloged across exploration and operational domains.` })}
            >
              Provenance
            </button>
          </div>
        </div>

        {/* KPI 3: Exploratory Drilling */}
        <div className="kpi-card" id="kpi-drilling-achieved">
          <div className="kpi-card-header">
            <span className="kpi-label">Exploratory Drilling</span>
            <TrendingUp size={18} className="kpi-icon text-emerald" />
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value">
              {summary?.total_exploratory_drilling_achieved_m !== null && summary?.total_exploratory_drilling_achieved_m !== undefined
                ? summary.total_exploratory_drilling_achieved_m.toLocaleString()
                : 'N/A'}
            </span>
            <span className="kpi-unit">metre</span>
          </div>
          <div className="kpi-footer">
            {summary?.total_exploratory_drilling_achieved_m !== null && summary?.total_exploratory_drilling_achieved_m !== undefined ? (
              <span className="kpi-tag-highlight">
                {summary?.drilling_achievement_pct ? `${summary.drilling_achievement_pct}% Target Met` : 'Dept. & State Govts'}
              </span>
            ) : (
              <span className="kpi-subtext">No drilling data in scope</span>
            )}
            {summary?.provenance_map?.['Total Exploratory Drilling Achieved'] && (
              <button
                className="kpi-prov-btn"
                onClick={() => openProvenance('Exploratory Drilling Achievement', summary.provenance_map['Total Exploratory Drilling Achieved'])}
              >
                Provenance
              </button>
            )}
          </div>
        </div>

        {/* KPI 4: Additional Coal Resources */}
        <div className="kpi-card" id="kpi-coal-resources">
          <div className="kpi-card-header">
            <span className="kpi-label">Additional Coal Resources</span>
            <Database size={18} className="kpi-icon text-indigo" />
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value">
              {summary?.additional_coal_resources_bt !== null && summary?.additional_coal_resources_bt !== undefined
                ? summary.additional_coal_resources_bt
                : 'N/A'}
            </span>
            <span className="kpi-unit">Billion Tonnes</span>
          </div>
          <div className="kpi-footer">
            <span className="kpi-subtext">
              {summary?.proved_resources_bt ? `${summary.proved_resources_bt} Bt Proved | ${summary.indicated_resources_bt} Bt Ind` : 'Resource estimates'}
            </span>
            {summary?.provenance_map?.['Additional coal resources estimated'] && (
              <button
                className="kpi-prov-btn"
                onClick={() => openProvenance('Additional Coal Resources', summary.provenance_map['Additional coal resources estimated'])}
              >
                Provenance
              </button>
            )}
          </div>
        </div>

        {/* KPI 5: Reports & Plans */}
        <div className="kpi-card" id="kpi-reports-prepared">
          <div className="kpi-card-header">
            <span className="kpi-label">Reports & Plans</span>
            <FileText size={18} className="kpi-icon text-pink" />
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value">
              {summary?.total_reports_prepared !== null && summary?.total_reports_prepared !== undefined
                ? summary.total_reports_prepared
                : summary?.geological_reports_count !== null && summary?.geological_reports_count !== undefined
                ? summary.geological_reports_count
                : 'N/A'}
            </span>
            <span className="kpi-unit">reports</span>
          </div>
          <div className="kpi-footer">
            <span className="kpi-subtext">
              {summary?.geological_reports_count ? `${summary.geological_reports_count} Geological Reports` : 'Completed deliverables'}
            </span>
            {summary?.provenance_map?.['GEOLOGICAL REPORTS'] && (
              <button
                className="kpi-prov-btn"
                onClick={() => openProvenance('Geological Reports', summary.provenance_map['GEOLOGICAL REPORTS'])}
              >
                Provenance
              </button>
            )}
          </div>
        </div>

        {/* KPI 6: Geophysical Logging */}
        <div className="kpi-card" id="kpi-geophysical-logging">
          <div className="kpi-card-header">
            <span className="kpi-label">Geophysical Logging</span>
            <Compass size={18} className="kpi-icon text-cyan" />
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value">
              {summary?.geophysical_logging_depth_m !== null && summary?.geophysical_logging_depth_m !== undefined
                ? summary.geophysical_logging_depth_m.toLocaleString()
                : 'N/A'}
            </span>
            <span className="kpi-unit">depth m</span>
          </div>
          <div className="kpi-footer">
            <span className="kpi-subtext">
              {summary?.boreholes_logged_count ? `${summary.boreholes_logged_count} boreholes logged` : 'Sub-surface control'}
            </span>
            {summary?.provenance_map?.['Geophysical logging depth metre'] && (
              <button
                className="kpi-prov-btn"
                onClick={() => openProvenance('Geophysical Logging', summary.provenance_map['Geophysical logging depth metre'])}
              >
                Provenance
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="analytics-nav-tabs">
        <button
          className={`analytics-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <BarChart3 size={15} />
          Executive Overview
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'drilling' ? 'active' : ''}`}
          onClick={() => setActiveTab('drilling')}
        >
          <TrendingUp size={15} />
          Drilling Analytics
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'resources' ? 'active' : ''}`}
          onClick={() => setActiveTab('resources')}
        >
          <Database size={15} />
          Coal Resources
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'projects' ? 'active' : ''}`}
          onClick={() => setActiveTab('projects')}
        >
          <Pickaxe size={15} />
          Mines & Projects ({projectsData?.total_projects || 0})
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'quality' ? 'active' : ''}`}
          onClick={() => setActiveTab('quality')}
        >
          <Flame size={15} />
          Coal Quality (Proximate)
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'explorer' ? 'active' : ''}`}
          onClick={() => setActiveTab('explorer')}
        >
          <TableIcon size={15} />
          Metrics Explorer ({metricsData?.total || 0})
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'cross_doc' ? 'active' : ''}`}
          onClick={() => setActiveTab('cross_doc')}
        >
          <Layers size={15} />
          Cross-Document Comparison
        </button>
      </div>

      {/* TAB 1: EXECUTIVE OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="analytics-tab-content">
          <div className="analytics-cards-grid">
            {/* Drilling Target vs Achievement Chart */}
            <div className="analytics-chart-card">
              <div className="chart-card-header">
                <div className="chart-title-group">
                  <h3 className="chart-title">Drilling Target vs. Achievement</h3>
                  <span className="chart-subtitle">CMPDI Departmental, MECL Contractual, State Governments & Total (metres)</span>
                </div>
                <span className="badge badge-warning">Fiscal 2006-07</span>
              </div>
              <div className="chart-container-inner" style={{ height: 320 }}>
                {drillingChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={drillingChartData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="2 2" stroke="var(--chart-grid)" />
                      <XAxis dataKey="agency" stroke="var(--chart-axis)" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                      <YAxis
                        stroke="var(--chart-axis)"
                        tick={{ fontSize: 11, fill: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
                        tickFormatter={(val) => val.toLocaleString()}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'var(--bg-glass)',
                          borderColor: 'var(--border-glass)',
                          borderRadius: 8,
                          color: 'var(--text-primary)',
                          fontSize: 12,
                          boxShadow: 'var(--shadow-md)',
                        }}
                        labelFormatter={(label, payload) => payload?.[0]?.payload?.fullAgency || label}
                        formatter={(val, name) => [`${val.toLocaleString()} m`, name]}
                      />
                      <Legend wrapperStyle={{ paddingTop: 10, fontSize: 11 }} />
                      <Bar dataKey="Target" fill="var(--text-muted)" opacity={0.5} radius={[2, 2, 0, 0]} name="Target (m)" />
                      <Bar dataKey="Achieved" fill="var(--color-brand)" radius={[2, 2, 0, 0]} name="Achieved (m)" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="analytics-empty-box">No drilling targets found in this document scope.</div>
                )}
              </div>
              <div className="chart-card-footer">
                <span className="footer-note">Source: CMPDI Annual Accounts & Reports | Provenance Verified</span>
                {drilling?.targets_vs_achievements?.[0]?.provenance && (
                  <button
                    className="view-ev-link"
                    onClick={() => openProvenance('Drilling Target vs Achievement', drilling.targets_vs_achievements[0].provenance)}
                  >
                    View Evidence (Page {drilling.targets_vs_achievements[0].provenance.source_page})
                  </button>
                )}
              </div>
            </div>

            {/* Subsidiary Project Distribution Chart */}
            <div className="analytics-chart-card">
              <div className="chart-card-header">
                <div className="chart-title-group">
                  <h3 className="chart-title">Mine Projects by Subsidiary</h3>
                  <span className="chart-subtitle">Breakdown across CIL subsidiaries ({activeSubsidiaryList})</span>
                </div>
                <span className="badge badge-cyan">{totalProjectsCount} Total</span>
              </div>
              <div className="chart-container-inner" style={{ height: 320 }}>
                {subsidiaryChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={subsidiaryChartData}
                      layout="vertical"
                      barSize={18}
                      barCategoryGap="20%"
                      margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
                    >
                      <CartesianGrid strokeDasharray="2 2" stroke="var(--chart-grid)" />
                      <XAxis
                        type="number"
                        stroke="var(--chart-axis)"
                        tick={{ fontSize: 11, fill: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
                      />
                      <YAxis
                        dataKey="name"
                        type="category"
                        stroke="var(--chart-axis)"
                        width={90}
                        interval={0}
                        tick={renderSubsidiaryYTick}
                      />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (!active || !payload || !payload.length) return null;
                          const entry = payload[0].payload;
                          const fullName = getFullSubsidiaryName(entry.name);
                          const count = payload[0].value;
                          return (
                            <div className="recharts-default-tooltip" style={{ minWidth: 220 }}>
                              <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4, lineHeight: 1.3 }}>
                                {fullName}
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)' }}>
                                <span
                                  style={{
                                    width: 8,
                                    height: 8,
                                    borderRadius: '50%',
                                    backgroundColor: entry.color || 'var(--color-brand)',
                                    display: 'inline-block',
                                  }}
                                />
                                <span>Projects: </span>
                                <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{count}</strong>
                              </div>
                            </div>
                          );
                        }}
                      />
                      <Bar dataKey="count" radius={[0, 2, 2, 0]}>
                        {subsidiaryChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="analytics-empty-box">No subsidiary project records in scope.</div>
                )}
              </div>
              <div className="chart-card-footer">
                <span className="footer-note">Includes detailed project reports, feasibility studies, and EMP records</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DRILLING ANALYTICS */}
      {activeTab === 'drilling' && (
        <div className="analytics-tab-content">
          <div className="analytics-section-title">
            <TrendingUp size={18} className="text-emerald" />
            Exploratory Drilling Breakdown & Operational Targets
          </div>

          {/* Agency Table */}
          <div className="analytics-table-card">
            <div className="table-card-header">
              <h4 className="table-heading">Agency-Wise Drilling Target vs. Achievement</h4>
              <span className="badge badge-subtle">Fiscal Period: 2006-07</span>
            </div>
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Agency / Category</th>
                  <th>Target</th>
                  <th>Achieved</th>
                  <th>Unit</th>
                  <th>Achievement %</th>
                  <th>Plan / Period</th>
                  <th>Audit Provenance</th>
                </tr>
              </thead>
              <tbody>
                {drilling?.targets_vs_achievements?.map((item, idx) => (
                  <tr key={idx}>
                    <td className="font-semibold text-primary">{item.agency}</td>
                    <td>{item.target !== null ? item.target.toLocaleString() : 'N/A'}</td>
                    <td className="text-emerald font-semibold">{item.achieved !== null ? item.achieved.toLocaleString() : 'N/A'}</td>
                    <td><span className="unit-pill">{item.unit}</span></td>
                    <td>
                      {item.achievement_pct !== null ? (
                        <span className={`status-pill ${item.achievement_pct >= 100 ? 'status-pill-green' : 'status-pill-amber'}`}>
                          {item.achievement_pct}%
                        </span>
                      ) : (
                        <span className="text-muted">N/A</span>
                      )}
                    </td>
                    <td>{item.fiscal_period || '2006-07'}</td>
                    <td>
                      {item.provenance ? (
                        <button
                          className="view-ev-btn"
                          onClick={() => openProvenance(item.agency, item.provenance)}
                        >
                          Page {item.provenance.source_page}
                        </button>
                      ) : (
                        <span className="text-muted">Direct</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Promotional Drilling & Non-CIL Cards */}
          <div className="analytics-two-col-grid">
            {/* Promotional Drilling by Block */}
            <div className="analytics-card-panel">
              <div className="panel-header">
                <h4 className="panel-heading">Promotional Drilling by Coalfield Block</h4>
                <span className="badge badge-emerald">Total: {drilling?.total_promotional_drilling_m ? `${drilling.total_promotional_drilling_m.toLocaleString()} m` : '6,879 m'}</span>
              </div>
              <div className="promo-blocks-list">
                {drilling?.promotional_drilling_by_block?.map((b, idx) => (
                  <div className="promo-block-item" key={idx}>
                    <div className="promo-block-info">
                      <span className="promo-block-name">{b.block_name}</span>
                      <span className="promo-block-meta">{b.fiscal_period} | Unit: {b.unit}</span>
                    </div>
                    <div className="promo-block-right">
                      <span className="promo-block-val">{b.drilling_metres.toLocaleString()} m</span>
                      {b.provenance && (
                        <button
                          className="view-ev-btn"
                          onClick={() => openProvenance(b.block_name, b.provenance)}
                        >
                          Page {b.provenance.source_page}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Non-CIL / Captive Blocks & Geophysical Logging */}
            <div className="analytics-card-panel">
              <div className="panel-header">
                <h4 className="panel-heading">Non-CIL Captive Exploration & Geophysical Logging</h4>
                <span className="badge badge-cyan">Special Exploration</span>
              </div>
              <div className="info-stat-list">
                <div className="info-stat-row">
                  <span className="info-stat-label">Exploratory Drilling in Non-CIL Blocks:</span>
                  <span className="info-stat-val">
                    {drilling?.non_cil_captive_blocks?.drilling_metres != null ? `${drilling.non_cil_captive_blocks.drilling_metres.toLocaleString()} m` : 'N/A'}
                  </span>
                </div>
                <div className="info-stat-row">
                  <span className="info-stat-label">Non-CIL Blocks Explored:</span>
                  <span className="info-stat-val">
                    {drilling?.non_cil_captive_blocks?.blocks_count != null ? `${drilling.non_cil_captive_blocks.blocks_count} blocks across ${drilling?.non_cil_captive_blocks?.coalfields_count || 'multiple'} coalfields` : 'N/A'}
                  </span>
                </div>
                <div className="info-stat-row">
                  <span className="info-stat-label">Detailed Exploration Reports:</span>
                  <span className="info-stat-val">
                    {drilling?.non_cil_captive_blocks?.reports_count != null ? `${drilling.non_cil_captive_blocks.reports_count} reports` : 'N/A'}
                  </span>
                </div>
                <div className="info-stat-row">
                  <span className="info-stat-label">Geophysical Logging Depth:</span>
                  <span className="info-stat-val">
                    {drilling?.geophysical_logging?.logging_depth_metres != null ? `${drilling.geophysical_logging.logging_depth_metres.toLocaleString()} depth metre (${drilling?.geophysical_logging?.boreholes_count || 'N/A'} boreholes)` : 'N/A'}
                  </span>
                </div>
                <div className="info-stat-row">
                  <span className="info-stat-label">Magnetic Survey Stations:</span>
                  <span className="info-stat-val">
                    {drilling?.geophysical_logging?.magnetic_survey_stations != null ? `${drilling.geophysical_logging.magnetic_survey_stations.toLocaleString()} stations` : 'N/A'}
                  </span>
                </div>
                <div className="info-stat-row">
                  <span className="info-stat-label">Surface Resistivity Profiling:</span>
                  <span className="info-stat-val">
                    {drilling?.geophysical_logging?.resistivity_profiling_km != null ? `${drilling.geophysical_logging.resistivity_profiling_km} line km | ${drilling?.geophysical_logging?.vertical_soundings_count || 'N/A'} soundings` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: COAL RESOURCE ANALYTICS */}
      {activeTab === 'resources' && (
        <div className="analytics-tab-content">
          <div className="analytics-section-title">
            <Database size={18} className="text-indigo" />
            Coal Resource Classifications & Geological Seam Reserves
          </div>

          <div className="analytics-two-col-grid">
            {/* Macro Resource Classifications */}
            <div className="analytics-card-panel">
              <div className="panel-header">
                <h4 className="panel-heading">Regional Coal Resource Estimates</h4>
                <span className="badge badge-indigo">CMPDI New GRs</span>
              </div>
              <div className="resource-category-list">
                {resources?.resource_categories?.map((c, idx) => (
                  <div className="resource-cat-card" key={idx}>
                    <div className="resource-cat-left">
                      <span className="cat-title">{c.category}</span>
                      <span className="cat-meta">Period: {c.fiscal_period || '2006-07'}</span>
                    </div>
                    <div className="resource-cat-right">
                      <span className="cat-value">{c.value}</span>
                      <span className="cat-unit">{c.unit}</span>
                      {c.provenance && (
                        <button
                          className="view-ev-btn"
                          onClick={() => openProvenance(c.category, c.provenance)}
                        >
                          Page {c.provenance.source_page}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Seam-by-Seam Reserves */}
            <div className="analytics-card-panel">
              <div className="panel-header">
                <h4 className="panel-heading">Stratigraphic Seam Reserves</h4>
                <span className="badge badge-subtle">{resources?.seam_reserves?.length || 0} Seams Logged</span>
              </div>
              {resources?.seam_reserves && resources.seam_reserves.length > 0 ? (
                <div className="seam-reserve-table-container">
                  <table className="analytics-table compact">
                    <thead>
                      <tr>
                        <th>Seam</th>
                        <th>Category</th>
                        <th>Gross MT</th>
                        <th>Extractable MT</th>
                        <th>Recovery %</th>
                        <th>Audit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {resources.seam_reserves.map((s, idx) => (
                        <tr key={idx}>
                          <td className="font-semibold text-primary">{s.seam_id}</td>
                          <td><span className="badge badge-subtle">{s.category || 'Proved'}</span></td>
                          <td>{s.gross_reserves_mt !== null ? s.gross_reserves_mt : 'N/A'}</td>
                          <td className="text-emerald font-semibold">{s.extractable_reserves_mt !== null ? s.extractable_reserves_mt : 'N/A'}</td>
                          <td>
                            {s.recovery_factor_pct !== null ? (
                              <span className="status-pill status-pill-green">{s.recovery_factor_pct}%</span>
                            ) : (
                              <span className="text-muted">N/A</span>
                            )}
                          </td>
                          <td>
                            {s.provenance && (
                              <button
                                className="view-ev-btn"
                                onClick={() => openProvenance(`Seam ${s.seam_id}`, s.provenance)}
                              >
                                Page {s.provenance.source_page}
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="analytics-empty-box">
                  <Info size={18} className="empty-icon text-muted" />
                  <p>No borehole seam reserve tables found for <strong>{selectedDoc}</strong>.</p>
                  <span className="text-xs text-muted">
                    Macro resource figures (1.78 Bt) are displayed from the geological summary metrics. Seam reserve tables are available in borehole spreadsheets.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: MINES & PROJECTS ANALYTICS */}
      {activeTab === 'projects' && (
        <div className="analytics-tab-content">
          <div className="analytics-filter-toolbar">
            <div className="filter-group">
              <label className="filter-label">Filter Subsidiary:</label>
              <select
                className="analytics-select"
                value={projectSubFilter}
                onChange={(e) => setProjectSubFilter(e.target.value)}
              >
                <option value="all">All Subsidiaries</option>
                {projectsData?.available_subsidiaries?.map((sub) => (
                  <option key={sub} value={sub}>{sub}</option>
                ))}
              </select>
            </div>

            <div className="search-group">
              <Search size={14} className="text-muted" />
              <input
                type="text"
                className="analytics-input"
                placeholder="Search project name, block, or basin..."
                value={projectSearch}
                onChange={(e) => setProjectSearch(e.target.value)}
              />
            </div>

            <span className="filter-results-badge">
              {projectsData?.total_projects || 0} projects found
            </span>
          </div>

          <div className="analytics-table-card">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Project Name</th>
                  <th>Subsidiary</th>
                  <th>Location / Basin</th>
                  <th>Block Name</th>
                  <th>Target Production</th>
                  <th>Stripping Ratio</th>
                  <th>Life (Yrs)</th>
                  <th>Source Page</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {projectsData?.projects?.map((p) => (
                  <tr key={p.id}>
                    <td className="font-semibold text-primary">{p.project_name}</td>
                    <td><span className="badge badge-warning" title={p.subsidiary || 'CIL'}>{formatSubsidiaryLabel(p.subsidiary || 'CIL')}</span></td>
                    <td>{p.location || '—'}</td>
                    <td>{p.block_name || '—'}</td>
                    <td>{p.target_production !== null ? `${p.target_production} ${p.target_production_unit || 'MTPA'}` : '—'}</td>
                    <td>{p.stripping_ratio !== null ? `${p.stripping_ratio}:1` : '—'}</td>
                    <td>{p.life_of_mine_years !== null ? `${p.life_of_mine_years} yrs` : '—'}</td>
                    <td><span className="page-pill">p. {p.source_page}</span></td>
                    <td>
                      <button
                        className="view-ev-btn"
                        onClick={() => openProvenance(p.project_name, { source_document: p.source_document, source_page: p.source_page, evidence_text: p.evidence_text })}
                      >
                        View Evidence
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: COAL QUALITY (PROXIMATE ANALYSIS) */}
      {activeTab === 'quality' && (
        <div className="analytics-tab-content">
          <div className="analytics-section-title">
            <Flame size={18} className="text-amber" />
            Laboratory Proximate Analysis & Coal Quality Parameters
          </div>

          {qualityData && qualityData.has_data ? (
            <div>
              {/* Quality Averages Cards */}
              <div className="quality-averages-grid">
                <div className="quality-stat-card">
                  <span className="q-label">Avg Moisture</span>
                  <span className="q-val">{qualityData.averages?.avg_moisture_pct !== null ? `${qualityData.averages.avg_moisture_pct}%` : 'N/A'}</span>
                  <span className="q-sub">In-situ core samples</span>
                </div>
                <div className="quality-stat-card">
                  <span className="q-label">Avg Ash Content</span>
                  <span className="q-val text-amber">{qualityData.averages?.avg_ash_pct !== null ? `${qualityData.averages.avg_ash_pct}%` : 'N/A'}</span>
                  <span className="q-sub">Standard proximate run</span>
                </div>
                <div className="quality-stat-card">
                  <span className="q-label">Avg Volatile Matter</span>
                  <span className="q-val">{qualityData.averages?.avg_volatile_matter_pct !== null ? `${qualityData.averages.avg_volatile_matter_pct}%` : 'N/A'}</span>
                  <span className="q-sub">Dry mineral-matter free</span>
                </div>
                <div className="quality-stat-card">
                  <span className="q-label">Avg Fixed Carbon</span>
                  <span className="q-val">{qualityData.averages?.avg_fixed_carbon_pct !== null ? `${qualityData.averages.avg_fixed_carbon_pct}%` : 'N/A'}</span>
                  <span className="q-sub">Combustion base</span>
                </div>
                <div className="quality-stat-card">
                  <span className="q-label">Gross Calorific Value</span>
                  <span className="q-val text-emerald">{qualityData.averages?.avg_gcv !== null ? `${qualityData.averages.avg_gcv} kcal/kg` : 'N/A'}</span>
                  <span className="q-sub">Bomb calorimeter grade</span>
                </div>
              </div>

              {/* Table of laboratory records */}
              <div className="analytics-table-card" style={{ marginTop: 20 }}>
                <table className="analytics-table">
                  <thead>
                    <tr>
                      <th>Seam ID</th>
                      <th>Borehole ID</th>
                      <th>Moisture %</th>
                      <th>Ash %</th>
                      <th>Volatile Matter %</th>
                      <th>Fixed Carbon %</th>
                      <th>GCV (kcal/kg)</th>
                      <th>Source Document</th>
                      <th>Page</th>
                      <th>Audit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {qualityData.records.map((r) => (
                      <tr key={r.id}>
                        <td className="font-semibold text-primary">{r.seam_id || 'Seam Sample'}</td>
                        <td><span className="badge badge-cyan">{r.borehole_id || 'Core Hole'}</span></td>
                        <td>{r.moisture_percent !== null ? `${r.moisture_percent}%` : '—'}</td>
                        <td className="text-amber font-semibold">{r.ash_percent !== null ? `${r.ash_percent}%` : '—'}</td>
                        <td>{r.volatile_matter_percent !== null ? `${r.volatile_matter_percent}%` : '—'}</td>
                        <td>{r.fixed_carbon_percent !== null ? `${r.fixed_carbon_percent}%` : '—'}</td>
                        <td className="text-emerald font-semibold">{r.gross_calorific_value !== null ? `${r.gross_calorific_value}` : '—'}</td>
                        <td><span className="doc-pill">{r.source_document}</span></td>
                        <td><span className="page-pill">p. {r.source_page}</span></td>
                        <td>
                          <button
                            className="view-ev-btn"
                            onClick={() => openProvenance(`Proximate Sample ${r.seam_id || ''}`, { source_document: r.source_document, source_page: r.source_page, evidence_text: r.evidence_text })}
                          >
                            View Evidence
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="empty-quality-card">
              <AlertCircle size={36} className="empty-quality-icon text-amber" />
              <h3 className="empty-quality-title">No Proximate Analysis Laboratory Records in Scope</h3>
              <p className="empty-quality-desc">
                {qualityData?.empty_state_reason || `The selected document '${selectedDoc}' does not contain laboratory proximate analysis core assay data.`}
              </p>
              <div className="empty-quality-actions">
                <button
                  className="action-button button-secondary"
                  onClick={() => setSelectedDoc('all')}
                >
                  Switch to Cumulative Scope (All Documents)
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 6: GEOLOGICAL METRICS EXPLORER */}
      {activeTab === 'explorer' && (
        <div className="analytics-tab-content">
          <div className="analytics-filter-toolbar">
            <div className="filter-group">
              <label className="filter-label">Category:</label>
              <select
                className="analytics-select"
                value={metricCatFilter}
                onChange={(e) => setMetricCatFilter(e.target.value)}
              >
                <option value="all">All Categories</option>
                {metricsData?.categories?.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Unit:</label>
              <select
                className="analytics-select"
                value={metricUnitFilter}
                onChange={(e) => setMetricUnitFilter(e.target.value)}
              >
                <option value="all">All Units</option>
                {metricsData?.units?.map((u) => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
            </div>

            <div className="search-group">
              <Search size={14} className="text-muted" />
              <input
                type="text"
                className="analytics-input"
                placeholder="Search metrics or evidence..."
                value={metricSearch}
                onChange={(e) => setMetricSearch(e.target.value)}
              />
            </div>

            <span className="filter-results-badge">
              {metricsData?.total || 0} metrics matched
            </span>
          </div>

          <div className="analytics-table-card">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Metric Name</th>
                  <th>Value</th>
                  <th>Unit</th>
                  <th>Period</th>
                  <th>Category</th>
                  <th>Source Document</th>
                  <th>Page</th>
                  <th>Audit Provenance</th>
                </tr>
              </thead>
              <tbody>
                {metricsData?.metrics?.map((m) => (
                  <tr key={m.id}>
                    <td className="font-semibold text-primary">{m.metric_name}</td>
                    <td className="font-mono text-emerald font-semibold">
                      {m.metric_value !== null ? m.metric_value.toLocaleString() : 'N/A'}
                    </td>
                    <td><span className="unit-pill">{m.unit || 'unitless'}</span></td>
                    <td>{m.year_period || '—'}</td>
                    <td><span className="badge badge-subtle">{m.category || 'Uncategorized'}</span></td>
                    <td><span className="doc-pill">{m.source_document}</span></td>
                    <td><span className="page-pill">p. {m.source_page}</span></td>
                    <td>
                      <button
                        className="view-ev-btn"
                        onClick={() => openProvenance(m.metric_name, { source_document: m.source_document, source_page: m.source_page, evidence_text: m.evidence_text })}
                      >
                        View Evidence
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 7: CROSS-DOCUMENT COMPARISON */}
      {activeTab === 'cross_doc' && (
        <div className="analytics-tab-content">
          <div className="analytics-section-title">
            <Layers size={18} className="text-cyan" />
            Cross-Document Analytical Comparison & Unit Integrity
          </div>

          {/* Unit Segregation Alert */}
          <div className="analytics-info-banner">
            <Info size={18} className="info-banner-icon text-cyan" />
            <div className="info-banner-text">
              <strong>Strict Physical Unit Preservation:</strong> {comparisonData?.incompatible_metrics_note || 'Disparate units are preserved in their native physical units without mathematical conflation.'}
            </div>
          </div>

          {/* Document Entities Matrix */}
          <div className="analytics-table-card" style={{ marginTop: 16 }}>
            <div className="table-card-header">
              <h4 className="table-heading">Structured Entity Distribution by Indexed Document</h4>
              <span className="badge badge-cyan">{comparisonData?.entity_breakdown?.length || 0} Documents</span>
            </div>
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Document Name</th>
                  <th>Mines / Projects</th>
                  <th>Boreholes</th>
                  <th>Coal Seams</th>
                  <th>Proximate Lab</th>
                  <th>Geological Metrics</th>
                  <th>Total Entities</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData?.entity_breakdown?.map((docItem, idx) => (
                  <tr key={idx}>
                    <td className="font-semibold text-primary">{docItem.document}</td>
                    <td>{docItem.mines_projects}</td>
                    <td>{docItem.boreholes}</td>
                    <td>{docItem.coal_seams}</td>
                    <td>{docItem.proximate_analyses}</td>
                    <td>{docItem.geological_metrics}</td>
                    <td className="text-emerald font-semibold">{docItem.total_entities}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Compatible Metrics Side-by-Side Table */}
          <div className="analytics-table-card" style={{ marginTop: 20 }}>
            <div className="table-card-header">
              <h4 className="table-heading">Compatible Metric Matrix Across Documents</h4>
              <span className="badge badge-subtle">{comparisonData?.compatible_metrics?.length || 0} Comparable Metrics</span>
            </div>
            <div className="matrix-scroll-container">
              <table className="analytics-table compact">
                <thead>
                  <tr>
                    <th>Metric Name</th>
                    <th>Unit</th>
                    <th>Category</th>
                    {comparisonData?.compared_documents?.map((doc) => (
                      <th key={doc} className="doc-col-header">{doc}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {comparisonData?.compatible_metrics?.slice(0, 30).map((cm, idx) => (
                    <tr key={idx}>
                      <td className="font-semibold text-primary">{cm.metric_name}</td>
                      <td><span className="unit-pill">{cm.unit}</span></td>
                      <td><span className="badge badge-subtle">{cm.category || 'General'}</span></td>
                      {comparisonData?.compared_documents?.map((doc) => {
                        const val = cm.values_by_document[doc];
                        const prov = cm.provenance_by_document[doc];
                        return (
                          <td key={doc} className="doc-val-cell">
                            {val !== undefined && val !== null ? (
                              <span
                                className="matrix-val clickable"
                                title={`Page ${prov?.source_page}: ${prov?.evidence_text}`}
                                onClick={() => openProvenance(cm.metric_name, prov)}
                              >
                                {val.toLocaleString()}
                              </span>
                            ) : (
                              <span className="text-muted">—</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* PROVENANCE MODAL / DRAWER */}
      {provenanceModal && (
        <div className="prov-modal-overlay" onClick={() => setProvenanceModal(null)}>
          <div className="prov-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="prov-modal-header">
              <div className="prov-modal-title-group">
                <CheckCircle2 size={18} className="text-emerald" />
                <h3 className="prov-modal-title">Audit Provenance & Citation</h3>
              </div>
              <button
                className="prov-modal-close"
                onClick={() => setProvenanceModal(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="prov-modal-body">
              <div className="prov-metric-badge">
                <span className="prov-badge-label">METRIC / FIELD:</span>
                <span className="prov-badge-val">{provenanceModal.title}</span>
              </div>

              <div className="prov-meta-grid">
                <div className="prov-meta-item">
                  <span className="prov-meta-key">Source Document:</span>
                  <span className="prov-meta-val">{provenanceModal.source_document}</span>
                </div>
                <div className="prov-meta-item">
                  <span className="prov-meta-key">Verified Physical Page:</span>
                  <span className="prov-meta-val font-semibold text-amber">
                    Page {provenanceModal.source_page}
                  </span>
                </div>
              </div>

              <div className="prov-evidence-box">
                <span className="prov-evidence-title">VERBATIM DOCUMENT EVIDENCE:</span>
                <blockquote className="prov-evidence-text">
                  "{provenanceModal.evidence_text}"
                </blockquote>
              </div>
            </div>

            <div className="prov-modal-footer">
              <span className="prov-footer-status text-emerald" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Check size={14} aria-hidden="true" />
                <span>Verified in SQLite extraction store (extraction.db)</span>
              </span>
              <button
                className="action-button button-secondary"
                onClick={() => setProvenanceModal(null)}
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
