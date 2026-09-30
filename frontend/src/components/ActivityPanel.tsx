import React, { useState, useEffect } from 'react';
import { OperationalAlert, ResourcePlanTransfer } from '../types/dashboard';
import { supabase } from '../lib/supabase';
import {
  AlertTriangle,
  Zap,
  Radio,
} from 'lucide-react';

interface ActivityPanelProps {
  initialAlerts: OperationalAlert[];
  pendingPlans: ResourcePlanTransfer[];
  onApprovePlan?: (planId: string) => void;
  onRejectPlan?: (planId: string) => void;
}

export const ActivityPanel: React.FC<ActivityPanelProps> = ({
  initialAlerts,
  pendingPlans: initialPendingPlans,
  onApprovePlan,
  onRejectPlan,
}) => {
  const [activeTab, setActiveTab] = useState<'alerts' | 'recommendations' | 'approvals'>('alerts');
  const [alerts, setAlerts] = useState<OperationalAlert[]>(initialAlerts);
  const [pendingPlans, setPendingPlans] = useState<ResourcePlanTransfer[]>(initialPendingPlans);
  const [isSimulatingAlert, setIsSimulatingAlert] = useState<boolean>(false);
  const [realtimeNotice, setRealtimeNotice] = useState<string | null>(null);

  // Phase 12: Supabase Realtime Multi-Table Subscription
  useEffect(() => {
    const channel = supabase
      .channel('hippogrid-realtime-feed')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'service_continuity' },
        (payload: any) => {
          const rec = payload.new;
          if (!rec) return;

          const newAlert: OperationalAlert = {
            id: rec.id || `alt-rt-${Date.now()}`,
            timestamp: 'Just now (Realtime)',
            severity: rec.status === 'CRITICAL' ? 'CRITICAL' : 'WARNING',
            phcName: rec.phc_id ? `PHC Telemetry (${rec.phc_id.slice(0, 8)})` : 'Monitored Facility',
            serviceName: (rec.service_id || 'diarrhoeal_care').replace('_', ' ').toUpperCase(),
            message: `Continuity threshold breach detected. Service compromise in ${rec.hours_to_compromise}h.`,
            dependency: rec.primary_bottleneck || 'Supply Dependency',
            actionRequired: 'Trigger immediate resource reallocation or mobile transfer.',
            humanApprovalStatus: 'PENDING',
          };

          setAlerts((prev) => [newAlert, ...prev]);
          setRealtimeNotice(`Realtime Alert: ${newAlert.serviceName} at risk (${rec.hours_to_compromise}h)!`);
          setTimeout(() => setRealtimeNotice(null), 6000);
        }
      )
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'resource_plans' },
        (payload: any) => {
          const plan = payload.new;
          if (!plan) return;

          const newPlanTransfer: ResourcePlanTransfer = {
            id: plan.id || `plan-${Date.now()}`,
            planId: plan.id || 'plan-opt-live',
            sourcePhc: 'Regional Central Depot',
            destinationPhc: 'Vulnerable Primary Health Centre',
            medicine: 'ORS & Emergency Antipyretics',
            quantity: 50,
            route: 'Direct Route NH-8',
            travelTimeMinutes: 45,
            expectedCoverageHours: 72.0,
            assuranceScore: 97.5,
            reason: 'Automated real-time MILP rebalance recommendation',
            status: 'PENDING',
          };

          setPendingPlans((prev) => [newPlanTransfer, ...prev]);
          setRealtimeNotice('New Resource Recommendation added to Pending Approvals!');
          setTimeout(() => setRealtimeNotice(null), 6000);
        }
      )
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'plan_feedback' },
        (payload: any) => {
          const fb = payload.new;
          if (!fb) return;
          setRealtimeNotice(`Officer Review Recorded: ${fb.action || 'DECISION_LOGGED'}`);
          setTimeout(() => setRealtimeNotice(null), 5000);
        }
      )
      .subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.log('Connected to HippoGrid Supabase Realtime channel.');
        }
      });

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  // Protected Business Action: Trigger Simulated Critical Alert via FastAPI
  const handleTriggerSimulatedAlert = async () => {
    setIsSimulatingAlert(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/continuity/simulate-alert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phc_code: 'PHC-DST-A1-04',
          service_id: 'diarrhoeal_care',
          status: 'CRITICAL',
          hours_to_compromise: 8.5,
          primary_bottleneck: 'Simulated Flash Flood ORS Stockout',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        // If Realtime is active, the websocket listener also catches it;
        // update local state as well for immediate responsiveness
        const newAlert: OperationalAlert = {
          id: data.id,
          timestamp: 'Just now (FastAPI Realtime)',
          severity: 'CRITICAL',
          phcName: data.phc_name || 'PHC North Sector-4',
          serviceName: 'Diarrhoeal Care',
          message: `CRITICAL ALERT: ${data.primary_bottleneck}. SCH dropped to ${data.hours_to_compromise}h.`,
          dependency: data.primary_bottleneck,
          actionRequired: 'Dispatch immediate replenishment via Route SH-12.',
          humanApprovalStatus: 'PENDING',
        };
        setAlerts((prev) => [newAlert, ...prev]);
        setRealtimeNotice('Simulated Alert inserted into PostgreSQL System of Record!');
        setTimeout(() => setRealtimeNotice(null), 5000);
      }
    } catch (err) {
      // Offline fallback: simulate alert client-side
      const fallbackAlert: OperationalAlert = {
        id: `sim-${Date.now()}`,
        timestamp: 'Just now (Simulated)',
        severity: 'CRITICAL',
        phcName: 'PHC North Sector-4',
        serviceName: 'Diarrhoeal Care',
        message: 'CRITICAL ALERT: Simulated Flash Flood ORS Stockout. SCH 8.5h.',
        dependency: 'ORS Buffer Depleted',
        actionRequired: 'Dispatch inter-PHC replenishment from Sector-3.',
        humanApprovalStatus: 'PENDING',
      };
      setAlerts((prev) => [fallbackAlert, ...prev]);
      setRealtimeNotice('Simulated Alert rendered in Command Center!');
      setTimeout(() => setRealtimeNotice(null), 5000);
    } finally {
      setIsSimulatingAlert(false);
    }
  };

  return (
    <aside className="activity-panel">
      {/* Realtime Notification Banner */}
      {realtimeNotice && (
        <div style={{
          background: 'linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)',
          color: '#ffffff',
          padding: '10px 16px',
          fontSize: '0.76rem',
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          boxShadow: '0 2px 8px rgba(2, 132, 199, 0.3)',
        }}>
          <Radio size={14} className="status-pulse" />
          <span>{realtimeNotice}</span>
        </div>
      )}

      {/* Header */}
      <div className="activity-header">
        <div>
          <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800 }}>Command Operations</h3>
          <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
            Supabase Realtime Stream • Seed 42
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="status-pulse" style={{ backgroundColor: '#10b981' }} />
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#059669' }}>LIVE</span>
        </div>
      </div>

      {/* Tabs: Critical Alerts | Recent Recommendations | Pending Approvals */}
      <div style={{ padding: '12px 18px', borderBottom: '1px solid var(--border-subtle)', background: '#f8fafc' }}>
        <div className="tab-pills" style={{ display: 'flex', width: '100%' }}>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`tab-pill ${activeTab === 'alerts' ? 'active' : ''}`}
            style={{ flex: 1, textAlign: 'center', fontSize: '0.72rem', padding: '6px 4px' }}
          >
            Critical Alerts ({alerts.filter((a) => a.severity === 'CRITICAL').length})
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`tab-pill ${activeTab === 'recommendations' ? 'active' : ''}`}
            style={{ flex: 1, textAlign: 'center', fontSize: '0.72rem', padding: '6px 4px' }}
          >
            Recommendations
          </button>
          <button
            onClick={() => setActiveTab('approvals')}
            className={`tab-pill ${activeTab === 'approvals' ? 'active' : ''}`}
            style={{ flex: 1, textAlign: 'center', fontSize: '0.72rem', padding: '6px 4px' }}
          >
            Approvals ({pendingPlans.filter((p) => p.status === 'PENDING').length})
          </button>
        </div>
      </div>

      {/* Feed Area */}
      <div className="activity-feed">
        {/* 1. CRITICAL ALERTS TAB */}
        {activeTab === 'alerts' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Realtime Test Button as required by Phase 12 spec */}
            <button
              onClick={handleTriggerSimulatedAlert}
              disabled={isSimulatingAlert}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '10px',
                border: '1px dashed #ef4444',
                background: '#fef2f2',
                color: '#ef4444',
                fontWeight: 700,
                fontSize: '0.78rem',
                cursor: isSimulatingAlert ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'background 0.2s ease',
              }}
            >
              <Zap size={14} />
              {isSimulatingAlert ? 'Broadcasting Event...' : 'Simulate Critical Alert (Phase 12 Realtime)'}
            </button>

            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`alert-card ${
                  alert.severity === 'CRITICAL' ? 'critical' : alert.severity === 'WARNING' ? 'warning' : 'info'
                }`}
              >
                <div className="alert-top">
                  <span style={{ fontWeight: 700 }}>{alert.phcName}</span>
                  <span>{alert.timestamp}</span>
                </div>

                <div className="alert-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {alert.severity === 'CRITICAL' && <AlertTriangle size={15} color="#ef4444" />}
                  {alert.serviceName}
                </div>

                <div className="alert-desc">{alert.message}</div>

                <div className="alert-intervention">
                  <span className="intervention-label">Recommended Action:</span>
                  <span>{alert.actionRequired}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                  <span style={{ fontSize: '0.70rem', color: 'var(--text-subtle)' }}>
                    Dep: {alert.dependency}
                  </span>
                  <span className="badge badge-warning" style={{ fontSize: '0.66rem' }}>
                    {alert.humanApprovalStatus || 'PENDING'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 2. RECENT RECOMMENDATIONS TAB */}
        {activeTab === 'recommendations' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {pendingPlans.map((plan) => (
              <div
                key={plan.id}
                style={{
                  background: '#ffffff',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '12px',
                  padding: '14px',
                  boxShadow: '0 2px 6px rgba(0, 0, 0, 0.02)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--primary)' }}>
                    MILP Transfer Recommendation
                  </span>
                  <span className="badge badge-healthy" style={{ fontSize: '0.68rem' }}>
                    {plan.assuranceScore}% Assurance
                  </span>
                </div>

                <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  {plan.quantity} units of {plan.medicine}
                </div>

                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  From: {plan.sourcePhc} <br />
                  To: {plan.destinationPhc}
                </div>

                <div style={{ fontSize: '0.70rem', color: 'var(--text-subtle)' }}>
                  Transit: {plan.travelTimeMinutes} mins via {plan.route}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 3. PENDING APPROVALS TAB */}
        {activeTab === 'approvals' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
              Chief Medical Officer Approval Queue ({pendingPlans.filter((p) => p.status === 'PENDING').length} awaiting decision)
            </div>

            {pendingPlans
              .filter((p) => p.status === 'PENDING')
              .map((plan) => (
                <div
                  key={plan.id}
                  style={{
                    background: '#ffffff',
                    border: '1px solid #fde68a',
                    borderLeft: '4px solid #f59e0b',
                    borderRadius: '12px',
                    padding: '14px',
                    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.03)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 800, color: 'var(--text-main)' }}>
                      {plan.medicine}
                    </span>
                    <span className="badge badge-warning" style={{ fontSize: '0.66rem' }}>
                      PENDING DECISION
                    </span>
                  </div>

                  <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                    Transfer <strong>{plan.quantity} units</strong> to {plan.destinationPhc}
                  </div>

                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '4px' }}>
                    <button
                      onClick={() => onRejectPlan && onRejectPlan(plan.id)}
                      style={{
                        padding: '4px 10px',
                        borderRadius: '6px',
                        border: '1px solid #fecaca',
                        background: '#fff5f5',
                        color: '#ef4444',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => onApprovePlan && onApprovePlan(plan.id)}
                      style={{
                        padding: '4px 14px',
                        borderRadius: '6px',
                        border: 'none',
                        background: '#059669',
                        color: '#ffffff',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      Approve
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </aside>
  );
};
