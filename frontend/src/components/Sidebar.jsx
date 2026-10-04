import React from 'react';
import {
  LayoutDashboard,
  Files,
  MessageSquare,
  Database,
  FileBarChart,
  BarChart3,
  Server,
  BookOpen,
  ShieldCheck,
} from 'lucide-react';

export const NAV_ITEMS = [
  {
    id: 'telemetry',
    label: 'Platform Overview',
    icon: LayoutDashboard,
  },
  {
    id: 'ingestion',
    label: 'Document Intelligence',
    icon: Files,
  },
  {
    id: 'rag',
    label: 'Knowledge Assistant',
    icon: MessageSquare,
  },
  {
    id: 'extraction',
    label: 'Structured Data',
    icon: Database,
  },
  {
    id: 'reports',
    label: 'Geological Reports',
    icon: FileBarChart,
  },
  {
    id: 'analytics',
    label: 'Mining Analytics',
    icon: BarChart3,
  },
  {
    id: 'topics',
    label: 'Topic Intelligence',
    icon: BookOpen,
  },
  {
    id: 'benchmarks',
    label: 'Validation & Benchmarks',
    icon: ShieldCheck,
  },
];

export default function Sidebar({ activeTab, onTabSelect }) {
  return (
    <aside className="app-sidebar" role="navigation" aria-label="Main platform navigation">
      <div className="sidebar-section-header">
        <span className="sidebar-section-label">WORKSPACE</span>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isSelected = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-button ${isSelected ? 'selected' : ''}`}
              onClick={() => onTabSelect(item.id)}
              id={`nav-item-${item.id}`}
              aria-current={isSelected ? 'page' : undefined}
            >
              <span className="nav-button-inner">
                <Icon size={18} strokeWidth={1.8} className="nav-icon" aria-hidden="true" />
                <span className="nav-label">{item.label}</span>
              </span>
              {isSelected && <span className="nav-active-pip" aria-hidden="true" />}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-system-card">
          <Server size={13} className="sys-icon" aria-hidden="true" />
          <div className="sys-text">
            <span className="sys-title">CMPDI / CIL</span>
            <span className="sys-version">v1.2 · 2026</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
