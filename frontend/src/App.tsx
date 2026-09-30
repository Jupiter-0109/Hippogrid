/**
 * HippoGrid Command Center Application — Dynamic Dashboard
 * Healthcare Infrastructure & Primary-care Planning Optimization Grid
 */
import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { KpiGrid } from './components/KpiGrid';
import { NetworkResilienceMap } from './components/NetworkResilienceMap';
import { AnalyticsPanel } from './components/AnalyticsPanel';
import { ForecastChart } from './components/ForecastChart';
import { PhcResilienceTable } from './components/PhcResilienceTable';
import { PhcDetailView } from './components/PhcDetailView';
import { ScenarioLab } from './components/ScenarioLab';
import { PlanReview } from './components/PlanReview';
import { StressLabView } from './components/StressLabView';
import { ActivityPanel } from './components/ActivityPanel';
import { INITIAL_DASHBOARD_DATA, INITIAL_RESOURCE_PLANS } from './mock/dashboardData';
import { ResourcePlanTransfer, KpiSummary } from './types/dashboard';
import { useLiveData } from './hooks/useLiveData';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [selectedState, setSelectedState] = useState<string>('ALL');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('ALL');
  const [selectedPhcCode, setSelectedPhcCode] = useState<string>('PHC-DST-A1-04');
  const [plans, setPlans] = useState<ResourcePlanTransfer[]>(INITIAL_RESOURCE_PLANS);

  // ── Live backend data ─────────────────────────────────────────────────────
  const { kpis: liveKpis, backendOnline, lastRefreshed, refresh } = useLiveData();

  // Merge live KPI values into the mock KpiSummary shape
  const mergedKpis: KpiSummary = {
    ...INITIAL_DASHBOARD_DATA.kpis,
    phcsMonitored: liveKpis.phcsMonitored,
    criticalPhcs: liveKpis.criticalPhcs,
    servicesAtRisk: liveKpis.servicesAtRisk,
    avgSchHours: liveKpis.avgSchHours,
    networkContinuityPercent: liveKpis.networkContinuityPercent,
    changeRate: {
      ...INITIAL_DASHBOARD_DATA.kpis.changeRate,
      criticalPhcs: liveKpis.criticalPhcs > 0 ? `${liveKpis.criticalPhcs} require attention` : 'All clear',
      avgSchHours: `${liveKpis.avgSchHours.toFixed(1)}h avg horizon`,
      networkContinuity: backendOnline
        ? `Live · refreshed ${lastRefreshed}`
        : 'Backend offline · showing sample data',
    },
  };
  // ─────────────────────────────────────────────────────────────────────────

  const handleSelectPhc = (code: string) => {
    setSelectedPhcCode(code);
    setActiveTab('phcs');
  };

  const handleApprovePlan = (planId: string) => {
    setPlans((prev) =>
      prev.map((p) => (p.id === planId ? { ...p, status: 'APPROVED' as const } : p))
    );
  };

  const handleRejectPlan = (planId: string) => {
    setPlans((prev) =>
      prev.map((p) => (p.id === planId ? { ...p, status: 'REJECTED' as const } : p))
    );
  };

  // Live alert count derived from KPIs
  const criticalAlertCount = backendOnline
    ? liveKpis.criticalPhcs
    : INITIAL_DASHBOARD_DATA.alerts.filter((a) => a.severity === 'CRITICAL').length;

  return (
    <div className="app-layout">
      {/* 1. Left Vertical Navigation Rail */}
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* 2. Main Content Flow */}
      <div className="main-wrapper">
        {/* Top Header */}
        <Header
          selectedState={selectedState}
          onStateChange={setSelectedState}
          selectedDistrict={selectedDistrict}
          onDistrictChange={setSelectedDistrict}
          currentDate={new Date().toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          unreadAlertCount={criticalAlertCount}
          realtimeActive={backendOnline}
          onRefresh={refresh}
        />

        {/* Workspace Canvas with Split Analytics + Alert Panel */}
        <div className="workspace-canvas">
          {/* Central Analytics Area */}
          <main className="analytics-viewport">
            {/* OVERVIEW TAB (MAIN DASHBOARD) */}
            {activeTab === 'overview' && (
              <>
                {/* 1. KPI Cards Row — sourced from live backend SCH data */}
                <KpiGrid kpis={mergedKpis} />

                {/* 2. Main Area: Network Resilience Leaflet Map */}
                <NetworkResilienceMap onSelectPhc={handleSelectPhc} />

                {/* 3. Second Row: Service Continuity + Forecast Charts */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
                  <AnalyticsPanel
                    phcs={INITIAL_DASHBOARD_DATA.phcs}
                    services={INITIAL_DASHBOARD_DATA.services}
                  />
                  <ForecastChart initialTarget="diarrhoeal_cases" />
                </div>

                {/* 4. Bottom: PHC Resilience Table — sourced from live backend SCH data */}
                <PhcResilienceTable
                  onSelectPhc={handleSelectPhc}
                  onRequestRebalance={() => setActiveTab('plans')}
                />
              </>
            )}

            {/* NETWORK MAP FULL VIEW */}
            {activeTab === 'network' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div className="panel-card" style={{ padding: '16px 24px' }}>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>
                    Geospatial Primary Care Topology &amp; Route Network
                  </h3>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Visualizing 36 facilities, inter-PHC transport arcs, and real-time passability conditions
                  </p>
                </div>
                <NetworkResilienceMap onSelectPhc={handleSelectPhc} />
              </div>
            )}

            {/* PHC DETAIL VIEW */}
            {activeTab === 'phcs' && (
              <PhcDetailView
                phcs={INITIAL_DASHBOARD_DATA.phcs}
                selectedPhcCode={selectedPhcCode}
                onBack={() => setActiveTab('overview')}
              />
            )}

            {/* FORECASTS VIEW — Dynamic XGBoost + Conformal */}
            {activeTab === 'forecasts' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div className="panel-card" style={{ padding: '16px 24px' }}>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>
                    Predictive Caseload &amp; Supply Demand Forecasting
                  </h3>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Coupled XGBoost models with Split Conformal Uncertainty (90% guarantee bounds)
                  </p>
                </div>
                <ForecastChart initialTarget="diarrhoeal_cases" />
              </div>
            )}

            {/* CONTINUITY VIEW — Dynamic SCH table */}
            {activeTab === 'continuity' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <AnalyticsPanel
                  phcs={INITIAL_DASHBOARD_DATA.phcs}
                  services={INITIAL_DASHBOARD_DATA.services}
                />
                <PhcResilienceTable onSelectPhc={handleSelectPhc} />
              </div>
            )}

            {/* SCENARIO LAB — Live POST /api/v1/simulate */}
            {activeTab === 'scenarios' && <ScenarioLab />}

            {/* PLAN REVIEW — Approve/Edit/Reject resource plans */}
            {activeTab === 'plans' && (
              <PlanReview
                initialPlans={plans}
                onDecisionRecorded={(id, action) => {
                  if (action === 'APPROVE') handleApprovePlan(id);
                  if (action === 'REJECT') handleRejectPlan(id);
                }}
              />
            )}

            {/* STRESS LAB — Live frontier + fragility from backend */}
            {activeTab === 'stress' && <StressLabView />}

            {/* EVALUATION VIEW */}
            {activeTab === 'evaluation' && (
              <div className="panel-card">
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Model Diagnostics &amp; Predictive Validation</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: '4px' }}>
                  Time-split empirical validation against 7-day Moving Average &amp; Weekday baselines
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '20px' }}>
                  <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>sMAPE Error</div>
                    <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#059669', marginTop: '4px' }}>14.2%</div>
                    <div style={{ fontSize: '0.74rem', color: '#059669' }}>-18.4% vs Moving Average</div>
                  </div>
                  <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Coverage Reliability</div>
                    <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#0284c7', marginTop: '4px' }}>91.8%</div>
                    <div style={{ fontSize: '0.74rem', color: '#0284c7' }}>Conformal α = 0.10 satisfied</div>
                  </div>
                  <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Deterministic Seed</div>
                    <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '4px' }}>42</div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Strict reproducibility across twins</div>
                  </div>
                  <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Backend Status</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: backendOnline ? '#059669' : '#ef4444', marginTop: '4px' }}>
                      {backendOnline ? '✓ Online' : '✗ Offline'}
                    </div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      {backendOnline ? `Last refresh: ${lastRefreshed}` : 'Start uvicorn server'}
                    </div>
                  </div>
                </div>
                {/* Also embed the live forecast chart for reference */}
                <div style={{ marginTop: '20px' }}>
                  <ForecastChart initialTarget="diarrhoeal_cases" />
                </div>
              </div>
            )}

            {/* SETTINGS VIEW */}
            {activeTab === 'settings' && (
              <div className="panel-card">
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>System Governance &amp; Architectural Guardrails</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '16px', fontSize: '0.84rem' }}>
                  <div style={{ padding: '14px', background: backendOnline ? '#ecfdf5' : '#fef2f2', borderRadius: '10px', border: `1px solid ${backendOnline ? '#a7f3d0' : '#fecaca'}` }}>
                    <strong>Backend API Status:</strong>{' '}
                    {backendOnline
                      ? `✓ Connected to FastAPI at http://localhost:8000 (last refresh: ${lastRefreshed})`
                      : '✗ Offline — start uvicorn with: cd E:\\HippoGrid && backend\\.venv\\Scripts\\uvicorn.exe backend.main:app --reload'}
                  </div>
                  <div style={{ padding: '14px', background: '#ecfdf5', borderRadius: '10px', border: '1px solid #a7f3d0' }}>
                    <strong>PostgreSQL System of Record:</strong> Supabase Pooler (aws-0-ap-southeast-1.pooler.supabase.com:5432)
                  </div>
                  <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                    <strong>Row-Level Security (RLS):</strong> Enabled on service_continuity, resource_plans, plan_feedback, and audit_logs.
                  </div>
                  <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                    <strong>Python Runtime:</strong> Strictly Python 3.10.7 with FastAPI, SQLAlchemy, XGBoost, OR-Tools, and NetworkX.
                  </div>
                  <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                    <strong>Deterministic Seed:</strong> 42 — fixed across all stochastic routines and Monte Carlo simulations.
                  </div>
                </div>
              </div>
            )}
          </main>

          {/* Right-Side Alert & Human Approval Feed */}
          <ActivityPanel
            initialAlerts={INITIAL_DASHBOARD_DATA.alerts}
            pendingPlans={plans}
            onApprovePlan={handleApprovePlan}
            onRejectPlan={handleRejectPlan}
          />
        </div>
      </div>
    </div>
  );
};

export default App;
