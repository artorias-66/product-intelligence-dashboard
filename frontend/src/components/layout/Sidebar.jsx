import { NavLink, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Upload,
  Briefcase,
  Package,
  Bell,
  DollarSign,
  Zap,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { alertsApi } from '../../api/client';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/upload', label: 'Upload', icon: Upload },
  { path: '/jobs', label: 'Jobs', icon: Briefcase },
  { path: '/products', label: 'Products', icon: Package },
  { path: '/alerts', label: 'Alerts', icon: Bell, showBadge: true },
  { path: '/competitor-prices', label: 'Competitor Prices', icon: DollarSign },
];

export default function Sidebar() {
  const location = useLocation();
  const [alertCount, setAlertCount] = useState(0);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    fetchAlertCount();
    const interval = setInterval(fetchAlertCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAlertCount = async () => {
    try {
      const res = await alertsApi.getAll({ is_read: false, limit: 1 });
      const data = res.data;
      const total = data.total ?? data.length ?? 0;
      setAlertCount(typeof total === 'number' ? total : 0);
    } catch {
      // silently ignore
    }
  };

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <aside className="sidebar" style={collapsed ? { width: 72 } : {}}>
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          <Zap size={20} />
        </div>
        {!collapsed && <span className="sidebar-brand-text">ProductIQ</span>}
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`sidebar-nav-item ${isActive(item.path) ? 'active' : ''}`}
            >
              <Icon className="nav-icon" size={20} />
              {!collapsed && <span>{item.label}</span>}
              {item.showBadge && alertCount > 0 && !collapsed && (
                <span className="sidebar-nav-badge">{alertCount > 99 ? '99+' : alertCount}</span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button
          className="sidebar-collapse-btn"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>
    </aside>
  );
}
