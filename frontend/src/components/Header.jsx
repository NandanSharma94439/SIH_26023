import React from 'react';
import { Layers, RefreshCw, Sun, Moon } from 'lucide-react';

export default function Header({
  health,
  loading,
  onRefresh,
  theme = 'light',
  onToggleTheme,
  activeModuleTitle = 'Document Intelligence',
}) {
  const isOnline = health?.success && health?.data?.status === 'ok';

  return (
    <header className="app-header" role="banner">
      <div className="header-left">
        <div className="header-brand">
          <div className="brand-logo-container" aria-hidden="true">
            <Layers size={18} />
          </div>
          <div className="brand-text">
            <span className="brand-title">GeoMine Intelligence</span>
            <span className="brand-subtitle">CMPDI · Exploration Suite</span>
          </div>
        </div>

        {activeModuleTitle && (
          <div className="header-context-divider" aria-hidden="true">
            <span className="context-slash">/</span>
            <span className="active-context-label">{activeModuleTitle}</span>
          </div>
        )}
      </div>

      <div className="header-actions">
        {/* Light / Dark Theme Toggle */}
        <button
          type="button"
          className="theme-toggle-btn"
          onClick={onToggleTheme}
          title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
          aria-label={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
          id="theme-toggle-btn"
        >
          {theme === 'dark' ? (
            <Sun size={15} className="theme-icon sun-icon" aria-hidden="true" />
          ) : (
            <Moon size={15} className="theme-icon moon-icon" aria-hidden="true" />
          )}
          <span className="theme-toggle-text">{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>

        {/* Backend API Health Status */}
        <div
          className={`health-status-chip ${isOnline ? 'online' : 'offline'}`}
          role="status"
          aria-live="polite"
        >
          <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
          <span className="health-label">
            {loading ? 'Connecting…' : isOnline ? 'API Ready' : 'API Offline'}
          </span>
          {health?.latencyMs !== undefined && (
            <span className="health-latency">{health.latencyMs}ms</span>
          )}
        </div>

        {/* Refresh Health Button */}
        <button
          className="refresh-btn"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh backend status"
          id="refresh-health-btn"
          aria-label="Refresh backend health status"
        >
          <RefreshCw size={13} className={loading ? 'spinning' : ''} aria-hidden="true" />
          <span>Refresh</span>
        </button>
      </div>
    </header>
  );
}
