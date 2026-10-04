/**
 * Frontend API Service Layer
 * Connects React Vite UI to the FastAPI backend.
 * SIH 2026 - Problem Statement 26023 (CMPDI / Coal India Limited)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  /**
   * Generic JSON request wrapper with timeout and standard error formatting
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || 15000);

    const startTime = performance.now();
    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      const latencyMs = Math.round(performance.now() - startTime);

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText };
        }
        return {
          success: false,
          status: response.status,
          error: errorData.detail || 'API request failed',
          latencyMs,
        };
      }

      const data = await response.json();
      return {
        success: true,
        status: response.status,
        data,
        latencyMs,
      };
    } catch (err) {
      const latencyMs = Math.round(performance.now() - startTime);
      return {
        success: false,
        status: 0,
        error: err.name === 'AbortError' ? 'Request timed out' : (err.message || 'Network error'),
        latencyMs,
      };
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Check backend health and modular subsystem readiness
   */
  async checkHealth() {
    return this.request('/api/health');
  }

  /**
   * Get root platform info
   */
  async getRootInfo() {
    return this.request('/');
  }

  /**
   * Upload and multi-modal parse a geological / mining document
   * Accepts: PDF, DOCX, XLSX, PNG, TIFF, JPG
   */
  async uploadDocument(file) {
    const url = `${this.baseUrl}/api/documents/upload`;
    const formData = new FormData();
    formData.append('file', file);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s for large scans
    const startTime = performance.now();

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      const latencyMs = Math.round(performance.now() - startTime);

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText };
        }
        return {
          success: false,
          status: response.status,
          error: errorData.detail || 'Upload failed',
          latencyMs,
        };
      }

      const data = await response.json();
      return {
        success: true,
        status: response.status,
        data,
        latencyMs,
      };
    } catch (err) {
      const latencyMs = Math.round(performance.now() - startTime);
      return {
        success: false,
        status: 0,
        error: err.name === 'AbortError' ? 'Upload timed out' : (err.message || 'Network error during upload'),
        latencyMs,
      };
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * List all ingested documents
   */
  async listDocuments() {
    return this.request('/api/documents');
  }

  /**
   * Get document metadata and storage info
   */
  async getDocument(documentId) {
    return this.request(`/api/documents/${documentId}`);
  }

  /**
   * Get page-level details (text blocks, coordinates, tables)
   */
  async getDocumentPages(documentId) {
    return this.request(`/api/documents/${documentId}/pages`);
  }

  /**
   * Get RAG knowledge base & vector store telemetry
   */
  async getRagStatus() {
    return this.request('/api/rag/status');
  }

  /**
   * Query the knowledge base with grounded citations
   */
  async queryRAG(query, topK = 5, documentIds = null) {
    const payload = {
      query,
      top_k: topK,
    };
    if (documentIds && documentIds.length > 0) {
      payload.document_ids = documentIds;
    }
    return this.request('/api/rag/query', {
      method: 'POST',
      body: JSON.stringify(payload),
      timeout: 30000,
    });
  }

  /**
   * Index a single processed document into FAISS
   */
  async indexDocument(documentId) {
    return this.request(`/api/rag/index/${documentId}`, {
      method: 'POST',
      timeout: 60000,
    });
  }

  /**
   * Index all unindexed processed documents into FAISS
   */
  async indexAllDocuments() {
    return this.request('/api/rag/index-all', {
      method: 'POST',
      timeout: 120000,
    });
  }

  // --- Phase 4: Structured Mining Extraction APIs ---

  /**
   * Get structured extraction telemetry and counts
   */
  async getExtractionStatus() {
    return this.request('/api/extraction/status');
  }

  /**
   * Extract structured mining data from a single document
   */
  async extractDocument(documentId) {
    return this.request(`/api/extraction/document/${documentId}`, {
      method: 'POST',
      timeout: 60000,
    });
  }

  /**
   * Batch extract structured mining data across all documents
   */
  async extractAllDocuments() {
    return this.request('/api/extraction/all', {
      method: 'POST',
      timeout: 180000,
    });
  }

  /**
   * Get extracted borehole records
   */
  async getBoreholes(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/extraction/boreholes${qs ? `?${qs}` : ''}`);
  }

  /**
   * Get extracted coal seam records
   */
  async getSeams(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/extraction/seams${qs ? `?${qs}` : ''}`);
  }

  /**
   * Get extracted proximate analysis records
   */
  async getProximateAnalyses(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/extraction/proximate-analysis${qs ? `?${qs}` : ''}`);
  }

  /**
   * Get extracted mine and project records
   */
  async getMines(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/extraction/mines${qs ? `?${qs}` : ''}`);
  }

  /**
   * Get extracted geological and exploration metrics
   */
  async getMetrics(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/extraction/metrics${qs ? `?${qs}` : ''}`);
  }

  // --- Phase 5: Automated Geological Reporting APIs ---

  async getReportsStatus() {
    return this.request('/api/reports/status');
  }

  async getReportTypes() {
    return this.request('/api/reports/types');
  }

  async generateReport(payload) {
    return this.request('/api/reports/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
      timeout: 60000,
    });
  }

  async generateGeologicalSummary(payload) {
    return this.request('/api/reports/geological-summary', {
      method: 'POST',
      body: JSON.stringify({ ...payload, report_type: 'cmpdi_geological_summary' }),
      timeout: 60000,
    });
  }

  async generateReserveReconciliation(payload) {
    return this.request('/api/reports/reserve-reconciliation', {
      method: 'POST',
      body: JSON.stringify({ ...payload, report_type: 'reserve_reconciliation_memo' }),
      timeout: 60000,
    });
  }

  /**
   * Download a generated report as PDF, Excel, or Markdown.
   * Returns a Blob rather than JSON so the browser can save the file.
   */
  async exportReport(format, payload) {
    const url = `${this.baseUrl}/api/reports/export/${format}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 90000);
    const startTime = performance.now();

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      const latencyMs = Math.round(performance.now() - startTime);

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText };
        }
        return {
          success: false,
          status: response.status,
          error: errorData.detail || 'Export failed',
          latencyMs,
        };
      }

      const blob = await response.blob();
      const disposition = response.headers.get('content-disposition') || '';
      const match = disposition.match(/filename="?([^"]+)"?/i);
      const filename = match ? match[1] : `cmpdi_report.${format === 'excel' ? 'xlsx' : format === 'markdown' ? 'md' : 'pdf'}`;

      return {
        success: true,
        status: response.status,
        blob,
        filename,
        latencyMs,
      };
    } catch (err) {
      const latencyMs = Math.round(performance.now() - startTime);
      return {
        success: false,
        status: 0,
        error: err.name === 'AbortError' ? 'Export timed out' : (err.message || 'Network error during export'),
        latencyMs,
      };
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // ==========================================
  // Phase 6: Mining Analytics & Visualizations
  // ==========================================

  async getAnalyticsSummary(params = {}) {
    const query = new URLSearchParams();
    if (params.document_id) query.append('document_id', params.document_id);
    if (params.source_document) query.append('source_document', params.source_document);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/summary${qs}`);
  }

  async getDrillingAnalytics(params = {}) {
    const query = new URLSearchParams();
    if (params.document_id) query.append('document_id', params.document_id);
    if (params.source_document) query.append('source_document', params.source_document);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/drilling${qs}`);
  }

  async getResourceAnalytics(params = {}) {
    const query = new URLSearchParams();
    if (params.document_id) query.append('document_id', params.document_id);
    if (params.source_document) query.append('source_document', params.source_document);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/resources${qs}`);
  }

  async getProjectAnalytics(params = {}) {
    const query = new URLSearchParams();
    if (params.document_id) query.append('document_id', params.document_id);
    if (params.source_document) query.append('source_document', params.source_document);
    if (params.subsidiary) query.append('subsidiary', params.subsidiary);
    if (params.location) query.append('location', params.location);
    if (params.search) query.append('search', params.search);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/projects${qs}`);
  }

  async getCoalQualityAnalytics(params = {}) {
    const query = new URLSearchParams();
    if (params.document_id) query.append('document_id', params.document_id);
    if (params.source_document) query.append('source_document', params.source_document);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/quality${qs}`);
  }

  async getGeologicalMetricsExplorer(params = {}) {
    const query = new URLSearchParams();
    if (params.document_id) query.append('document_id', params.document_id);
    if (params.source_document) query.append('source_document', params.source_document);
    if (params.category) query.append('category', params.category);
    if (params.unit) query.append('unit', params.unit);
    if (params.search) query.append('search', params.search);
    if (params.limit !== undefined) query.append('limit', params.limit);
    if (params.offset !== undefined) query.append('offset', params.offset);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/metrics${qs}`);
  }

  async getCrossDocumentComparison(params = {}) {
    const query = new URLSearchParams();
    if (params.documents) query.append('documents', params.documents);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/analytics/comparison${qs}`);
  }

  /**
   * Get Topic Intelligence summary — all docs or scoped to one document
   */
  async getTopicSummary(params = {}) {
    const query = new URLSearchParams();
    if (params.document_id) query.append('document_id', params.document_id);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/topics/summary${qs}`);
  }

  /**
   * Get word cloud data — all docs or scoped to one document
   */
  async getTopicWordCloud(params = {}) {
    const query = new URLSearchParams();
    if (params.document_id) query.append('document_id', params.document_id);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/api/topics/word-cloud${qs}`);
  }

  /**
   * Get topic intelligence for a specific document
   */
  async getDocumentTopics(documentId) {
    return this.request(`/api/topics/documents/${documentId}`);
  }

  /**
   * Benchmark & Validation Endpoints
   */
  async getBenchmarkSummary() {
    return this.request('/api/benchmarks/summary');
  }

  async submitManualBaseline(data) {
    return this.request('/api/benchmarks/time-reduction', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getExtractionAccuracy() {
    return this.request('/api/benchmarks/accuracy');
  }

  async getAutomationCoverage() {
    return this.request('/api/benchmarks/automation');
  }

  getBenchmarkExportUrl(format = 'markdown') {
    return `${this.baseUrl}/api/benchmarks/export?format=${encodeURIComponent(format)}`;
  }
}

export const api = new ApiService(API_BASE_URL);
export default api;

