import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Package, TrendingUp, AlertTriangle, AlertCircle, Info, Bell, Upload, RefreshCw } from 'lucide-react';
import { dashboardApi, alertsApi, seedApi } from '../api/client';

const SEVERITY_COLORS = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#3b82f6' };

function formatTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [summaryRes, alertsRes] = await Promise.all([
        dashboardApi.getQualitySummary(),
        alertsApi.getAll({ limit: 5, is_read: false }),
      ]);
      setSummary(summaryRes.data);
      setAlerts(alertsRes.data.alerts || []);
    } catch (e) {
      console.error('Dashboard load error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await seedApi.seed();
      await loadData();
    } catch (e) {
      console.error('Seed error:', e);
    } finally {
      setSeeding(false);
    }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  const s = summary || {};
  const stats = [
    { label: 'Total Products', value: s.total_products || 0, icon: Package, color: 'var(--accent-primary)' },
    { label: 'Avg Quality Score', value: `${(s.average_quality_score || 0).toFixed(1)}%`, icon: TrendingUp, color: 'var(--color-success)' },
    { label: 'HIGH Issues', value: s.high_severity_count || 0, icon: AlertTriangle, color: 'var(--color-danger)' },
    { label: 'MEDIUM Issues', value: s.medium_severity_count || 0, icon: AlertCircle, color: 'var(--color-warning)' },
    { label: 'LOW Issues', value: s.low_severity_count || 0, icon: Info, color: 'var(--color-info)' },
    { label: 'Active Alerts', value: alerts.length, icon: Bell, color: '#a855f7' },
  ];

  const pieData = (s.issues_by_severity || []).map(i => ({ name: i.severity, value: i.count }));
  const barData = (s.quality_distribution || []).map(d => ({ name: d.range_label.split(' ')[0], count: d.count, fullLabel: d.range_label }));

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        {s.total_products === 0 && (
          <button className="btn-primary" onClick={handleSeed} disabled={seeding}>
            {seeding ? 'Seeding...' : '🌱 Seed Sample Data'}
          </button>
        )}
      </div>

      <div className="stats-grid">
        {stats.map((st, i) => {
          const Icon = st.icon;
          return (
            <div className="stat-card" key={i}>
              <div className="stat-card-icon" style={{ color: st.color, backgroundColor: st.color + '18' }}>
                <Icon size={22} />
              </div>
              <div className="stat-card-content">
                <div className="stat-card-value">{st.value}</div>
                <div className="stat-card-label">{st.label}</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="charts-row">
        <div className="card">
          <div className="card-header"><h3 className="card-title">Issues by Severity</h3></div>
          <div className="chart-container" style={{ height: 280 }}>
            {pieData.length > 0 ? (
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={4} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                    {pieData.map((entry, idx) => <Cell key={idx} fill={SEVERITY_COLORS[entry.name] || '#6366f1'} />)}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1a1d27', border: '1px solid #334155', borderRadius: 8, color: '#f1f5f9' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state">No issues found</div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3 className="card-title">Quality Score Distribution</h3></div>
          <div className="chart-container" style={{ height: 280 }}>
            {barData.length > 0 ? (
              <ResponsiveContainer>
                <BarChart data={barData} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} allowDecimals={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#1a1d27', border: '1px solid #334155', borderRadius: 8, color: '#f1f5f9' }} />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state">No data available</div>
            )}
          </div>
        </div>
      </div>

      <div className="charts-row">
        <div className="card" style={{ flex: 2 }}>
          <div className="card-header">
            <h3 className="card-title">Recent Alerts</h3>
            <button className="btn-sm btn-secondary" onClick={() => navigate('/alerts')}>View All</button>
          </div>
          <div className="alert-list-compact">
            {alerts.length > 0 ? alerts.map(a => (
              <div key={a.id} className="alert-row">
                <span className={`severity-dot severity-dot-${a.severity.toLowerCase()}`} />
                <div className="alert-row-content">
                  <span className="alert-row-title">{a.title}</span>
                  <span className="alert-row-meta">{a.product_sku || 'System'} · {formatTime(a.created_at)}</span>
                </div>
              </div>
            )) : <div className="empty-state">No unread alerts</div>}
          </div>
        </div>

        <div className="card" style={{ flex: 1 }}>
          <div className="card-header"><h3 className="card-title">Quick Actions</h3></div>
          <div className="quick-actions">
            <button className="btn-primary btn-lg" onClick={() => navigate('/upload')}>
              <Upload size={18} /> Upload Products
            </button>
            <button className="btn-secondary btn-lg" onClick={() => navigate('/competitor-prices')}>
              <RefreshCw size={18} /> Manage Prices
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
