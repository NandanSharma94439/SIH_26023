import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  FileText,
  FileSpreadsheet,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Info,
  Clock,
  Layers,
  ChevronLeft,
  ChevronRight,
  Table as TableIcon,
  Cpu,
  RefreshCw,
  Search,
  ScanLine,
  FileCode2,
} from 'lucide-react';
import api from '../services/api';

const FILE_TYPE_ICONS = {
  pdf: FileText,
  docx: FileCode2,
  xlsx: FileSpreadsheet,
  png: ImageIcon,
  jpg: ImageIcon,
  tiff: ImageIcon,
};

export default function DocumentManager({ onDocumentIngested }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [selectedDocDetails, setSelectedDocDetails] = useState(null);
  const [selectedDocPages, setSelectedDocPages] = useState([]);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [activeViewTab, setActiveViewTab] = useState('text'); // 'text', 'tables', 'blocks'

  const [loadingDocs, setLoadingDocs] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { type: 'success' | 'error', message: '' }
  const [isDragOver, setIsDragOver] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');

  const fileInputRef = useRef(null);

  // Fetch document list
  const fetchDocuments = async () => {
    setLoadingDocs(true);
    const res = await api.listDocuments();
    if (res.success && Array.isArray(res.data)) {
      setDocuments(res.data);
      if (res.data.length > 0 && !selectedDocId) {
        selectDocument(res.data[0].id);
      }
    }
    setLoadingDocs(false);
  };

  // Select and load document details + pages
  const selectDocument = async (docId) => {
    setSelectedDocId(docId);
    setCurrentPageIndex(0);

    const [detailRes, pagesRes] = await Promise.all([
      api.getDocument(docId),
      api.getDocumentPages(docId),
    ]);

    if (detailRes.success) {
      setSelectedDocDetails(detailRes.data);
    }
    if (pagesRes.success && pagesRes.data?.pages) {
      setSelectedDocPages(pagesRes.data.pages);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  // Handle file upload
  const handleFileUpload = async (file) => {
    if (!file) return;

    setUploading(true);
    setUploadStatus(null);

    const res = await api.uploadDocument(file);
    setUploading(false);

    if (res.success && res.data?.document) {
      if (res.data.already_exists) {
        setUploadStatus({
          type: 'info',
          message: `Document '${file.name}' already exists in repository (${res.data.document.filename}). Reusing existing record without reprocessing.`,
        });
      } else {
        setUploadStatus({
          type: 'success',
          message: `Successfully ingested '${file.name}' (${res.data.document.total_pages} pages parsed in ${res.data.document.processing_time_ms}ms).`,
        });
      }
      await fetchDocuments();
      selectDocument(res.data.document.id);
      if (onDocumentIngested) onDocumentIngested();
    } else {
      setUploadStatus({
        type: 'error',
        message: res.error || 'Document ingestion failed.',
      });
    }
  };

  // Drag and drop handlers
  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const onDragLeave = () => {
    setIsDragOver(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  // Filtered document list
  const filteredDocs = documents.filter((d) =>
    d.filename.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const currentPage = selectedDocPages[currentPageIndex] || null;

  return (
    <div className="doc-manager-container">
      {/* Upload Dropzone */}
      <div
        className={`dropzone glass-panel ${isDragOver ? 'drag-over' : ''} ${
          uploading ? 'uploading' : ''
        }`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg,.tiff,.tif"
          onChange={(e) => {
            if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
          }}
          disabled={uploading}
        />

        <div className="dropzone-content">
          <div className="dropzone-icon-wrap">
            <Upload size={24} className={uploading ? 'spinning' : ''} />
          </div>
          <div className="dropzone-text">
            <h3 className="dropzone-title">
              {uploading
                ? 'Processing & Multi-Modal Parsing...'
                : 'Upload Mining & Geological Documents'}
            </h3>
            <p className="dropzone-subtitle">
              Drag and drop Geological Reports (GRs), borehole lithology sheets, or maps.
              Supported: <strong>PDF, DOCX, XLSX, TIFF, PNG, JPG</strong> (Max 50MB)
            </p>
          </div>
          <button
            type="button"
            className="browse-btn"
            disabled={uploading}
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            {uploading ? 'Parsing...' : 'Select File'}
          </button>
        </div>

        {uploading && (
          <div className="upload-progress-bar-container">
            <div className="upload-progress-bar-indeterminate" />
          </div>
        )}
      </div>

      {/* Upload Notification Message */}
      {uploadStatus && (
        <div
          className={`upload-alert ${
            uploadStatus.type === 'success'
              ? 'alert-success'
              : uploadStatus.type === 'info'
              ? 'alert-info'
              : 'alert-error'
          }`}
        >
          {uploadStatus.type === 'success' ? (
            <CheckCircle2 size={18} />
          ) : uploadStatus.type === 'info' ? (
            <Info size={18} />
          ) : (
            <AlertCircle size={18} />
          )}
          <span>{uploadStatus.message}</span>
        </div>
      )}

      {/* Main Document Interface: Left List + Right Inspector */}
      <div className="doc-workspace-grid">
        {/* Left Column: Ingested Documents List */}
        <div className="doc-sidebar-panel glass-panel">
          <div className="panel-header">
            <div className="panel-title-row">
              <h3 className="panel-title">Ingested Repository</h3>
              <span className="badge badge-cyan">{documents.length} Files</span>
            </div>
            <div className="panel-search-row">
              <div className="search-input-wrapper">
                <Search size={14} className="search-icon" />
                <input
                  type="text"
                  placeholder="Filter documents..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="search-input"
                />
              </div>
              <button
                className="icon-refresh-btn"
                onClick={fetchDocuments}
                title="Refresh document registry"
              >
                <RefreshCw size={13} className={loadingDocs ? 'spinning' : ''} />
              </button>
            </div>
          </div>

          <div className="doc-list">
            {filteredDocs.length === 0 ? (
              <div className="doc-list-empty">
                {documents.length === 0 ? (
                  <span>No documents uploaded yet. Use the upload zone above.</span>
                ) : (
                  <span>No documents match '{searchFilter}'</span>
                )}
              </div>
            ) : (
              filteredDocs.map((doc) => {
                const IconComponent = FILE_TYPE_ICONS[doc.file_type] || FileText;
                const isSelected = doc.id === selectedDocId;
                return (
                  <div
                    key={doc.id}
                    className={`doc-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => selectDocument(doc.id)}
                  >
                    <div className="doc-card-icon-wrap">
                      <IconComponent size={18} />
                    </div>
                    <div className="doc-card-content">
                      <span className="doc-card-name" title={doc.filename}>
                        {doc.filename}
                      </span>
                      <div className="doc-card-badges">
                        <span className="badge badge-subtle">
                          {doc.file_type.toUpperCase()}
                        </span>
                        <span className="badge badge-subtle">
                          {doc.total_pages} {doc.total_pages === 1 ? 'Page' : 'Pages'}
                        </span>
                        {doc.has_tables && (
                          <span className="badge badge-warning" title="Contains extracted tables">
                            Tables
                          </span>
                        )}
                        {doc.ocr_pages_count > 0 && (
                          <span className="badge badge-success" title="OCR Applied">
                            OCR
                          </span>
                        )}
                      </div>
                      <span className="doc-card-meta">
                        {(doc.file_size_bytes / 1024).toFixed(1)} KB &bull;{' '}
                        {new Date(doc.uploaded_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Multi-modal Page & Structure Inspector */}
        <div className="doc-inspector-panel glass-panel">
          {selectedDocDetails ? (
            <>
              {/* Document Overview Header */}
              <div className="inspector-header">
                <div className="inspector-title-block">
                  <div className="doc-title-row">
                    <h2 className="inspector-doc-name">
                      {selectedDocDetails.metadata.filename}
                    </h2>
                    <span className="badge badge-success">
                      {selectedDocDetails.metadata.status}
                    </span>
                  </div>
                  <span className="inspector-meta-row">
                    ID: <code>{selectedDocDetails.metadata.id}</code> &bull; Parsed in{' '}
                    <strong>{selectedDocDetails.metadata.processing_time_ms} ms</strong> &bull;{' '}
                    Format: {selectedDocDetails.metadata.file_type.toUpperCase()}
                  </span>
                </div>

                {/* Subsystem & View Tabs */}
                <div className="inspector-tabs">
                  <button
                    className={`tab-btn ${activeViewTab === 'text' ? 'active' : ''}`}
                    onClick={() => setActiveViewTab('text')}
                  >
                    <FileText size={15} />
                    <span>Extracted Text</span>
                  </button>
                  <button
                    className={`tab-btn ${activeViewTab === 'tables' ? 'active' : ''}`}
                    onClick={() => setActiveViewTab('tables')}
                  >
                    <TableIcon size={15} />
                    <span>
                      Tables (
                      {selectedDocPages.reduce((acc, p) => acc + (p.tables?.length || 0), 0)})
                    </span>
                  </button>
                  <button
                    className={`tab-btn ${activeViewTab === 'blocks' ? 'active' : ''}`}
                    onClick={() => setActiveViewTab('blocks')}
                  >
                    <Layers size={15} />
                    <span>Blocks & Coords</span>
                  </button>
                </div>
              </div>

              {/* Page Navigator */}
              {selectedDocPages.length > 0 && (
                <div className="page-navigator">
                  <div className="nav-controls">
                    <button
                      className="page-nav-btn"
                      disabled={currentPageIndex <= 0}
                      onClick={() => setCurrentPageIndex((prev) => Math.max(0, prev - 1))}
                    >
                      <ChevronLeft size={16} />
                    </button>

                    <span className="page-indicator">
                      Page{' '}
                      <select
                        value={currentPageIndex}
                        onChange={(e) => setCurrentPageIndex(Number(e.target.value))}
                        className="page-select"
                      >
                        {selectedDocPages.map((p, idx) => (
                          <option key={p.page_number} value={idx}>
                            {p.page_number}
                          </option>
                        ))}
                      </select>{' '}
                      of {selectedDocPages.length}
                    </span>

                    <button
                      className="page-nav-btn"
                      disabled={currentPageIndex >= selectedDocPages.length - 1}
                      onClick={() =>
                        setCurrentPageIndex((prev) =>
                          Math.min(selectedDocPages.length - 1, prev + 1)
                        )
                      }
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>

                  {currentPage && (
                    <div className="page-meta-badges">
                      <span className="badge badge-subtle">
                        {currentPage.word_count} words
                      </span>
                      <span className="badge badge-subtle">
                        {currentPage.char_count} chars
                      </span>
                      {currentPage.dimensions?.width && (
                        <span className="badge badge-subtle">
                          {currentPage.dimensions.width} &times; {currentPage.dimensions.height} pt
                        </span>
                      )}
                      {currentPage.ocr_applied ? (
                        <span className="badge badge-success">
                          OCR Applied {currentPage.ocr_confidence ? `(${currentPage.ocr_confidence}%)` : ''}
                        </span>
                      ) : (
                        <span className="badge badge-cyan">Native PyMuPDF</span>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* OCR Fallback Diagnostics Banner if OCR was attempted or needed */}
              {currentPage?.ocr_error && (
                <div className="ocr-diagnostic-banner">
                  <ScanLine size={16} className="diagnostic-icon" />
                  <div className="diagnostic-text">
                    <strong>OCR Engine Diagnostic:</strong> {currentPage.ocr_error}
                  </div>
                </div>
              )}

              {/* Main Page View Area */}
              <div className="inspector-content-area">
                {activeViewTab === 'text' && (
                  <div className="text-viewer">
                    {currentPage?.text ? (
                      <pre className="extracted-preformatted-text">{currentPage.text}</pre>
                    ) : (
                      <div className="empty-content">No text extracted on this page.</div>
                    )}
                  </div>
                )}

                {activeViewTab === 'tables' && (
                  <div className="tables-viewer">
                    {currentPage?.tables && currentPage.tables.length > 0 ? (
                      currentPage.tables.map((t, tIdx) => (
                        <div key={tIdx} className="table-block">
                          <div className="table-title">
                            <TableIcon size={14} />
                            <span>
                              Table {t.table_index} ({t.num_rows} rows &bull; {t.num_cols} columns)
                            </span>
                          </div>
                          <div className="table-responsive-wrapper">
                            <table className="extracted-table">
                              {t.headers && (
                                <thead>
                                  <tr>
                                    {t.headers.map((h, hIdx) => (
                                      <th key={hIdx}>{h || `Col ${hIdx + 1}`}</th>
                                    ))}
                                  </tr>
                                </thead>
                              )}
                              <tbody>
                                {t.rows.map((row, rIdx) => (
                                  <tr key={rIdx}>
                                    {row.map((cell, cIdx) => (
                                      <td key={cIdx}>{cell}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="empty-content">
                        No structured tables detected on page {currentPageIndex + 1}.
                      </div>
                    )}
                  </div>
                )}

                {activeViewTab === 'blocks' && (
                  <div className="blocks-viewer">
                    {currentPage?.blocks && currentPage.blocks.length > 0 ? (
                      <div className="blocks-list">
                        {currentPage.blocks.map((b, bIdx) => (
                          <div key={bIdx} className="block-item">
                            <div className="block-meta">
                              <span className="badge badge-warning">Block #{b.block_index}</span>
                              <span className="badge badge-subtle">{b.block_type}</span>
                              {b.bbox && b.bbox.length === 4 && (
                                <code className="bbox-coords">
                                  [{b.bbox.join(', ')}]
                                </code>
                              )}
                            </div>
                            <p className="block-text">{b.text}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="empty-content">No bounding blocks for this page.</div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="inspector-empty-state">
              <Layers size={36} className="empty-icon" />
              <h3>No Document Selected</h3>
              <p>Upload a document or choose one from the repository on the left to inspect.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
