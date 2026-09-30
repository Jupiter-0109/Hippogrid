import {
  LayoutDashboard,
  Network,
  Hospital,
  TrendingUp,
  ShieldCheck,
  Zap,
  GitPullRequest,
  Activity,
  CheckCircle2,
  Settings,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'network', label: 'Network', icon: Network },
    { id: 'phcs', label: 'PHCs', icon: Hospital },
    { id: 'forecasts', label: 'Forecasts', icon: TrendingUp },
    { id: 'continuity', label: 'Continuity', icon: ShieldCheck },
    { id: 'scenarios', label: 'Scenarios', icon: Zap },
    { id: 'plans', label: 'Resource Plans', icon: GitPullRequest },
    { id: 'stress', label: 'Stress Lab', icon: Activity },
    { id: 'evaluation', label: 'Evaluation', icon: CheckCircle2 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon-wrapper">
          <ShieldCheck size={24} />
        </div>
        <div className="brand-text">
          <h1>HIPPOGRID</h1>
          <p>PHC Continuity Twin</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onTabChange(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button
          className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => onTabChange('settings')}
        >
          <Settings size={18} />
          <span>System Config</span>
        </button>

        <div className="sidebar-badge">
          <strong>Deterministic Mode</strong>
          <div>Seed: 42 • Phase 0 Prototype</div>
        </div>
      </div>
    </aside>
  );
};
