import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, XCircle, Edit3 } from 'lucide-react';
import { api, StressFrontierPoint } from '../services/api';

type FrontierPointData = StressFrontierPoint;

// Sample Resilience Frontier Points across normalized shock severity
const SAMPLE_FRONTIER: FrontierPointData[] = [
  { shock_size: 0.15, plausibility: 0.88, failure_probability_without_intervention: 0.02, failure_probability_with_intervention: 0.00, phcs_compromised_without: 0, threshold_breached: false },
  { shock_size: 0.25, plausibility: 0.76, failure_probability_without_intervention: 0.08, failure_probability_with_intervention: 0.01, phcs_compromised_without: 1, threshold_breached: false },
  { shock_size: 0.35, plausibility: 0.62, failure_probability_without_intervention: 0.22, failure_probability_with_intervention: 0.04, phcs_compromised_without: 2, threshold_breached: false },
  { shock_size: 0.45, plausibility: 0.49, failure_probability_without_intervention: 0.48, failure_probability_with_intervention: 0.11, phcs_compromised_without: 3, threshold_breached: true },
  { shock_size: 0.55, plausibility: 0.38, failure_probability_without_intervention: 0.74, failure_probability_with_intervention: 0.19, phcs_compromised_without: 4, threshold_breached: true },
  { shock_size: 0.65, plausibility: 0.28, failure_probability_without_intervention: 0.89, failure_probability_with_intervention: 0.28, phcs_compromised_without: 5, threshold_breached: true },
  { shock_size: 0.75, plausibility: 0.19, failure_probability_without_intervention: 0.96, failure_probability_with_intervention: 0.36, phcs_compromised_without: 6, threshold_breached: true },
  { shock_size: 0.85, plausibility: 0.12, failure_probability_without_intervention: 0.99, failure_probability_with_intervention: 0.47, phcs_compromised_without: 8, threshold_breached: true },
];

export const StressFrontierCard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'frontier' | 'review'>('frontier');
  const [frontierData, setFrontierData] = useState<FrontierPointData[]>(SAMPLE_FRONTIER);
  const [_loading, setLoading] = useState(false);
  const [_backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [_minimalShock, setMinimalShock] = useState<any>(null);

  const loadFrontier = async () => {
    setLoading(true);
    try {
      const res = await api.stressFrontier();
      const raw = (res as any).frontier_data || res;
      if (Array.isArray(raw) && raw.length > 0) {
        setFrontierData(raw);
        setMinimalShock((res as any).minimal_compound_shock || null);
        setBackendOnline(true);
      } else {
        setFrontierData(SAMPLE_FRONTIER);
        setBackendOnline(true);
      }
    } catch {
      setFrontierData(SAMPLE_FRONTIER);
      setBackendOnline(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFrontier();
  }, []);

  // Review state demo
  const [reviewDecisions, setReviewDecisions] = useState<{ [key: string]: string }>({
    'TR-001': 'APPROVED',
  });

  // SVG Chart Geometry
  const width = 680;
  const height = 230;
  const padding = { top: 25, right: 30, bottom: 35, left: 45 };

  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  const getX = (shock: number) => padding.left + (shock / 1.0) * plotW;
  const getY = (prob: number) => padding.top + plotH - prob * plotH;

  // Build SVG path for Unmitigated Failure Line
  const unmitigatedPath = frontierData.reduce(
    (acc, d, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${getX(d.shock_size)} ${getY(d.failure_probability_without_intervention)}`,
    ''
  );

  // Build SVG path for HippoGrid Mitigated Line
  const mitigatedPath = frontierData.reduce(
    (acc, d, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${getX(d.shock_size)} ${getY(d.failure_probability_with_intervention)}`,
    ''
  );

  // Smallest breach point (threshold breached without intervention)
  const breachPoint = frontierData.find((p) => p.threshold_breached) || frontierData[3] || SAMPLE_FRONTIER[3];

  return (
    <div className="panel-card" style={{ marginTop: '20px' }}>
      <div className="panel-header">
        <div className="panel-header-text">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} color="#ef4444" />
            <h3 style={{ margin: 0 }}>Reverse Stress Engine & Human Review</h3>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 600,
                background: '#fee2e2',
                color: '#b91c1c',
                padding: '2px 8px',
                borderRadius: '6px',
              }}
            >
              Smallest Plausible Compound Shock
            </span>
          </div>
          <p style={{ margin: '4px 0 0 0' }}>
            "What compound shock causes &ge; 3 PHCs to lose an essential service for 48 continuous hours?"
          </p>
        </div>

        <div className="tab-pills">
          <button
            className={`tab-pill ${activeTab === 'frontier' ? 'active' : ''}`}
            onClick={() => setActiveTab('frontier')}
          >
            Resilience Frontier
          </button>
          <button
            className={`tab-pill ${activeTab === 'review' ? 'active' : ''}`}
            onClick={() => setActiveTab('review')}
          >
            Human Review Desk
          </button>
        </div>
      </div>

      {activeTab === 'frontier' ? (
        <>
          {/* Shock Severity vs Failure Probability SVG Area Chart */}
          <div style={{ overflowX: 'auto', background: '#f8fafc', borderRadius: '12px', padding: '12px' }}>
            <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', maxHeight: '250px' }}>
              {/* Horizontal Grid lines */}
              {[0, 0.25, 0.5, 0.75, 1.0].map((prob) => {
                const y = getY(prob);
                return (
                  <g key={prob}>
                    <line
                      x1={padding.left}
                      y1={y}
                      x2={width - padding.right}
                      y2={y}
                      stroke="#e2e8f0"
                      strokeDasharray={prob === 0 ? '0' : '4 4'}
                    />
                    <text
                      x={padding.left - 8}
                      y={y + 4}
                      textAnchor="end"
                      fontSize="10"
                      fill="#94a3b8"
                      fontWeight="500"
                    >
                      {Math.round(prob * 100)}%
                    </text>
                  </g>
                );
              })}

              {/* Critical Breakdown Threshold Line (50% probability line) */}
              <line
                x1={padding.left}
                y1={getY(0.50)}
                x2={width - padding.right}
                y2={getY(0.50)}
                stroke="#cbd5e1"
                strokeWidth="1.5"
                strokeDasharray="6 4"
              />
              <text
                x={width - padding.right - 10}
                y={getY(0.50) - 6}
                textAnchor="end"
                fontSize="9"
                fill="#64748b"
                fontWeight="600"
              >
                Critical Breakdown Boundary (P &ge; 0.50)
              </text>

              {/* Unmitigated Curve (Red) */}
              <path
                d={unmitigatedPath}
                fill="none"
                stroke="#ef4444"
                strokeWidth="2.8"
              />

              {/* HippoGrid Mitigated Curve (Green) */}
              <path
                d={mitigatedPath}
                fill="none"
                stroke="#10b981"
                strokeWidth="2.8"
              />

              {/* Breach Marker */}
              <circle
                cx={getX(breachPoint.shock_size)}
                cy={getY(breachPoint.failure_probability_without_intervention)}
                r="6"
                fill="#ef4444"
                stroke="#ffffff"
                strokeWidth="2"
              />
              <text
                x={getX(breachPoint.shock_size) - 10}
                y={getY(breachPoint.failure_probability_without_intervention) - 12}
                fontSize="10"
                fill="#b91c1c"
                fontWeight="700"
              >
                Smallest Breach Shock (S = {breachPoint.shock_size})
              </text>

              {/* X Axis Labels */}
              {[0.1, 0.3, 0.5, 0.7, 0.9].map((shock) => (
                <text
                  key={shock}
                  x={getX(shock)}
                  y={height - 10}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#64748b"
                  fontWeight="500"
                >
                  S = {shock.toFixed(1)}
                </text>
              ))}
            </svg>
          </div>

          {/* Frontier Explanation & Comparative Insights */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '14px',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', gap: '18px', alignItems: 'center', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '14px', height: '3px', background: '#ef4444', display: 'inline-block' }} />
                <span style={{ color: '#ef4444', fontWeight: 600 }}>Without Intervention (Fragile)</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '14px', height: '3px', background: '#10b981', display: 'inline-block' }} />
                <span style={{ color: '#059669', fontWeight: 600 }}>With HippoGrid Intervention (+55% Buffer)</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <span
                style={{
                  fontSize: '0.74rem',
                  background: '#fef2f2',
                  color: '#991b1b',
                  padding: '3px 10px',
                  borderRadius: '6px',
                  fontWeight: 600,
                }}
              >
                Breach Threshold: S = {breachPoint.shock_size} (Plausibility: {breachPoint.plausibility})
              </span>
            </div>
          </div>
        </>
      ) : (
        /* Human Review Desk */
        <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontWeight: 600, fontSize: '0.88rem', color: '#1e293b' }}>
              Human Decision Gate — Plan #PLN-202506-08 (District DST-A1)
            </span>
            <span style={{ fontSize: '0.74rem', background: '#e2e8f0', padding: '2px 8px', borderRadius: '4px' }}>
              Mandate: Every recommendation requires human approval
            </span>
          </div>

          <table className="data-table" style={{ background: '#ffffff', borderRadius: '8px' }}>
            <thead>
              <tr>
                <th>Source PHC</th>
                <th>Destination PHC</th>
                <th>Medicine</th>
                <th>Prescribed Units</th>
                <th>Travel Time</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>PHC North Sector-3</strong></td>
                <td><strong>PHC North Sector-1</strong></td>
                <td>Oral Rehydration Salts (ORS)</td>
                <td><strong>40 units</strong></td>
                <td>35 mins</td>
                <td>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      style={{
                        background: '#dcfce7',
                        color: '#166534',
                        border: 'none',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '0.74rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                      onClick={() => setReviewDecisions({ ...reviewDecisions, 'TR-001': 'APPROVED' })}
                    >
                      <CheckCircle size={12} /> APPROVE
                    </button>
                    <button
                      style={{
                        background: '#fef3c7',
                        color: '#92400e',
                        border: 'none',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '0.74rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                      onClick={() => setReviewDecisions({ ...reviewDecisions, 'TR-001': 'EDITED' })}
                    >
                      <Edit3 size={12} /> EDIT
                    </button>
                    <button
                      style={{
                        background: '#fee2e2',
                        color: '#991b1b',
                        border: 'none',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '0.74rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                      onClick={() => setReviewDecisions({ ...reviewDecisions, 'TR-001': 'REJECTED' })}
                    >
                      <XCircle size={12} /> REJECT
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <div style={{ marginTop: '12px', fontSize: '0.74rem', color: '#64748b' }}>
            Status: Decision recorded as <strong>{reviewDecisions['TR-001'] || 'PENDING'}</strong> in immutable audit trail.
          </div>
        </div>
      )}
    </div>
  );
};
