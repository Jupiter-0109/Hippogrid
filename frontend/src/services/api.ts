/**
 * HippoGrid API Client
 * Healthcare Infrastructure & Primary-care Planning Optimization Grid
 *
 * Provides typed fetch wrappers for all backend API endpoints.
 * Falls back to mock data if the backend is offline.
 */

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface SchEntry {
  phc_code: string;
  phc_name: string;
  service_id: string;
  sch_hours: number;
  status: 'CRITICAL' | 'WATCH' | 'HEALTHY';
  limiting_dependency: string;
  confidence: number;
}

export interface ForecastPoint {
  record_date: string;
  actual: number;
  forecast: number;
  upper_bound: number;
}

export interface ForecastResponse {
  target: string;
  model_version: string;
  metrics: {
    mae: number;
    rmse: number;
    smape: number;
    coverage: number;
  };
  data_points: ForecastPoint[];
}

export interface SimulateRequest {
  name: string;
  rain_multiplier: number;
  road_closure_fraction: number;
  staff_absence_fraction: number;
  demand_surge_multiplier: number;
  start_date: string;
  duration_days: number;
  run_monte_carlo: boolean;
}

export interface SimulateResponse {
  mode: string;
  scenario: SimulateRequest;
  metrics: {
    total_demand: number;
    served_patients: number;
    unserved_patients: number;
    service_failure_count: number;
    patient_spillovers_count: number;
    network_continuity_rate: number;
  };
  compromised_phcs: Array<{
    code: string;
    name: string;
    compromised_services: string[];
    spillover_received: number;
  }>;
}

export interface StressFrontierPoint {
  shock_size: number;
  plausibility: number;
  failure_probability_without_intervention: number;
  failure_probability_with_intervention: number;
  phcs_compromised_without: number;
  threshold_breached: boolean;
  shock?: {
    rain_multiplier: number;
    road_closure_fraction: number;
    staff_absence_fraction: number;
    demand_surge_multiplier: number;
  };
}

export interface FragilityItem {
  rank: number;
  phc_code: string;
  phc_name: string;
  district_code: string;
  fragility_score: number;
  primary_vulnerability: string;
  first_service_to_fail: string;
  hours_to_fail_at_min_shock: number;
}

export interface PrescribeResponse {
  plan_id: string;
  algorithm: string;
  transfers: Array<{
    source_phc: string;
    destination_phc: string;
    medicine_id: string;
    quantity: number;
    route: string;
    travel_time_minutes: number;
    expected_coverage_hours: number;
    assurance_score: number;
    reason: string;
  }>;
  total_transport_cost: number;
  min_phc_coverage_hours: number;
}

export interface HealthResponse {
  status: string;
  project: string;
}

// ── API Calls ──────────────────────────────────────────────────────────────

export const api = {
  health(): Promise<HealthResponse> {
    return apiFetch<HealthResponse>('/health');
  },

  /** SCH horizons for all 36 PHCs across all 4 services */
  sch(): Promise<SchEntry[]> {
    return apiFetch<SchEntry[]>('/api/v1/sch');
  },

  /** Forecast trajectory with conformal bounds */
  forecast(target = 'diarrhoeal_cases', days = 15): Promise<ForecastResponse> {
    return apiFetch<ForecastResponse>(`/api/v1/forecast?target=${target}&days=${days}`);
  },

  /** POST simulation run */
  simulate(req: SimulateRequest): Promise<SimulateResponse> {
    return apiFetch<SimulateResponse>('/api/v1/simulate', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  /** Stress resilience frontier */
  stressFrontier(): Promise<StressFrontierPoint[]> {
    return apiFetch<StressFrontierPoint[]>('/api/v1/stress/frontier');
  },

  /** Fragility ranking */
  fragility(): Promise<FragilityItem[]> {
    return apiFetch<FragilityItem[]>('/api/v1/stress/fragility');
  },

  /** Resource prescriber */
  prescribe(stocks?: Record<string, Record<string, number>>): Promise<PrescribeResponse> {
    return apiFetch<PrescribeResponse>('/api/v1/plan/prescribe', {
      method: 'POST',
      body: JSON.stringify({ current_stocks: stocks || {} }),
    });
  },
};
