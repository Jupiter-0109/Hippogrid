/**
 * TypeScript Data Models for HippoGrid Dashboard
 * Healthcare Infrastructure & Primary-care Planning Optimization Grid
 */

export type ContinuityStatus = 'HEALTHY' | 'WATCH' | 'WARNING' | 'CRITICAL' | 'COMPROMISED';

export interface DataQualitySummary {
  qualityScore: number;
  qualityStatus: 'HEALTHY' | 'WARNING' | 'CRITICAL';
  totalErrors: number;
  totalWarnings: number;
  rowsChecked: number;
}

export interface KpiSummary {
  phcsMonitored: number;
  criticalPhcs: number;
  servicesAtRisk: number;
  avgSchHours: number;
  activeScenarios: number;
  networkContinuityPercent: number;
  dataQuality?: DataQualitySummary;
  changeRate: {
    phcsMonitored: string;
    criticalPhcs: string;
    servicesAtRisk: string;
    avgSchHours: string;
    activeScenarios: string;
    networkContinuity: string;
  };
}

export interface PhcServiceDetail {
  id: string;
  name: string;
  schHours: number;
  status: ContinuityStatus;
  limitingDependency: string;
  forecastCaseload: number;
  confidencePercent: number;
}

export interface PhcContinuityCard {
  id: string;
  code: string;
  name: string;
  district: string;
  catchmentPopulation: number;
  status: ContinuityStatus;
  hoursToCompromise: number;
  primaryBottleneck: string;
  criticalService: string;
  confidencePercent: number;
  powerBackupHours: number;
  staffOnDuty: number;
  services?: PhcServiceDetail[];
}

export interface ServiceTrack {
  id: string;
  name: string;
  criticality: 'CRITICAL' | 'HIGH' | 'STANDARD';
  continuityScore: number; // 0 to 100
  monitoredCount: number;
  atRiskCount: number;
  status: ContinuityStatus;
  bottlenecks: string[];
}

export interface OperationalAlert {
  id: string;
  timestamp: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  phcName: string;
  serviceName: string;
  message: string;
  dependency: string;
  actionRequired: string;
  humanApprovalStatus?: 'PENDING' | 'APPROVED' | 'MODIFIED' | 'REJECTED';
}

export interface ResourcePlanTransfer {
  id: string;
  planId: string;
  sourcePhc: string;
  destinationPhc: string;
  medicine: string;
  quantity: number;
  route: string;
  travelTimeMinutes: number;
  expectedCoverageHours: number;
  assuranceScore: number;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'EDITED' | 'REJECTED';
}

export interface ScenarioParamsUI {
  rainMultiplier: number;
  roadClosureFraction: number;
  staffAbsenceFraction: number;
  demandSurgeMultiplier: number;
}

export interface DashboardState {
  kpis: KpiSummary;
  phcs: PhcContinuityCard[];
  services: ServiceTrack[];
  alerts: OperationalAlert[];
  pendingPlans: ResourcePlanTransfer[];
  lastUpdated: string;
}
