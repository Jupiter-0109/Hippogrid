import React from 'react';
import { Hospital, AlertTriangle, Activity, Clock, ShieldCheck, Layers } from 'lucide-react';
import { KpiSummary } from '../types/dashboard';

interface KpiGridProps {
  kpis: KpiSummary;
}

export const KpiGrid: React.FC<KpiGridProps> = ({ kpis }) => {
  return (
    <div className="kpi-grid">
      {/* 1. PHCs Monitored */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-label">PHCs Monitored</span>
          <div className="kpi-icon-pill blue">
            <Hospital size={18} />
          </div>
        </div>
        <div className="kpi-body">
          <span className="kpi-value">{kpis.phcsMonitored}</span>
          <span className="kpi-unit">facilities</span>
        </div>
        <div className="kpi-footer" style={{ color: '#0284c7' }}>
          <span>{kpis.changeRate.phcsMonitored}</span>
        </div>
      </div>

      {/* 2. Critical PHCs */}
      <div className="kpi-card" style={{ borderColor: kpis.criticalPhcs > 0 ? '#fecaca' : undefined }}>
        <div className="kpi-header">
          <span className="kpi-label">Critical PHCs</span>
          <div className="kpi-icon-pill red">
            <AlertTriangle size={18} />
          </div>
        </div>
        <div className="kpi-body">
          <span className="kpi-value" style={{ color: '#ef4444' }}>
            {kpis.criticalPhcs}
          </span>
          <span className="kpi-unit">at breach horizon</span>
        </div>
        <div className="kpi-footer" style={{ color: '#ef4444' }}>
          <span>{kpis.changeRate.criticalPhcs}</span>
        </div>
      </div>

      {/* 3. Services at Risk */}
      <div className="kpi-card" style={{ borderColor: kpis.servicesAtRisk > 0 ? '#fde68a' : undefined }}>
        <div className="kpi-header">
          <span className="kpi-label">Services At Risk</span>
          <div className="kpi-icon-pill amber">
            <Activity size={18} />
          </div>
        </div>
        <div className="kpi-body">
          <span className="kpi-value" style={{ color: '#d97706' }}>
            {kpis.servicesAtRisk}
          </span>
          <span className="kpi-unit">clinical lines</span>
        </div>
        <div className="kpi-footer" style={{ color: '#d97706' }}>
          <span>{kpis.changeRate.servicesAtRisk}</span>
        </div>
      </div>

      {/* 4. Average SCH */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-label">Average SCH</span>
          <div className="kpi-icon-pill green">
            <Clock size={18} />
          </div>
        </div>
        <div className="kpi-body">
          <span className="kpi-value" style={{ color: '#059669' }}>
            {kpis.avgSchHours.toFixed(1)}h
          </span>
          <span className="kpi-unit">service horizon</span>
        </div>
        <div className="kpi-footer" style={{ color: '#059669' }}>
          <span>{kpis.changeRate.avgSchHours}</span>
        </div>
      </div>

      {/* 5. Data Quality */}
      {kpis.dataQuality && (
        <div
          className="kpi-card"
          style={{
            borderColor:
              kpis.dataQuality.qualityScore < 85.0
                ? '#ef4444'
                : kpis.dataQuality.qualityScore < 95.0
                ? '#f59e0b'
                : 'rgba(226, 232, 240, 0.7)',
            backgroundColor:
              kpis.dataQuality.qualityScore < 85.0 ? '#fff5f5' : 'var(--bg-card)',
          }}
        >
          <div className="kpi-header">
            <span className="kpi-label">Data Quality</span>
            <div
              className={`kpi-icon-pill ${
                kpis.dataQuality.qualityScore < 85.0
                  ? 'red'
                  : kpis.dataQuality.qualityScore < 95.0
                  ? 'amber'
                  : 'green'
              }`}
            >
              {kpis.dataQuality.qualityScore < 85.0 ? (
                <AlertTriangle size={18} />
              ) : (
                <ShieldCheck size={18} />
              )}
            </div>
          </div>
          <div className="kpi-body">
            <span
              className="kpi-value"
              style={{
                color:
                  kpis.dataQuality.qualityScore < 85.0
                    ? '#ef4444'
                    : kpis.dataQuality.qualityScore < 95.0
                    ? '#d97706'
                    : '#059669',
              }}
            >
              {kpis.dataQuality.qualityScore}%
            </span>
            <span className="kpi-unit">quality score</span>
          </div>
          <div className="kpi-footer">
            {kpis.dataQuality.totalErrors > 0 ? (
              <span style={{ color: '#ef4444', fontWeight: 600 }}>
                ⚠️ {kpis.dataQuality.totalErrors} errors detected
              </span>
            ) : (
              <span style={{ color: '#059669' }}>
                100% verified ({kpis.dataQuality.rowsChecked.toLocaleString()} rows)
              </span>
            )}
          </div>
        </div>
      )}

      {/* 6. Active Scenarios */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-label">Active Scenarios</span>
          <div className="kpi-icon-pill blue">
            <Layers size={18} />
          </div>
        </div>
        <div className="kpi-body">
          <span className="kpi-value" style={{ color: '#0284c7' }}>
            {kpis.activeScenarios}
          </span>
          <span className="kpi-unit">simulated twins</span>
        </div>
        <div className="kpi-footer" style={{ color: '#0284c7' }}>
          <span>{kpis.changeRate.activeScenarios}</span>
        </div>
      </div>
    </div>
  );
};
