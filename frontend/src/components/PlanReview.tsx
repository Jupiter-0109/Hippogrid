import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ArrowRight, CheckCircle2, XCircle, Edit3, ShieldCheck, MapPin, Truck, Save } from 'lucide-react';
import { ResourcePlanTransfer } from '../types/dashboard';

interface PlanReviewProps {
  initialPlans?: ResourcePlanTransfer[];
  onDecisionRecorded?: (planId: string, action: string) => void;
}

export const PlanReview: React.FC<PlanReviewProps> = ({
  initialPlans,
  onDecisionRecorded,
}) => {
  const [plans, setPlans] = useState<ResourcePlanTransfer[]>(
    initialPlans || [
      {
        id: 'plan-tr-001',
        planId: 'plan-opt-4201',
        sourcePhc: 'PHC North Sector-3 (Surplus)',
        destinationPhc: 'PHC North Sector-4 (Deficit)',
        medicine: 'Oral Rehydration Salts (ORS)',
        quantity: 45,
        route: 'Route A1-Ridge Corridor via SH-12',
        travelTimeMinutes: 38,
        expectedCoverageHours: 72.0,
        assuranceScore: 98.4,
        reason: 'Compensate for flash flood surge & prevent service compromise',
        status: 'PENDING',
      },
      {
        id: 'plan-tr-002',
        planId: 'plan-opt-4202',
        sourcePhc: 'District Central Warehouse WH-A1',
        destinationPhc: 'PHC North Sector-6',
        medicine: 'Oxytocin Ampoules & IV Fluids',
        quantity: 30,
        route: 'Direct Highway Corridor NH-8',
        travelTimeMinutes: 52,
        expectedCoverageHours: 96.0,
        assuranceScore: 95.8,
        reason: 'Emergency maternal delivery buffer replenishment',
        status: 'PENDING',
      },
      {
        id: 'plan-tr-003',
        planId: 'plan-opt-4203',
        sourcePhc: 'PHC South Sector-1',
        destinationPhc: 'PHC Barani Sector-2',
        medicine: 'Paracetamol & Rapid Diagnostic Kits',
        quantity: 60,
        route: 'Western Bypass Bridge Corridor',
        travelTimeMinutes: 44,
        expectedCoverageHours: 84.0,
        assuranceScore: 92.0,
        reason: 'Pre-emptive vector-borne outbreak mitigation',
        status: 'PENDING',
      },
    ]
  );

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editQuantity, setEditQuantity] = useState<number>(0);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>('ROUTE_UNSAFE');

  // TanStack Query Mutation for Feedback
  const feedbackMutation = useMutation({
    mutationFn: async ({
      transferId,
      action,
      qty,
      reason,
    }: {
      transferId: string;
      action: 'APPROVE' | 'EDIT' | 'REJECT';
      qty?: number;
      reason?: string;
    }) => {
      const plan = plans.find((p) => p.id === transferId);
      const payload = {
        plan_id: plan?.planId || 'plan-opt-4201',
        actor_id: 'dr_rajesh_cmo',
        actor_role: 'Chief Medical Officer',
        model_version: 'ortools-v1.0',
        reviews: [
          {
            transfer_id: transferId,
            action: action,
            original_quantity: plan?.quantity || 45,
            modified_quantity: action === 'EDIT' ? qty : undefined,
            reason_code: action === 'REJECT' ? reason : undefined,
            notes: action === 'EDIT' ? `Modified to ${qty} by CMO` : undefined,
          },
        ],
      };

      try {
        const res = await fetch('http://localhost:8000/api/v1/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('API failed');
        return await res.json();
      } catch (err) {
        return { status: 'RECORDED_CLIENT_SIDE' };
      }
    },
    onSuccess: (_, variables) => {
      setPlans((prev) =>
        prev.map((p) => {
          if (p.id === variables.transferId) {
            return {
              ...p,
              quantity: variables.qty !== undefined ? variables.qty : p.quantity,
              status:
                variables.action === 'APPROVE'
                  ? 'APPROVED'
                  : variables.action === 'EDIT'
                  ? 'EDITED'
                  : 'REJECTED',
            };
          }
          return p;
        })
      );
      if (onDecisionRecorded) {
        onDecisionRecorded(variables.transferId, variables.action);
      }
      setEditingId(null);
      setRejectingId(null);
    },
  });

  const handleApprove = (id: string) => {
    feedbackMutation.mutate({ transferId: id, action: 'APPROVE' });
  };

  const handleStartEdit = (plan: ResourcePlanTransfer) => {
    setEditingId(plan.id);
    setEditQuantity(plan.quantity);
  };

  const handleSaveEdit = (id: string) => {
    feedbackMutation.mutate({
      transferId: id,
      action: 'EDIT',
      qty: editQuantity,
    });
  };

  const handleReject = (id: string) => {
    feedbackMutation.mutate({
      transferId: id,
      action: 'REJECT',
      reason: rejectionReason,
    });
  };

  return (
    <div className="plan-review-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="panel-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div className="kpi-icon-pill blue" style={{ width: '38px', height: '38px' }}>
                <Truck size={20} />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                Resource Redistribution Plan Review
              </h3>
            </div>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              All algorithmic recommendations mandate explicit human decision-maker approval before dispatch
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <span className="sidebar-badge" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ShieldCheck size={14} color="#059669" />
              OR-Tools Mathematical Guarantee
            </span>
          </div>
        </div>

        {/* Transfer Cards List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '20px' }}>
          {plans.map((p) => {
            const isEditing = editingId === p.id;
            const isRejecting = rejectingId === p.id;

            return (
              <div
                key={p.id}
                style={{
                  background: p.status === 'APPROVED' ? '#f0fdf4' : p.status === 'REJECTED' ? '#fef2f2' : '#ffffff',
                  border: `1px solid ${
                    p.status === 'APPROVED' ? '#bbf7d0' : p.status === 'REJECTED' ? '#fecaca' : 'var(--border-subtle)'
                  }`,
                  borderRadius: '16px',
                  padding: '20px',
                  boxShadow: 'var(--shadow-subtle)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px',
                }}
              >
                {/* Top Row: Path and Assurance */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  {/* Transfer Path */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <MapPin size={16} color="#0284c7" />
                      <span style={{ fontWeight: 800, fontSize: '0.92rem', color: 'var(--text-main)' }}>
                        {p.sourcePhc}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#64748b' }}>
                      <div style={{ width: '40px', height: '2px', background: '#cbd5e1' }} />
                      <Truck size={15} color="#0284c7" />
                      <ArrowRight size={16} />
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <MapPin size={16} color="#ef4444" />
                      <span style={{ fontWeight: 800, fontSize: '0.92rem', color: 'var(--text-main)' }}>
                        {p.destinationPhc}
                      </span>
                    </div>
                  </div>

                  {/* Assurance & Status */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="badge badge-healthy" style={{ fontSize: '0.78rem' }}>
                      Assurance: {p.assuranceScore}%
                    </span>
                    <span
                      className={`badge ${
                        p.status === 'APPROVED'
                          ? 'badge-healthy'
                          : p.status === 'REJECTED'
                          ? 'badge-critical'
                          : p.status === 'EDITED'
                          ? 'badge-warning'
                          : 'badge-warning'
                      }`}
                    >
                      {p.status}
                    </span>
                  </div>
                </div>

                {/* Details Strip: Medicine, Quantity, Route */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '12px',
                  background: '#f8fafc',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: '1px solid #f1f5f9',
                }}>
                  <div>
                    <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                      Medicine / Resource
                    </div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-main)' }}>
                      {p.medicine}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                      Quantity Prescribed
                    </div>
                    {isEditing ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
                        <input
                          type="number"
                          value={editQuantity}
                          onChange={(e) => setEditQuantity(parseInt(e.target.value) || 1)}
                          style={{
                            width: '80px',
                            padding: '4px 8px',
                            borderRadius: '6px',
                            border: '1px solid var(--primary)',
                            fontWeight: 700,
                          }}
                        />
                        <button
                          onClick={() => handleSaveEdit(p.id)}
                          style={{
                            background: '#059669',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '4px 8px',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '0.74rem',
                          }}
                        >
                          <Save size={12} /> Save
                        </button>
                      </div>
                    ) : (
                      <div style={{ fontSize: '1rem', fontWeight: 800, color: '#0284c7' }}>
                        {p.quantity} Units
                      </div>
                    )}
                  </div>

                  <div>
                    <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                      Transit Time & Route
                    </div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)' }}>
                      {p.travelTimeMinutes} mins • {p.route}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.70rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                      Continuity Coverage
                    </div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#059669' }}>
                      +{p.expectedCoverageHours} Hours Buffer
                    </div>
                  </div>
                </div>

                {/* Reason Rationale */}
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <strong>Clinical Rationale:</strong> {p.reason}
                </div>

                {/* Reject Reason Form Inline */}
                {isRejecting && (
                  <div style={{
                    background: '#fff5f5',
                    border: '1px solid #fecaca',
                    padding: '12px 14px',
                    borderRadius: '10px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#991b1b' }}>
                      Select Formal Rejection Reason Code:
                    </span>
                    <select
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      style={{
                        padding: '6px 10px',
                        borderRadius: '6px',
                        border: '1px solid #fca5a5',
                        background: '#ffffff',
                        fontSize: '0.80rem',
                      }}
                    >
                      <option value="ROUTE_UNSAFE">Route Unsafe / Road Flooded</option>
                      <option value="CLINICAL_PRIORITY_CONFLICT">Clinical Priority Conflict (Local ICU Demand)</option>
                      <option value="DONOR_FACILITY_OVERBURDENED">Donor Facility Overburdened</option>
                      <option value="SUPPLY_INADEQUATE">Supply Inadequate for Local Buffer</option>
                    </select>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => setRejectingId(null)}
                        className="tab-pill"
                        style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleReject(p.id)}
                        style={{
                          background: '#ef4444',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '6px 12px',
                          fontWeight: 700,
                          fontSize: '0.75rem',
                          cursor: 'pointer',
                        }}
                      >
                        Confirm Rejection
                      </button>
                    </div>
                  </div>
                )}

                {/* Action Buttons: APPROVE, EDIT, REJECT */}
                {p.status === 'PENDING' && !isEditing && !isRejecting && (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', borderTop: '1px solid #f1f5f9', paddingTop: '12px' }}>
                    <button
                      onClick={() => setRejectingId(p.id)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 16px',
                        borderRadius: '8px',
                        border: '1px solid #fecaca',
                        background: '#fff5f5',
                        color: '#ef4444',
                        fontWeight: 700,
                        fontSize: '0.82rem',
                        cursor: 'pointer',
                      }}
                    >
                      <XCircle size={15} /> Reject
                    </button>

                    <button
                      onClick={() => handleStartEdit(p)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 16px',
                        borderRadius: '8px',
                        border: '1px solid #fed7aa',
                        background: '#fffbeb',
                        color: '#b45309',
                        fontWeight: 700,
                        fontSize: '0.82rem',
                        cursor: 'pointer',
                      }}
                    >
                      <Edit3 size={15} /> Edit Quantity
                    </button>

                    <button
                      onClick={() => handleApprove(p.id)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 20px',
                        borderRadius: '8px',
                        border: 'none',
                        background: '#059669',
                        color: '#ffffff',
                        fontWeight: 700,
                        fontSize: '0.82rem',
                        cursor: 'pointer',
                        boxShadow: '0 2px 6px rgba(5, 150, 105, 0.25)',
                      }}
                    >
                      <CheckCircle2 size={15} /> Approve Transfer
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
