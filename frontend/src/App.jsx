import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from './services/api';
import Header from './components/Header';
import Sidebar, { NAV_ITEMS } from './components/Sidebar';
import TelemetryOverview from './components/TelemetryOverview';
import ModuleGrid from './components/ModuleGrid';
import RoadmapView from './components/RoadmapView';
import ModulePlaceholder from './components/ModulePlaceholder';
import DocumentManager from './components/DocumentManager';
import RAGAssistant from './components/RAGAssistant';
import StructuredExtraction from './components/StructuredExtraction';
import GeologicalReports from './components/GeologicalReports';
import MiningAnalytics from './components/MiningAnalytics';
import TopicIntelligence from './components/TopicIntelligence';
import ValidationBenchmarks from './components/ValidationBenchmarks';
import { initSmoothScroll, destroySmoothScroll, animatePageEntrance } from './services/motion';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('ingestion');
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const contentRef = useRef(null);

  // Light / Dark Theme State with localStorage and system preference detection
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('geomine-theme');
      if (saved === 'dark' || saved === 'light') return saved;
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'light';
  });

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      try {
        localStorage.setItem('geomine-theme', next);
        document.documentElement.setAttribute('data-theme', next);
      } catch (e) {
        console.warn('Failed to save theme to localStorage:', e);
      }
      return next;
    });
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Central Lenis + GSAP Smooth Scroll Setup
  useEffect(() => {
    const cleanup = initSmoothScroll();
    return () => {
      if (cleanup) cleanup();
      destroySmoothScroll();
    };
  }, []);

  // Subtle GSAP entrance animation on module tab change
  useEffect(() => {
    if (contentRef.current) {
      animatePageEntrance(contentRef.current);
    }
  }, [activeTab]);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    const result = await api.checkHealth();
    setHealth(result);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchHealth();
    // Auto-poll health every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const activeModuleItem = NAV_ITEMS.find((item) => item.id === activeTab);
  const activeModuleTitle = activeModuleItem ? activeModuleItem.label : 'Workspace';

  return (
    <div className="app-container">
      <Header
        health={health}
        loading={loading}
        onRefresh={fetchHealth}
        theme={theme}
        onToggleTheme={toggleTheme}
        activeModuleTitle={activeModuleTitle}
      />

      <div className="app-body">
        <Sidebar
          activeTab={activeTab}
          onTabSelect={(tab) => setActiveTab(tab)}
        />

        <main className="app-content" ref={contentRef}>
          {activeTab === 'telemetry' && (
            <>
              <TelemetryOverview health={health} loading={loading} />
              <ModuleGrid modules={health?.data?.modules || {}} />
              <RoadmapView />
            </>
          )}

          {activeTab === 'ingestion' && (
            <DocumentManager onDocumentIngested={fetchHealth} />
          )}

          {activeTab === 'rag' && (
            <RAGAssistant />
          )}

          {activeTab === 'extraction' && (
            <StructuredExtraction />
          )}

          {activeTab === 'reports' && (
            <GeologicalReports />
          )}

          {activeTab === 'analytics' && (
            <MiningAnalytics onNavigateToReports={(doc) => setActiveTab('reports')} />
          )}

          {activeTab === 'topics' && (
            <TopicIntelligence />
          )}

          {activeTab === 'benchmarks' && (
            <ValidationBenchmarks />
          )}

          {activeTab !== 'telemetry' && activeTab !== 'ingestion' && activeTab !== 'rag' && activeTab !== 'extraction' && activeTab !== 'reports' && activeTab !== 'analytics' && activeTab !== 'topics' && activeTab !== 'benchmarks' && (
            <ModulePlaceholder
              moduleId={activeTab}
              onBackToTelemetry={() => setActiveTab('telemetry')}
            />
          )}
        </main>
      </div>
    </div>
  );
}
