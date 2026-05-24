import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle, XCircle, Loader2, Clock, FileText,
  Film, AlertTriangle, Plus, RefreshCw
} from 'lucide-react';
import { jobsApi } from '../api/client';

const STATUS_CONFIG = {
  PENDING:             { color: '#94a3b8', icon: Clock,        label: 'Pending' },
  PROCESSING:          { color: '#6366f1', icon: Loader2,      label: 'Processing', spin: true },
  RUNNING:             { color: '#6366f1', icon: Loader2,      label: 'Processing', spin: true },
  COMPLETED:           { color: '#22c55e', icon: CheckCircle,  label: 'Completed' },
  PARTIALLY_COMPLETED: { color: '#f59e0b', icon: AlertTriangle,label: 'Partial' },
  FAILED:              { color: '#ef4444', icon: XCircle,      label: 'Failed' },
};

function timeStr(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleString('en-IN', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
  });
}

function elapsed(start, end) {
  if (!start) return '—';
  const diff = Math.floor((new Date(end || Date.now()) - new Date(start)) / 1000);
  if (diff < 60) return `${diff}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`;
  return `${Math.floor(diff / 3600)}h`;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef(null);

  const hasActiveJobs = (jobs) =>
    jobs.some(j => j.status === 'RUNNING' || j.status === 'PROCESSING' || j.status === 'PENDING');

  const fetchJobs = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const res = await jobsApi.getAll({ page: 1, page_size: 50 });
      const data = res.data;
      const list = data.jobs || data || [];
      setJobs(list);
      setTotal(data.total || list.length);

      // Auto-poll if active jobs exist
      if (hasActiveJobs(list)) {
        if (!intervalRef.current) {
          intervalRef.current = setInterval(() => fetchJobs(true), 2000);
        }
      } else {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const activeCount = jobs.filter(j => j.status === 'RUNNING' || j.status === 'PROCESSING' || j.status === 'PENDING').length;

  return (
    <div className="jobs-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Processing Jobs</h1>
          {activeCount > 0 && (
            <span style={{ fontSize: '0.8125rem', color: '#6366f1', display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.25rem' }}>
              <Loader2 size={13} className="spin" />
              {activeCount} job{activeCount > 1 ? 's' : ''} running · auto-refreshing
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={() => fetchJobs()}>
            <RefreshCw size={15} /> Refresh
          </button>
          <Link to="/upload" className="btn btn-primary">
            <Plus size={15} /> New Upload
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="loading-spinner"><div className="spinner" /></div>
      ) : jobs.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <FileText size={48} />
            <h3>No jobs yet</h3>
            <p>Upload a product CSV or video to create a processing job.</p>
            <Link to="/upload" className="btn btn-primary" style={{ marginTop: '1rem' }}>
              Start Upload
            </Link>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {jobs.map(job => {
            const cfg = STATUS_CONFIG[job.status] || STATUS_CONFIG.PENDING;
            const StatusIcon = cfg.icon;
            const TypeIcon = job.type === 'video_upload' ? Film : FileText;
            const pct = Math.min(100, Math.max(0, job.progress ?? 0));
            const isActive = job.status === 'RUNNING' || job.status === 'PROCESSING' || job.status === 'PENDING';

            return (
              <div key={job.id} className="card" style={{
                border: isActive ? '1px solid #6366f130' : undefined,
                transition: 'all 0.3s',
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                  {/* Icon */}
                  <div style={{ padding: '10px', borderRadius: 'var(--radius-lg)', background: 'var(--bg)', flexShrink: 0 }}>
                    <TypeIcon size={22} color={cfg.color} />
                  </div>

                  {/* Main content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.375rem' }}>
                      <span style={{ fontWeight: 600, color: '#f1f5f9', fontSize: '0.9375rem' }}>
                        {job.file_name || 'Processing Job'}
                      </span>
                      <span className="badge" style={{
                        background: cfg.color + '18', color: cfg.color,
                        border: `1px solid ${cfg.color}40`, display: 'inline-flex', alignItems: 'center', gap: '0.3rem'
                      }}>
                        <StatusIcon size={12} className={cfg.spin ? 'spin' : ''} />
                        {cfg.label}
                      </span>
                      <span className="badge-type">{job.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    </div>

                    {/* Progress bar */}
                    <div style={{ marginBottom: '0.75rem' }}>
                      <div style={{ height: 8, background: '#1e293b', borderRadius: 4, overflow: 'hidden' }}>
                        <div style={{
                          height: '100%', width: `${pct}%`,
                          background: isActive
                            ? 'linear-gradient(90deg, #6366f1, #8b5cf6)'
                            : job.status === 'COMPLETED' ? '#22c55e'
                            : job.status === 'FAILED' ? '#ef4444' : '#f59e0b',
                          borderRadius: 4,
                          transition: 'width 0.5s ease',
                        }} />
                      </div>
                    </div>

                    {/* Meta row */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', fontSize: '0.8125rem', color: '#64748b' }}>
                      <span>{job.processed_products ?? 0} / {job.total_products ?? 0} products</span>
                      <span>{pct}% complete</span>
                      <span>Created: {timeStr(job.created_at)}</span>
                      {job.started_at && <span>Duration: {elapsed(job.started_at, job.completed_at)}</span>}
                      {job.enhance_titles && <span style={{ color: '#a855f7' }}>✦ AI Enhanced</span>}
                    </div>

                    {job.error_message && (
                      <div style={{ marginTop: '0.75rem', padding: '0.625rem 0.875rem', background: '#1c0202', border: '1px solid #ef444440', borderRadius: 'var(--radius)', fontSize: '0.8125rem', color: '#ef4444' }}>
                        <AlertTriangle size={13} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                        {job.error_message.slice(0, 150)}{job.error_message.length > 150 ? '...' : ''}
                      </div>
                    )}
                  </div>

                  {/* Action */}
                  <Link to={`/jobs/${job.id}`} className="btn btn-sm btn-primary" style={{ flexShrink: 0 }}>
                    {isActive ? 'Track' : 'View'} →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
