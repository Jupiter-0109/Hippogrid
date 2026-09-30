/**
 * HippoGrid Stress Lab View — Dynamic (Phase 9 Reverse Stress Engine)
 * Fetches live Resilience Frontier and Fragility Ranking from the backend.
 */
import React, { useState, useEffect } from 'react';
import { StressFrontierCard } from './StressFrontierCard';
import { ShieldAlert, Layers, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { api, FragilityItem } from '../services/api';

const SAMPLE_FRAGILITY: FragilityItem[] = [
  { rank: 1, phc_code: 'PHC-DST-A1-06', phc_name: 'PHC North Sector-6', district_code: 'DST-A1', fragility_score: 92.4, primary_vulnerability: 'Staff Nurse Shortage + Single Access Bridge', first_service_to_fail: 'Maternal Delivery', hours_to_fail_at_min_shock: 12.0 },
  { rank: 2, phc_code: 'PHC-DST-B1-02', phc_name: 'PHC Barani Sector-2', district_code: 'DST-B1', fragility_score: 88.6, primary_vulnerability: 'River Floodplain Inundation Cutoff', first_service_to_fail: 'Diarrhoeal Care', hours_to_fail_at_min_shock: 16.0 },
  { rank: 3, phc_code: 'PHC-DST-A1-04', phc_name: 'PHC North Sector-4', district_code: 'DST-A1', fragility_score: 84.1, primary_vulnerability: 'Rapid ORS Exhaustion during Monsoon Surge', first_service_to_fail: 'Diarrhoeal Care', hours_to_fail_at_min_shock: 18.0 },
  { rank: 4, phc_code: 'PHC-DST-A1-05', phc_name: 'PHC North Sector-5', district_code: 'DST-A1', fragility_score: 68.5, primary_vulnerability: 'Solar Battery Discharge on Rainy Days', first_service_to_fail: 'Vaccination', hours_to_fail_at_min_shock: 50.0 },
  { rank: 5, phc_code: 'PHC-DST-A1-01', phc_name: 'PHC North Sector-1', district_code: 'DST-A1', fragility_score: 62.0, primary_vulnerability: 'Secondary Route Transit Degradation', first_service_to_fail: 'Diarrhoeal Care', hours_to_fail_at_min_shock: 54.0 },
];

export const StressLabView: React.FC = () => {
  const [selectedSubTab, setSelectedSubTab] = useState<'frontier' | 'fragility' | 'scenarios'>('frontier');
  const [fragility, setFragility] = useState<FragilityItem[]>(SAMPLE_FRAGILITY);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  const loadFragility = async () => {
    setLoading(true);
    try {
      const res = await api.fragility();
      // Backend returns { ranking: [...] }
      const raw = (res as any).ranking || res;
      if (Array.isArray(raw) && raw.length > 0) {
        // Map backend fields to our FragilityItem shape
        const mapped: FragilityItem[] = raw.map((item: any, idx: number) => ({
          rank: item.rank ?? idx + 1,
          phc_code: item.phc_code || item.code || '',
          phc_name: item.phc_name || item.name || item.phc_code || '',
          district_code: item.district_code || item.district || '',
          fragility_score: item.fragility_score ?? item.fragilityScore ?? 0,
          primary_vulnerability: item.primary_vulnerability || item.criticalVulnerability || 'Unknown',
          first_service_to_fail: item.first_service_to_fail || item.firstServiceToFail || '',
          hours_to_fail_at_min_shock: item.hours_to_fail_at_min_shock ?? item.hoursToFailAtMinShock ?? 0,
        }));
        setFragility(mapped);
        setBackendOnline(true);
      } else {
        setFragility(SAMPLE_FRAGILITY);
        setBackendOnline(true);
      }
    } catch {
      setFragility(SAMPLE_FRAGILITY);
      setBackendOnline(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFragility();
  }, []);

  return (
    <div className="stress-lab-view" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Subnavigation Bar */}
      <div className="panel-card" style={{ padding: '16px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Stress Lab &amp; Resilience Frontier
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Quantitative reverse stress testing • Smallest plausible compound shock identification
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Status indicator */}
            <span style={{ fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '4px', color: backendOnline ? '#059669' : '#94a3b8' }}>
              {backendOnline ? <Wifi size={12} /> : <WifiOff size={12} />}
              {backendOnline === null ? 'Connecting...' : backendOnline ? 'Live' : 'Sample Data'}
            </span>
            <button
              onClick={loadFragility}
              disabled={loading}
              style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '5px 10px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#f8fafc', fontSize: '0.76rem', fontWeight: 600, cursor: loading ? 'wait' : 'pointer', color: '#475569' }}
            >
              <RefreshCw size={12} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              Refresh
            </button>

            <div className="tab-pills">
              {(['frontier', 'fragility', 'scenarios'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setSelectedSubTab(tab)}
                  className={`tab-pill ${selectedSubTab === tab ? 'active' : ''}`}
                >
                  {tab === 'frontier' ? 'Resilience Frontier' : tab === 'fragility' ? 'Fragility Ranking' : 'Scenario Comparison'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 1. RESILIENCE FRONTIER — dynamic via StressFrontierCard */}
      {selectedSubTab === 'frontier' && <StressFrontierCard />}

      {/* 2. FRAGILITY RANKINGS — live from backend */}
      {selectedSubTab === 'fragility' && (
        <div className="panel-card">
          <div className="panel-header">
            <div className="panel-header-text">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={20} color="#ef4444" />
                <h3 style={{ margin: 0 }}>Network Fragility Ranking</h3>
              </div>
              <p style={{ margin: '4px 0 0 0' }}>
                PHCs ordered by systemic vulnerability to combined shocks
              </p>
            </div>
            <span className="badge badge-critical">
              Top {Math.min(3, fragility.filter((f) => f.fragility_score > 80).length)} Require Active Rebalance
            </span>
          </div>

          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Facility</th>
                  <th>District</th>
                  <th>Fragility Score</th>
                  <th>First Service to Fail</th>
                  <th>Min Shock Horizon</th>
                  <th>Critical Vulnerability</th>
                </tr>
              </thead>
              <tbody>
                {fragility.map((item) => (
                  <tr key={item.phc_code}>
                    <td>
                      <span
                        style={{
                          width: '24px', height: '24px', borderRadius: '50%',
                          background: item.rank <= 3 ? '#fee2e2' : '#f1f5f9',
                          color: item.rank <= 3 ? '#ef4444' : '#64748b',
                          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                          fontWeight: 800, fontSize: '0.75rem',
                        }}
                      >
                        #{item.rank}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{item.phc_name}</div>
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{item.phc_code}</div>
                    </td>
                    <td>{item.district_code}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 800, color: item.fragility_score > 80 ? '#ef4444' : '#f59e0b' }}>
                          {item.fragility_score.toFixed(1)}
                        </span>
                        <div style={{ width: '60px', height: '6px', background: '#e2e8f0', borderRadius: '3px' }}>
                          <div
                            style={{
                              width: `${item.fragility_score}%`, height: '100%',
                              backgroundColor: item.fragility_score > 80 ? '#ef4444' : '#f59e0b',
                              borderRadius: '3px', transition: 'width 0.4s ease',
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-warning" style={{ fontSize: '0.72rem' }}>
                        {item.first_service_to_fail}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 700, color: item.hours_to_fail_at_min_shock < 24 ? '#ef4444' : '#f59e0b' }}>
                        {item.hours_to_fail_at_min_shock} Hours
                      </span>
                    </td>
                    <td style={{ fontSize: '0.78rem', color: '#475569' }}>{item.primary_vulnerability}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. SCENARIO COMPARISON */}
      {selectedSubTab === 'scenarios' && (
        <div className="panel-card">
          <div className="panel-header">
            <div className="panel-header-text">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={20} color="#0284c7" />
                <h3 style={{ margin: 0 }}>Scenario Stress Comparison Matrix</h3>
              </div>
              <p style={{ margin: '4px 0 0 0' }}>
                Side-by-side performance of primary care network across multi-hazard conditions
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '18px' }}>
            <div style={{ background: '#f8fafc', padding: '20px', borderRadius: '16px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 800 }}>Baseline Conditions</h4>
                <span className="badge badge-healthy">Nominal</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem' }}>
                <div><strong>Rain:</strong> 1.0x (Normal)</div>
                <div><strong>Roads:</strong> 100% Passable</div>
                <div><strong>Staff:</strong> Full Roster (0% Absence)</div>
                <div><strong>Demand:</strong> 1.0x Expected</div>
                <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '8px 0' }} />
                <div style={{ color: '#059669', fontWeight: 700 }}>Service Continuity: 98.2%</div>
                <div style={{ color: '#64748b' }}>Compromised PHCs: 0</div>
              </div>
            </div>

            <div style={{ background: '#fffbeb', padding: '20px', borderRadius: '16px', border: '1px solid #fde68a' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 800 }}>Monsoon Flash Flood</h4>
                <span className="badge badge-warning">High Risk</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem' }}>
                <div><strong>Rain:</strong> 2.8x (Heavy Inundation)</div>
                <div><strong>Roads:</strong> 35% Inundated / Blocked</div>
                <div><strong>Staff:</strong> 15% Commute Delays</div>
                <div><strong>Demand:</strong> 1.8x Diarrhoeal Spike</div>
                <hr style={{ border: 'none', borderTop: '1px solid #fde68a', margin: '8px 0' }} />
                <div style={{ color: '#d97706', fontWeight: 700 }}>Service Continuity: 78.4%</div>
                <div style={{ color: '#d97706' }}>Compromised PHCs: 3 facilities</div>
              </div>
            </div>

            <div style={{ background: '#fff5f5', padding: '20px', borderRadius: '16px', border: '1px solid #fecaca' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 800 }}>Compound Black Sky</h4>
                <span className="badge badge-critical">Critical</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem' }}>
                <div><strong>Rain:</strong> 3.5x Extreme Cloudburst</div>
                <div><strong>Roads:</strong> 60% Transit Cut</div>
                <div><strong>Staff:</strong> 40% Absence / Illness</div>
                <div><strong>Demand:</strong> 2.5x Epidemic Outbreak</div>
                <hr style={{ border: 'none', borderTop: '1px solid #fecaca', margin: '8px 0' }} />
                <div style={{ color: '#ef4444', fontWeight: 700 }}>Service Continuity: 48.0%</div>
                <div style={{ color: '#ef4444' }}>Compromised PHCs: 8 facilities</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
