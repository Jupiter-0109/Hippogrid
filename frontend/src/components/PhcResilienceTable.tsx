/**
 * HippoGrid PHC Resilience Table — Dynamic (Phase 4 SCH)
 * Fetches live Service Capability Horizon data from the backend.
 * Falls back to static default rows when the backend is offline.
 */
import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle, AlertCircle, ArrowUpRight, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { api, SchEntry } from '../services/api';

export interface PhcResilienceRow {
  code: string;
  name: string;
  district: string;
  worstService: string;
  schHours: number;
  limitingDependency: string;
  risk: 'CRITICAL' | 'WATCH' | 'HEALTHY';
  recommendedAction: string;
}

interface PhcResilienceTableProps {
  onSelectPhc?: (code: string) => void;
  onRequestRebalance?: (code: string) => void;
}

const DEFAULT_ROWS: PhcResilienceRow[] = [
  { code: 'PHC-DST-A1-06', name: 'PHC North Sector-6', district: 'DST-A1', worstService: 'Maternal Delivery', schHours: 12.0, limitingDependency: 'Staff Nurses (1/2 duty)', risk: 'CRITICAL', recommendedAction: 'Dispatch Relief Nurse from WH-DST-A1' },
  { code: 'PHC-DST-A1-04', name: 'PHC North Sector-4', district: 'DST-A1', worstService: 'Diarrhoeal Care', schHours: 18.0, limitingDependency: 'Oral Rehydration Salts', risk: 'CRITICAL', recommendedAction: 'Inter-PHC Transfer from Sector-3 (40 units)' },
  { code: 'PHC-DST-B1-02', name: 'PHC Barani Sector-2', district: 'DST-B1', worstService: 'Diarrhoeal Care', schHours: 16.0, limitingDependency: 'Road Inundation (Blocked)', risk: 'CRITICAL', recommendedAction: 'Reroute via Western Bypass Corridor' },
  { code: 'PHC-DST-A1-01', name: 'PHC North Sector-1', district: 'DST-A1', worstService: 'Diarrhoeal Care', schHours: 54.0, limitingDependency: 'Zinc Sulfate Buffer', risk: 'WATCH', recommendedAction: 'Schedule Priority Depot Replenishment' },
  { code: 'PHC-DST-A1-05', name: 'PHC North Sector-5', district: 'DST-A1', worstService: 'Vaccination', schHours: 50.0, limitingDependency: 'Battery Discharge Horizon', risk: 'WATCH', recommendedAction: 'Top-up Solar Storage Hybrid Inverter' },
  { code: 'PHC-DST-A1-02', name: 'PHC North Sector-2', district: 'DST-A1', worstService: 'Maternal Delivery', schHours: 88.0, limitingDependency: 'Nominal Inventory', risk: 'HEALTHY', recommendedAction: 'Maintain Current Roster & Buffer' },
  { code: 'PHC-DST-A1-03', name: 'PHC North Sector-3', district: 'DST-A1', worstService: 'Fever & Malaria', schHours: 112.0, limitingDependency: 'None (Surplus Capacity)', risk: 'HEALTHY', recommendedAction: 'Eligible Donor Facility for Sector-4' },
];

function schEntriesToRows(entries: SchEntry[]): PhcResilienceRow[] {
  // Group by PHC code, pick worst service per PHC
  const byPhc: Record<string, SchEntry[]> = {};
  for (const e of entries) {
    const key = e.phc_code || '';
    if (!byPhc[key]) byPhc[key] = [];
    byPhc[key].push(e);
  }

  return Object.entries(byPhc)
    .map(([code, svcs]) => {
      // Worst service = lowest sch_hours
      const worst = svcs.reduce((a, b) => (a.sch_hours < b.sch_hours ? a : b));
      const risk: PhcResilienceRow['risk'] =
        worst.status === 'CRITICAL' ? 'CRITICAL' :
        worst.status === 'WATCH' ? 'WATCH' : 'HEALTHY';

      const name = worst.phc_name || code;
      const parts = code.split('-');
      const district = parts.slice(0, 3).join('-');

      const serviceLabel =
        worst.service_id === 'diarrhoeal_care' ? 'Diarrhoeal Care' :
        worst.service_id === 'maternal_delivery' ? 'Maternal Delivery' :
        worst.service_id === 'vaccination' ? 'Vaccination' :
        worst.service_id === 'fever_malaria' ? 'Fever & Malaria' :
        worst.service_id || 'Unknown';

      let action = 'Monitor & maintain';
      if (risk === 'CRITICAL') action = 'Immediate resource transfer required';
      else if (risk === 'WATCH') action = 'Schedule priority replenishment';

      return {
        code,
        name,
        district,
        worstService: serviceLabel,
        schHours: worst.sch_hours,
        limitingDependency: worst.limiting_dependency || 'Unknown',
        risk,
        recommendedAction: action,
      };
    })
    .sort((a, b) => a.schHours - b.schHours); // Most critical first
}

export const PhcResilienceTable: React.FC<PhcResilienceTableProps> = ({
  onSelectPhc,
  onRequestRebalance,
}) => {
  const [rows, setRows] = useState<PhcResilienceRow[]>(DEFAULT_ROWS);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const entries = await api.sch();
      const liveRows = schEntriesToRows(entries);
      setRows(liveRows.length > 0 ? liveRows : DEFAULT_ROWS);
      setBackendOnline(true);
    } catch {
      setRows(DEFAULT_ROWS);
      setBackendOnline(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 60_000);
    return () => clearInterval(interval);
  }, []);

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'CRITICAL':
        return <span className="badge badge-critical"><ShieldAlert size={12} /> CRITICAL</span>;
      case 'WATCH':
        return <span className="badge badge-warning"><AlertCircle size={12} /> WATCH</span>;
      default:
        return <span className="badge badge-healthy"><CheckCircle size={12} /> HEALTHY</span>;
    }
  };

  const getMeterColor = (hours: number) => {
    if (hours < 48) return '#ef4444';
    if (hours < 72) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className="panel-card" style={{ marginTop: '20px' }}>
      <div className="panel-header">
        <div className="panel-header-text">
          <h3 style={{ margin: 0 }}>Primary Health Centre Resilience Matrix</h3>
          <p style={{ margin: '4px 0 0 0' }}>
            Service capability horizons, limiting constraints, and proactive resource actions
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Backend status pill */}
          <span
            style={{ fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '4px', color: backendOnline ? '#059669' : '#94a3b8' }}
            title={backendOnline ? 'Live SCH data from backend' : 'Showing sample data (backend offline)'}
          >
            {backendOnline ? <Wifi size={12} /> : <WifiOff size={12} />}
            {backendOnline === null ? 'Connecting...' : backendOnline ? 'Live SCH' : 'Offline'}
          </span>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Monitoring <strong>{rows.length}</strong> facilities
          </span>
          <button
            onClick={load}
            disabled={loading}
            title="Refresh SCH data"
            style={{
              display: 'flex', alignItems: 'center', gap: '4px',
              padding: '5px 10px', borderRadius: '8px', border: '1px solid #e2e8f0',
              background: '#f8fafc', fontSize: '0.76rem', fontWeight: 600,
              cursor: loading ? 'wait' : 'pointer', color: '#475569',
            }}
          >
            <RefreshCw size={12} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Primary Health Centre</th>
              <th>District</th>
              <th>Worst Service</th>
              <th>SCH Horizon</th>
              <th>Limiting Dependency</th>
              <th>Risk Level</th>
              <th>Recommended Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.code} style={{ cursor: 'pointer' }} onClick={() => onSelectPhc && onSelectPhc(row.code)}>
                <td>
                  <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{row.name}</div>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{row.code}</div>
                </td>
                <td><span style={{ fontWeight: 600, color: '#334155' }}>{row.district}</span></td>
                <td><span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1e293b' }}>{row.worstService}</span></td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 800, color: getMeterColor(row.schHours), fontSize: '0.92rem' }}>
                      {row.schHours.toFixed(1)}h
                    </span>
                    <div className="hours-bar-bg" style={{ width: '60px' }}>
                      <div
                        className="hours-bar-fill"
                        style={{
                          width: `${Math.min(100, (row.schHours / 120.0) * 100)}%`,
                          backgroundColor: getMeterColor(row.schHours),
                          transition: 'width 0.4s ease',
                        }}
                      />
                    </div>
                  </div>
                </td>
                <td>
                  <span style={{ background: '#f1f5f9', padding: '3px 8px', borderRadius: '6px', fontSize: '0.74rem', color: '#475569', fontWeight: 500 }}>
                    {row.limitingDependency}
                  </span>
                </td>
                <td>{getRiskBadge(row.risk)}</td>
                <td>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onRequestRebalance) onRequestRebalance(row.code);
                    }}
                    style={{
                      background: '#f0f9ff', border: '1px solid #bae6fd',
                      color: '#0284c7', padding: '4px 10px', borderRadius: '8px',
                      fontSize: '0.74rem', fontWeight: 600, cursor: 'pointer',
                      display: 'flex', alignItems: 'center', gap: '4px',
                    }}
                  >
                    <span>{row.recommendedAction}</span>
                    <ArrowUpRight size={12} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
