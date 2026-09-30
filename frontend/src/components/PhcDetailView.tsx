import React, { useState } from 'react';
import { Hospital, ShieldAlert, CheckCircle, AlertTriangle, Activity, Zap, Users, ArrowLeft } from 'lucide-react';
import { PhcContinuityCard, PhcServiceDetail } from '../types/dashboard';

interface PhcDetailViewProps {
  phcs: PhcContinuityCard[];
  selectedPhcCode?: string;
  onBack?: () => void;
}

export const PhcDetailView: React.FC<PhcDetailViewProps> = ({
  phcs,
  selectedPhcCode,
  onBack,
}) => {
  const [activeCode, setActiveCode] = useState<string>(
    selectedPhcCode || phcs[0]?.code || 'PHC-DST-A1-04'
  );

  const selectedPhc = phcs.find((p) => p.code === activeCode) || phcs[0];

  // Default 4 services if not fully populated
  const defaultServices: PhcServiceDetail[] = [
    {
      id: 'diarrhoeal_care',
      name: 'Diarrhoeal Care',
      schHours: selectedPhc?.hoursToCompromise || 18.0,
      status: selectedPhc?.status === 'CRITICAL' ? 'CRITICAL' : 'WATCH',
      limitingDependency: 'Oral Rehydration Salts (ORS) & Zinc Buffer',
      forecastCaseload: 48,
      confidencePercent: 96.2,
    },
    {
      id: 'maternal_delivery',
      name: 'Maternal Delivery',
      schHours: 64.0,
      status: 'HEALTHY',
      limitingDependency: 'Staff Nurse On Duty (Nominal Roster)',
      forecastCaseload: 12,
      confidencePercent: 94.0,
    },
    {
      id: 'vaccination',
      name: 'Vaccination',
      schHours: 52.0,
      status: 'WATCH',
      limitingDependency: 'Cold Chain Ice-Pack Buffer & Inverter',
      forecastCaseload: 30,
      confidencePercent: 91.0,
    },
    {
      id: 'fever_malaria',
      name: 'Fever / Malaria',
      schHours: 82.0,
      status: 'HEALTHY',
      limitingDependency: 'Rapid Diagnostic Tests (RDT) Surplus',
      forecastCaseload: 26,
      confidencePercent: 95.5,
    },
  ];

  const services = selectedPhc?.services && selectedPhc.services.length === 4
    ? selectedPhc.services
    : defaultServices;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return (
          <span className="badge badge-critical">
            <ShieldAlert size={12} /> CRITICAL
          </span>
        );
      case 'WATCH':
      case 'WARNING':
        return (
          <span className="badge badge-warning">
            <AlertTriangle size={12} /> WATCH
          </span>
        );
      case 'HEALTHY':
      default:
        return (
          <span className="badge badge-healthy">
            <CheckCircle size={12} /> HEALTHY
          </span>
        );
    }
  };

  const getSchColor = (hours: number) => {
    if (hours < 48) return '#ef4444';
    if (hours < 72) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className="phc-detail-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Card */}
      <div className="panel-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {onBack && (
              <button
                onClick={onBack}
                className="tab-pill"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 12px' }}
              >
                <ArrowLeft size={16} /> Back to Overview
              </button>
            )}
            <div className="kpi-icon-pill blue" style={{ width: '48px', height: '48px', borderRadius: '14px' }}>
              <Hospital size={24} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                  {selectedPhc.name}
                </h2>
                <span className="sidebar-badge" style={{ padding: '3px 8px', fontWeight: 700 }}>
                  {selectedPhc.code}
                </span>
                {getStatusBadge(selectedPhc.status)}
              </div>
              <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                {selectedPhc.district} • Catchment Population: {selectedPhc.catchmentPopulation.toLocaleString()}
              </p>
            </div>
          </div>

          {/* Quick Facility Switcher Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Select Facility:</span>
            <select
              value={activeCode}
              onChange={(e) => setActiveCode(e.target.value)}
              style={{
                padding: '8px 14px',
                borderRadius: '10px',
                border: '1px solid var(--border-subtle)',
                background: '#ffffff',
                fontWeight: 600,
                fontSize: '0.84rem',
                color: 'var(--text-main)',
                cursor: 'pointer',
              }}
            >
              {phcs.map((p) => (
                <option key={p.code} value={p.code}>
                  {p.code} - {p.name} ({p.status})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Vital Facility Telemetry Strip */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '16px',
          marginTop: '20px',
          paddingTop: '16px',
          borderTop: '1px solid var(--border-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="kpi-icon-pill amber" style={{ width: '36px', height: '36px' }}>
              <Zap size={18} />
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                Power Backup
              </div>
              <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-main)' }}>
                {selectedPhc.powerBackupHours.toFixed(1)} Hours
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="kpi-icon-pill blue" style={{ width: '36px', height: '36px' }}>
              <Users size={18} />
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                Clinical Staff on Duty
              </div>
              <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-main)' }}>
                {selectedPhc.staffOnDuty} Medical Officers / Nurses
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="kpi-icon-pill red" style={{ width: '36px', height: '36px' }}>
              <ShieldAlert size={18} />
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                Primary Bottleneck
              </div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ef4444' }}>
                {selectedPhc.primaryBottleneck}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FOUR SERVICE CARDS (PHASE 11 SPEC) */}
      <div>
        <div style={{ marginBottom: '14px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
            Service Capability Horizons & Dependency Constraints
          </h3>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Individual capability assurance models across the 4 essential primary healthcare lines
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
          {services.map((srv) => {
            const schColor = getSchColor(srv.schHours);
            const schWidth = Math.min(100, (srv.schHours / 120) * 100);

            return (
              <div
                key={srv.id}
                className="panel-card"
                style={{
                  padding: '22px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px',
                  borderTop: `4px solid ${schColor}`,
                }}
              >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                      {srv.name}
                    </h4>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      Core Clinical Line
                    </span>
                  </div>
                  {getStatusBadge(srv.status)}
                </div>

                {/* SCH Meter */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.74rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-muted)' }}>
                      Service Continuity (SCH)
                    </span>
                    <span style={{ fontSize: '1.3rem', fontWeight: 800, color: schColor }}>
                      {srv.schHours.toFixed(1)} hrs
                    </span>
                  </div>
                  <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${schWidth}%`,
                        backgroundColor: schColor,
                        borderRadius: '4px',
                        transition: 'width 0.4s ease',
                      }}
                    />
                  </div>
                </div>

                {/* Limiting Dependency */}
                <div style={{
                  background: '#f8fafc',
                  border: '1px solid #f1f5f9',
                  borderRadius: '10px',
                  padding: '10px 12px',
                }}>
                  <div style={{ fontSize: '0.70rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--primary)' }}>
                    Limiting Dependency
                  </div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
                    {srv.limitingDependency}
                  </div>
                </div>

                {/* Forecast & Confidence */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '10px',
                  paddingTop: '10px',
                  borderTop: '1px solid #f1f5f9',
                }}>
                  <div>
                    <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                      Forecast (7-day)
                    </div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Activity size={14} color="#0284c7" />
                      {srv.forecastCaseload} cases
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                      Confidence Bound
                    </div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#059669' }}>
                      {srv.confidencePercent.toFixed(1)}% (90% CI)
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
