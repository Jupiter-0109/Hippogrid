/**
 * HippoGrid Live Data Hook
 * Healthcare Infrastructure & Primary-care Planning Optimization Grid
 *
 * Provides a single hook that fetches all dynamic data from the backend
 * and derives live KPI values. Falls back gracefully when backend is offline.
 */
import { useState, useEffect, useCallback } from 'react';
import { api, SchEntry } from '../services/api';
import { INITIAL_DASHBOARD_DATA } from '../mock/dashboardData';

interface LiveKpis {
  phcsMonitored: number;
  criticalPhcs: number;
  servicesAtRisk: number;
  avgSchHours: number;
  networkContinuityPercent: number;
}

interface LiveDataState {
  kpis: LiveKpis;
  schEntries: SchEntry[];
  backendOnline: boolean;
  lastRefreshed: string;
  loading: boolean;
  refresh: () => void;
}

function deriveKpis(entries: SchEntry[]): LiveKpis {
  if (entries.length === 0) {
    return {
      phcsMonitored: INITIAL_DASHBOARD_DATA.kpis.phcsMonitored,
      criticalPhcs: INITIAL_DASHBOARD_DATA.kpis.criticalPhcs,
      servicesAtRisk: INITIAL_DASHBOARD_DATA.kpis.servicesAtRisk,
      avgSchHours: INITIAL_DASHBOARD_DATA.kpis.avgSchHours,
      networkContinuityPercent: INITIAL_DASHBOARD_DATA.kpis.networkContinuityPercent,
    };
  }

  const phcCodes = [...new Set(entries.map((e) => e.phc_code || ''))];
  const phcsMonitored = phcCodes.filter(Boolean).length;

  // Worst SCH per PHC (minimum hours across all services at that PHC)
  const worstByPhc: Record<string, number> = {};
  for (const entry of entries) {
    const key = entry.phc_code || '';
    if (!key) continue;
    const cur = worstByPhc[key] ?? Infinity;
    worstByPhc[key] = Math.min(cur, entry.sch_hours);
  }

  const criticalPhcs = Object.values(worstByPhc).filter((h) => h < 48).length;
  const servicesAtRisk = entries.filter((e) => e.status === 'CRITICAL' || e.status === 'WATCH').length;
  const avgSchHours =
    entries.reduce((sum, e) => sum + e.sch_hours, 0) / Math.max(entries.length, 1);

  const healthyCount = Object.values(worstByPhc).filter((h) => h >= 72).length;
  const networkContinuityPercent = Math.round((healthyCount / phcsMonitored) * 100);

  return {
    phcsMonitored,
    criticalPhcs,
    servicesAtRisk,
    avgSchHours: Math.round(avgSchHours * 10) / 10,
    networkContinuityPercent,
  };
}

export function useLiveData(): LiveDataState {
  const [schEntries, setSchEntries] = useState<SchEntry[]>([]);
  const [backendOnline, setBackendOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>('Never');

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const entries = await api.sch();
      setSchEntries(entries);
      setBackendOnline(true);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch {
      setBackendOnline(false);
      setSchEntries([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    // Auto-refresh every 60s
    const interval = setInterval(refresh, 60_000);
    return () => clearInterval(interval);
  }, [refresh]);

  const kpis = deriveKpis(schEntries);

  return { kpis, schEntries, backendOnline, lastRefreshed, loading, refresh };
}

export type { LiveDataState, LiveKpis };
