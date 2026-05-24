import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  CheckCircle, XCircle, Loader2, Clock, FileText, Film,
  AlertTriangle, Package, RefreshCw, ChevronRight, Zap
} from 'lucide-react';
import { jobsApi } from '../api/client';

const STATUS_CONFIG = {
  PENDING:             { color: '#94a3b8', bg: '#1e293b', icon: Clock,       label: 'Pending' },
  PENDING_REVIEW:      { color: '#f59e0b', bg: '#1c1400', icon: AlertTriangle,label: 'Review Needed', spin: false },
  PROCESSING:          { color: '#6366f1', bg: '#1e1b4b', icon: Loader2,     label: 'Processing', spin: true },
  RUNNING:             { color: '#6366f1', bg: '#1e1b4b', icon: Loader2,     label: 'Processing', spin: true },
  COMPLETED:           { color: '#22c55e', bg: '#052e16', icon: CheckCircle, label: 'Completed' },
  PARTIALLY_COMPLETED: { color: '#f59e0b', bg: '#1c1400', icon: AlertTriangle,label: 'Partial' },
  FAILED:              { color: '#ef4444', bg: '#1c0202', icon: XCircle,     label: 'Failed' },
};

function elapsed(start, end) {
  if (!start) return '—';
  const s = new Date(end || Date.now());
  const diff = Math.floor((s - new Date(start)) / 1000);
  if (diff < 60) return `${diff}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`;
  return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
}

function timeStr(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleString('en-IN', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}

export default function JobDetailPage() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [approving, setApproving] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [draftData, setDraftData] = useState([]);
  const intervalRef = useRef(null);
  const pollCountRef = useRef(0);

  const isActive = (status) => status === 'RUNNING' || status === 'PROCESSING' || status === 'PENDING';
  const isReview = (status) => status === 'PENDING_REVIEW';

  const fetchJob = async () => {
    try {
      const res = await jobsApi.getById(id);
      setJob(res.data);
      setError('');
      pollCountRef.current += 1;

      if (res.data.status === 'PENDING_REVIEW' && draftData.length === 0 && res.data.draft_data) {
        setDraftData(res.data.draft_data);
      }

      // Stop polling once job finishes or needs review
      if (!isActive(res.data.status)) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load job');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJob();
    // Poll every 1.5s while job is active
    intervalRef.current = setInterval(() => {
      if (job && !isActive(job.status)) return;
      fetchJob();
    }, 1500);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [id]);

  const handleApprove = async () => {
    if (approving) return;
    setApproving(true);
    
    // Stop polling immediately to prevent in-flight requests from overriding our optimistic update
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    try {
      await jobsApi.approve(id, draftData);
      // Optimistically update to hide the dialogue box immediately
      setJob(prev => ({ ...prev, status: 'PROCESSING' }));
      
      // Wait 1.5s before we fetch the fresh state from the DB to avoid race conditions
      setTimeout(() => {
        fetchJob();
        intervalRef.current = setInterval(fetchJob, 1500);
      }, 1500);
    } catch (e) {
      const detail = e.response?.data?.detail || '';
      if (detail.includes('expected \'PENDING_REVIEW\'')) {
        await fetchJob();
        intervalRef.current = setInterval(fetchJob, 1500);
      } else {
        setError('Failed to approve job: ' + (detail || e.message));
        // Resume polling on failure
        intervalRef.current = setInterval(fetchJob, 1500);
      }
    } finally {
      setApproving(false);
    }
  };

  const handleRetry = async () => {
    if (retrying) return;
    setRetrying(true);
    try {
      await jobsApi.retry(id);
      await fetchJob(); // Get updated state (should be PENDING_REVIEW)
      // Resume polling
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(fetchJob, 1500);
    } catch (e) {
      alert('Failed to retry job: ' + (e.response?.data?.detail || e.message));
    } finally {
      setRetrying(false);
    }
  };

  const handleDraftChange = (index, field, value) => {
    const newData = [...draftData];
    newData[index] = { ...newData[index], [field]: value };
    setDraftData(newData);
  };

  const handleRemoveDraft = (index) => {
    const newData = draftData.filter((_, i) => i !== index);
    setDraftData(newData);
  };

  const handleAddDraft = () => {
    const newSku = `VID-P${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`;
    setDraftData([...draftData, {
      sku_id: newSku,
      product_title: '',
      brand: '',
      category: '',
      price: '',
      description: ''
    }]);
  };

  if (loading) return (
    <div className="loading-spinner"><div className="spinner" /></div>
  );

  if (error) return (
    <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
      <XCircle size={48} color="#ef4444" style={{ margin: '0 auto 1rem' }} />
      <h3 style={{ color: '#ef4444' }}>Error loading job</h3>
      <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>{error}</p>
      <Link to="/jobs" className="btn btn-primary" style={{ marginTop: '1.5rem', display: 'inline-flex' }}>
        Back to Jobs
      </Link>
    </div>
  );

  if (!job) return null;

  const cfg = STATUS_CONFIG[job.status] || STATUS_CONFIG.PENDING;
  const StatusIcon = cfg.icon;
  const progress = job.progress ?? 0;
  const pct = Math.min(100, Math.max(0, progress));
  const active = isActive(job.status);
  const TypeIcon = job.type === 'video_upload' ? Film : FileText;

  const steps = [
    { label: 'Job Created',    done: true,                              time: job.created_at },
    { label: 'Processing Started', done: !!job.started_at,             time: job.started_at },
    { label: 'Validating Products', done: pct >= 50 || !active,        time: (pct >= 50 || !active) ? (job.started_at || job.completed_at) : null },
    { label: 'AI Title Enhancement', done: pct >= 80 || !active,       time: (pct >= 80 || !active) ? (job.started_at || job.completed_at) : null },
    { label: 'Generating Alerts',  done: pct >= 95 || !active,         time: (pct >= 95 || !active) ? (job.started_at || job.completed_at) : null },
    { label: 'Job Complete',   done: !!job.completed_at,               time: job.completed_at },
  ];

  return (
    <div className="job-detail-page">
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <Link to="/jobs">Jobs</Link>
        <ChevronRight size={14} />
        <span>{job.file_name || job.id.slice(0, 8)}</span>
      </div>

      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '10px', borderRadius: 'var(--radius-lg)', background: cfg.bg }}>
            <TypeIcon size={28} color={cfg.color} />
          </div>
          <div>
            <h1 className="page-title">{job.file_name || 'Processing Job'}</h1>
            <span className="text-secondary">Job ID: {job.id.slice(0, 8)}... · {job.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {active && (
            <span style={{ fontSize: '0.8125rem', color: '#6366f1', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Loader2 size={14} className="spin" /> Live updating...
            </span>
          )}
          {job.status === 'FAILED' && job.draft_data && (
            <button className="btn btn-sm" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }} onClick={handleRetry} disabled={retrying}>
              <RefreshCw size={14} className={retrying ? "spin" : ""} /> {retrying ? 'Retrying...' : 'Retry Job'}
            </button>
          )}
          <span className="badge" style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}40`, fontSize: '0.875rem', padding: '6px 14px' }}>
            <StatusIcon size={14} className={cfg.spin ? 'spin' : ''} style={{ marginRight: 6 }} />
            {cfg.label}
          </span>
        </div>
      </div>

      {/* Manual Review Form (if PENDING_REVIEW) */}
      {isReview(job.status) && (
        <div className="card" style={{ marginBottom: '1.5rem', border: '1px solid #f59e0b' }}>
          <div className="card-header" style={{ background: '#1c1400', padding: '1rem', borderBottom: '1px solid #f59e0b40' }}>
            <h3 className="card-title" style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={18} /> Review Extracted Products
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginTop: '0.25rem' }}>
              Please review and correct the product details extracted from the video before proceeding.
            </p>
          </div>
          
          <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {draftData.map((item, idx) => (
              <div key={idx} style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1rem', position: 'relative' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h4 style={{ color: '#f1f5f9', margin: 0 }}>Product #{idx + 1} ({item.sku_id})</h4>
                  <button className="btn btn-sm" style={{ background: '#ef444420', color: '#ef4444', border: '1px solid #ef444440', cursor: 'pointer' }} onClick={() => handleRemoveDraft(idx)}>
                    <XCircle size={14} style={{ marginRight: '4px' }} /> Remove
                  </button>
                </div>
                <div className="form-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Title</label>
                    <input className="form-input" value={item.product_title || ''} onChange={(e) => handleDraftChange(idx, 'product_title', e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Brand</label>
                    <input className="form-input" value={item.brand || ''} onChange={(e) => handleDraftChange(idx, 'brand', e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Category</label>
                    <input className="form-input" value={item.category || ''} onChange={(e) => handleDraftChange(idx, 'category', e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Price (₹)</label>
                    <input className="form-input" type="number" value={item.price || ''} onChange={(e) => handleDraftChange(idx, 'price', e.target.value)} />
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label className="form-label">Description</label>
                    <textarea className="form-input" rows={2} value={item.description || ''} onChange={(e) => handleDraftChange(idx, 'description', e.target.value)} />
                  </div>
                </div>
              </div>
            ))}
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <button className="btn btn-secondary" onClick={handleAddDraft} style={{ borderStyle: 'dashed' }}>
                + Add Another Product
              </button>
            </div>
          </div>

          <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid var(--border)', background: 'var(--bg-lighter)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{draftData.length} product{draftData.length !== 1 ? 's' : ''} to process</span>
            <button className="btn btn-primary" onClick={handleApprove} disabled={approving || draftData.length === 0}>
              {approving ? <><Loader2 size={16} className="spin" /> Approving...</> : <><CheckCircle size={16} /> Approve & Process</>}
            </button>
          </div>
        </div>
      )}

      {/* Main Progress Card */}
      <div className="card" style={{ marginBottom: '1.5rem', border: active ? '1px solid #6366f140' : undefined }}>
        <div className="card-header">
          <h3 className="card-title">Processing Progress</h3>
          <span style={{ color: '#94a3b8', fontSize: '0.8125rem' }}>
            {job.processed_products} / {job.total_products} products
          </span>
        </div>

        {/* Big progress bar */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
              {active ? `Processing... (${pct}%)` : `${pct}% complete`}
            </span>
            <span style={{ fontSize: '2rem', fontWeight: 700, color: cfg.color, lineHeight: 1 }}>
              {pct}%
            </span>
          </div>
          <div style={{ height: 20, background: '#1e293b', borderRadius: 10, overflow: 'hidden', position: 'relative' }}>
            <div style={{
              height: '100%',
              width: `${pct}%`,
              background: active
                ? 'linear-gradient(90deg, #6366f1, #8b5cf6)'
                : job.status === 'COMPLETED' ? '#22c55e'
                : job.status === 'FAILED' ? '#ef4444'
                : '#f59e0b',
              borderRadius: 10,
              transition: 'width 0.5s ease',
              boxShadow: active ? '0 0 12px #6366f180' : 'none',
            }} />
            {active && (
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)',
                animation: 'shimmer 1.5s infinite',
                borderRadius: 10,
              }} />
            )}
          </div>
        </div>

        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
          {[
            { label: 'Total Products', value: job.total_products, color: '#6366f1', icon: Package },
            { label: 'Processed', value: job.processed_products, color: '#22c55e', icon: CheckCircle },
            { label: 'Time Elapsed', value: elapsed(job.started_at, job.completed_at), color: '#f59e0b', icon: Clock },
            { label: 'AI Enhanced', value: job.enhance_titles ? 'Yes' : 'No', color: '#a855f7', icon: Zap },
          ].map((s) => {
            const Icon = s.icon;
            return (
              <div key={s.label} style={{ background: 'var(--bg)', borderRadius: 'var(--radius-lg)', padding: '1rem', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <Icon size={16} color={s.color} />
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</span>
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: s.color }}>{s.value}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Processing Timeline */}
        <div className="card">
          <div className="card-header"><h3 className="card-title">Processing Timeline</h3></div>
          <div className="timeline">
            {steps.map((step, i) => (
              <div key={i} className={`timeline-item ${step.done ? 'done' : ''}`}>
                <div className="timeline-dot" style={step.done ? { background: cfg.color, borderColor: cfg.color } : {}} />
                {i < steps.length - 1 && (
                  <div className="timeline-line" style={{ background: step.done ? cfg.color : 'var(--border)' }} />
                )}
                <div className="timeline-content">
                  <span className="timeline-label" style={{ color: step.done ? '#f1f5f9' : '#64748b' }}>
                    {step.label}
                    {i === 1 && active && <Loader2 size={12} className="spin" style={{ marginLeft: 6, color: '#6366f1' }} />}
                  </span>
                  <span className="timeline-time">{step.time ? timeStr(step.time) : active && i > 1 ? 'In progress...' : 'Pending'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Job Info + Errors */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card">
            <div className="card-header"><h3 className="card-title">Job Details</h3></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {[
                { label: 'Job ID', value: job.id },
                { label: 'Type', value: job.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) },
                { label: 'File', value: job.file_name || '—' },
                { label: 'Created', value: timeStr(job.created_at) },
                { label: 'Started', value: timeStr(job.started_at) },
                { label: 'Finished', value: timeStr(job.completed_at) },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ color: '#64748b' }}>{label}</span>
                  <span style={{ color: '#e2e8f0', fontFamily: label === 'Job ID' ? 'monospace' : undefined, maxWidth: '60%', textAlign: 'right', wordBreak: 'break-all' }}>{value}</span>
                </div>
              ))}
            </div>
          </div>

          {job.error_message && (
            <div className="card card-error">
              <div className="card-header">
                <h3 className="card-title" style={{ color: '#ef4444' }}>
                  <AlertTriangle size={16} /> Errors / Warnings
                </h3>
              </div>
              <pre className="error-message">{job.error_message}</pre>
            </div>
          )}

          {/* Action buttons */}
          {!active && (
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <Link to="/products" className="btn btn-primary" style={{ justifyContent: 'center' }}>
                <Package size={16} /> View Products
              </Link>
              <Link to="/upload" className="btn btn-secondary" style={{ justifyContent: 'center' }}>
                <RefreshCw size={16} /> New Upload
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Products processed (when done) */}
      {job.products && job.products.length > 0 && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h3 className="card-title">Products Processed ({job.products.length})</h3>
          </div>
          <div className="card table-card" style={{ marginTop: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Title</th>
                  <th>Quality Score</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {job.products.map(p => (
                  <tr key={p.sku_id}>
                    <td className="font-mono">{p.sku_id}</td>
                    <td className="td-title">{p.product_title || <span className="text-danger">Missing</span>}</td>
                    <td>
                      <span className={`quality-score ${p.quality_score >= 80 ? 'quality-good' : p.quality_score >= 50 ? 'quality-medium' : 'quality-bad'}`}>
                        {(p.quality_score || 0).toFixed(0)}
                      </span>
                    </td>
                    <td><Link to={`/products/${p.sku_id}`} className="btn btn-sm btn-primary">View</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
}
