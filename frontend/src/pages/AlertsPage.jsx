import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Check, Filter } from 'lucide-react';
import { alertsApi } from '../api/client';

function formatTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} days ago`;
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

const SEVERITY_COLORS = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#3b82f6' };

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);
  const [severity, setSeverity] = useState('');
  const [type, setType] = useState('');
  const [readFilter, setReadFilter] = useState('');
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  useEffect(() => { loadAlerts(); }, [severity, type, readFilter, page]);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 15 };
      if (severity) params.severity = severity;
      if (type) params.type = type;
      if (readFilter === 'unread') params.is_read = false;
      if (readFilter === 'read') params.is_read = true;
      const res = await alertsApi.getAll(params);
      setAlerts(res.data.alerts || []);
      setTotal(res.data.total || 0);
      setUnread(res.data.unread_count || 0);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const markAsRead = async (alertId) => {
    try {
      await alertsApi.markRead(alertId);
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, is_read: true } : a));
      setUnread(prev => Math.max(0, prev - 1));
    } catch (e) { console.error(e); }
  };

  const extractSku = (alert) => {
    if (alert.product_sku) return alert.product_sku;
    const match = alert.message?.match(/'([^'\s]+)'/);
    return match ? match[1] : null;
  };

  const handleAlertClick = (alert) => {
    const sku = extractSku(alert);
    if (sku) navigate(`/products/${sku}`);
  };

  return (
    <div className="alerts-page">
      <div className="page-header">
        <h1 className="page-title">Alerts & Notifications</h1>
        {unread > 0 && <span className="badge badge-high">{unread} unread</span>}
      </div>

      <div className="filter-bar">
        <div className="filter-group">
          <select className="filter-select" value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1); }}>
            <option value="">All Severities</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
          <select className="filter-select" value={type} onChange={(e) => { setType(e.target.value); setPage(1); }}>
            <option value="">All Types</option>
            <option value="listing_quality">Listing Quality</option>
            <option value="price_alert">Price Alert</option>
            <option value="price_drop">Price Drop</option>
          </select>
          <select className="filter-select" value={readFilter} onChange={(e) => { setReadFilter(e.target.value); setPage(1); }}>
            <option value="">All</option>
            <option value="unread">Unread</option>
            <option value="read">Read</option>
          </select>
        </div>
        <span className="filter-count">{total} alert{total !== 1 ? 's' : ''}</span>
      </div>

      {loading ? <div className="loading-spinner"><div className="spinner" /></div> : alerts.length === 0 ? (
        <div className="card"><div className="empty-state"><Bell size={48} /><h3>No alerts</h3><p>All clear! No alerts match your filters.</p></div></div>
      ) : (
        <div className="alerts-list">
          {alerts.map(alert => {
            const sku = extractSku(alert);
            return (
            <div 
              key={alert.id} 
              className={`alert-card ${!alert.is_read ? 'alert-card-unread' : ''} ${sku ? 'clickable-alert' : ''}`}
              onClick={() => handleAlertClick(alert)}
              style={sku ? { cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s' } : {}}
              onMouseEnter={(e) => { if(sku) e.currentTarget.style.transform = 'translateY(-2px)' }}
              onMouseLeave={(e) => { if(sku) e.currentTarget.style.transform = 'translateY(0)' }}
            >
              <div className="alert-card-left">
                <span className="severity-dot" style={{ backgroundColor: SEVERITY_COLORS[alert.severity] }} />
              </div>
              <div className="alert-card-content">
                <div className="alert-card-header">
                  <span className={`badge badge-${alert.severity.toLowerCase()}`}>{alert.severity}</span>
                  <span className="alert-card-type">{alert.type?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                </div>
                <h4 className="alert-card-title">{alert.title}</h4>
                <p className="alert-card-message">{alert.message}</p>
                <div className="alert-card-meta">
                  {sku && (
                    <span className="alert-product-link" onClick={(e) => { e.stopPropagation(); navigate(`/products/${sku}`); }}>
                      {sku}
                    </span>
                  )}
                  <span className="alert-card-time">{formatTime(alert.created_at)}</span>
                </div>
              </div>
              <div className="alert-card-actions">
                {!alert.is_read && (
                  <button className="btn-sm btn-secondary" onClick={(e) => { e.stopPropagation(); markAsRead(alert.id); }} title="Mark as read">
                    <Check size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
