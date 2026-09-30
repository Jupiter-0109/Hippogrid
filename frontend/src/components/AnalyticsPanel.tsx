import React, { useState } from 'react';
import { PhcContinuityCard, ServiceTrack } from '../types/dashboard';
import { Clock, ShieldAlert, CheckCircle, AlertCircle } from 'lucide-react';

interface AnalyticsPanelProps {
  phcs: PhcContinuityCard[];
  services: ServiceTrack[];
}

export const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({ phcs, services }) => {
  const [activeTab, setActiveTab] = useState<'phcs' | 'services'>('phcs');

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return (
          <span className="badge badge-critical">
            <ShieldAlert size={12} />
            CRITICAL
          </span>
        );
      case 'WARNING':
        return (
          <span className="badge badge-warning">
            <AlertCircle size={12} />
            WARNING
          </span>
        );
      case 'HEALTHY':
      default:
        return (
          <span className="badge badge-healthy">
            <CheckCircle size={12} />
            HEALTHY
          </span>
        );
    }
  };

  const getMeterColor = (hours: number) => {
    if (hours <= 12) return '#ef4444';
    if (hours <= 24) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className="panel-card">
      <div className="panel-header">
        <div className="panel-header-text">
          <h3>Service Continuity Assurance Twin</h3>
          <p>Multi-dependency lead time to service compromise (Seed: 42)</p>
        </div>

        <div className="tab-pills">
          <button
            className={`tab-pill ${activeTab === 'phcs' ? 'active' : ''}`}
            onClick={() => setActiveTab('phcs')}
          >
            PHC Facilities ({phcs.length})
          </button>
          <button
            className={`tab-pill ${activeTab === 'services' ? 'active' : ''}`}
            onClick={() => setActiveTab('services')}
          >
            Clinical Services ({services.length})
          </button>
        </div>
      </div>

      <div className="data-table-container">
        {activeTab === 'phcs' ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Primary Health Centre</th>
                <th>Status</th>
                <th>Hours to Compromise</th>
                <th>Primary Bottleneck / Dependency</th>
                <th>Service At Risk</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {phcs.map((phc) => (
                <tr key={phc.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{phc.name}</div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      {phc.code} • Pop: {phc.catchmentPopulation.toLocaleString()}
                    </div>
                  </td>
                  <td>{getStatusBadge(phc.status)}</td>
                  <td>
                    <div className="hours-meter">
                      <Clock size={14} color={getMeterColor(phc.hoursToCompromise)} />
                      <span
                        className="hours-meter-val"
                        style={{ color: getMeterColor(phc.hoursToCompromise) }}
                      >
                        {phc.hoursToCompromise}h
                      </span>
                      <div className="hours-bar-bg">
                        <div
                          className="hours-bar-fill"
                          style={{
                            width: `${Math.min(100, (phc.hoursToCompromise / 72) * 100)}%`,
                            backgroundColor: getMeterColor(phc.hoursToCompromise),
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 500, color: '#334155' }}>
                      {phc.primaryBottleneck}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)' }}>
                      Power backup: {phc.powerBackupHours}h • Staff on duty: {phc.staffOnDuty}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, color: '#0369a1' }}>
                      {phc.criticalService}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, color: '#475569' }}>
                      {phc.confidencePercent}%
                    </span>
                    <div style={{ fontSize: '0.70rem', color: 'var(--text-subtle)' }}>
                      Conformal 95%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Service Line</th>
                <th>Criticality</th>
                <th>Continuity Score</th>
                <th>Facilities Monitored</th>
                <th>Facilities At Risk</th>
                <th>Primary Bottlenecks</th>
              </tr>
            </thead>
            <tbody>
              {services.map((svc) => (
                <tr key={svc.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{svc.name}</div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      Identifier: {svc.id}
                    </div>
                  </td>
                  <td>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        color: svc.criticality === 'CRITICAL' ? '#ef4444' : '#0284c7',
                      }}
                    >
                      {svc.criticality}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                        {svc.continuityScore}%
                      </span>
                      <div className="hours-bar-bg" style={{ width: '90px' }}>
                        <div
                          className="hours-bar-fill"
                          style={{
                            width: `${svc.continuityScore}%`,
                            backgroundColor: svc.continuityScore > 90 ? '#10b981' : '#f59e0b',
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td>
                    <strong>{svc.monitoredCount}</strong> PHCs
                  </td>
                  <td>
                    <strong style={{ color: svc.atRiskCount > 0 ? '#ef4444' : '#10b981' }}>
                      {svc.atRiskCount}
                    </strong>{' '}
                    facilities
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {svc.bottlenecks.map((b, idx) => (
                        <span
                          key={idx}
                          style={{
                            background: '#f1f5f9',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '0.72rem',
                            color: '#475569',
                          }}
                        >
                          {b}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
