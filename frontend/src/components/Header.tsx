import React from 'react';
import { Bell, User, Calendar, MapPin, RefreshCw } from 'lucide-react';

interface HeaderProps {
  selectedState: string;
  onStateChange: (state: string) => void;
  selectedDistrict: string;
  onDistrictChange: (district: string) => void;
  currentDate?: string;
  unreadAlertCount?: number;
  realtimeActive?: boolean;
  onRefresh?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  selectedState,
  onStateChange,
  selectedDistrict,
  onDistrictChange,
  currentDate = 'Wednesday, 30 Sep 2026',
  unreadAlertCount = 2,
  realtimeActive = true,
  onRefresh,
}) => {
  return (
    <header className="top-header" style={{ padding: '0 28px', height: '82px' }}>
      <div className="header-left" style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            Good morning, Administrator 👋
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Calendar size={13} />
            <span>{currentDate}</span>
          </div>
        </div>

        {/* State Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f8fafc', padding: '6px 12px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <MapPin size={15} color="#0284c7" />
          <select
            value={selectedState}
            onChange={(e) => onStateChange(e.target.value)}
            style={{
              border: 'none',
              background: 'transparent',
              fontSize: '0.82rem',
              fontWeight: 600,
              color: '#1e293b',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="ALL">All States (3)</option>
            <option value="STA">State A (Highland Region)</option>
            <option value="STB">State B (Riverine Valley)</option>
            <option value="STC">State C (Plateau Corridor)</option>
          </select>
        </div>

        {/* District Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f8fafc', padding: '6px 12px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <select
            value={selectedDistrict}
            onChange={(e) => onDistrictChange(e.target.value)}
            style={{
              border: 'none',
              background: 'transparent',
              fontSize: '0.82rem',
              fontWeight: 600,
              color: '#1e293b',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="ALL">All Districts (6)</option>
            <option value="DST-A1">DST-A1 (North Aranya)</option>
            <option value="DST-A2">DST-A2 (South Devgarh)</option>
            <option value="DST-B1">DST-B1 (East Barani)</option>
            <option value="DST-B2">DST-B2 (West Kusuma)</option>
            <option value="DST-C1">DST-C1 (Chinar Ridge)</option>
            <option value="DST-C2">DST-C2 (Dharani Plain)</option>
          </select>
        </div>
      </div>

      <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Realtime Pulse Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: realtimeActive ? '#ecfdf5' : '#f1f5f9',
            border: `1px solid ${realtimeActive ? '#a7f3d0' : '#cbd5e1'}`,
            padding: '6px 12px',
            borderRadius: '20px',
            fontSize: '0.76rem',
            fontWeight: 600,
            color: realtimeActive ? '#065f46' : '#64748b',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: realtimeActive ? '#10b981' : '#94a3b8',
              boxShadow: realtimeActive ? '0 0 8px rgba(16, 185, 129, 0.6)' : 'none',
              display: 'inline-block',
            }}
          />
          <span>{realtimeActive ? 'Live · Backend Online' : 'Backend Offline · Sample Data'}</span>
        </div>

        {/* Manual Refresh Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            title="Refresh all data from backend"
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              padding: '6px 12px', borderRadius: '20px',
              border: '1px solid #e2e8f0', background: '#ffffff',
              fontSize: '0.76rem', fontWeight: 600, cursor: 'pointer',
              color: '#0284c7', boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
            }}
          >
            <RefreshCw size={13} />
            Refresh
          </button>
        )}

        {/* Notifications Icon with Badge */}
        <div style={{ position: 'relative' }}>
          <button
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '12px',
              border: '1px solid #e2e8f0',
              background: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#334155',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
            }}
            title="Notifications"
          >
            <Bell size={18} />
          </button>
          {unreadAlertCount > 0 && (
            <span
              style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                background: '#ef4444',
                color: '#ffffff',
                borderRadius: '10px',
                fontSize: '0.65rem',
                fontWeight: 700,
                padding: '1px 5px',
                boxShadow: '0 2px 6px rgba(239, 68, 68, 0.4)',
              }}
            >
              {unreadAlertCount}
            </span>
          )}
        </div>

        {/* User Profile Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '4px 10px 4px 4px',
            borderRadius: '24px',
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
          }}
        >
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.85rem',
            }}
          >
            <User size={18} />
          </div>
          <div style={{ textAlign: 'left', lineHeight: 1.2 }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b' }}>Dr. A. Verma</div>
            <div style={{ fontSize: '0.68rem', color: '#64748b' }}>State Epidemiologist</div>
          </div>
        </div>
      </div>
    </header>
  );
};
