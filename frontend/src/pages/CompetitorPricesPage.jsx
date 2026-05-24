import { useState, useRef } from 'react';
import { Upload, Plus, RefreshCw, Loader2, DollarSign } from 'lucide-react';
import { competitorApi } from '../api/client';

export default function CompetitorPricesPage() {
  const [mode, setMode] = useState('upload');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState('');
  const [manualEntry, setManualEntry] = useState({
    sku_id: '', platform: 'Amazon', product_name: '', competitor_url: '', competitor_price: '', currency: 'INR'
  });
  const fileRef = useRef(null);

  const handleUploadCsv = async () => {
    if (!file) return;
    setUploading(true);
    setMessage('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await competitorApi.uploadCsv(formData);
      setMessage(res.data.message || 'Competitor prices uploaded successfully!');
      setFile(null);
    } catch (e) {
      setMessage('Upload failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setUploading(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    setUploading(true);
    setMessage('');
    try {
      const csvHeader = 'sku_id,product_name,platform,competitor_url,competitor_price,currency';
      const row = [manualEntry.sku_id, manualEntry.product_name, manualEntry.platform,
        manualEntry.competitor_url, manualEntry.competitor_price, manualEntry.currency].map(v => `"${v}"`).join(',');
      const blob = new Blob([csvHeader + '\n' + row], { type: 'text/csv' });
      const formData = new FormData();
      formData.append('file', blob, 'manual_competitor.csv');
      await competitorApi.uploadCsv(formData);
      setMessage('Competitor price added successfully!');
      setManualEntry({ sku_id: '', platform: 'Amazon', product_name: '', competitor_url: '', competitor_price: '', currency: 'INR' });
    } catch (e) {
      setMessage('Failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setUploading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setMessage('');
    try {
      const res = await competitorApi.refresh();
      setMessage(res.data.message || 'Prices refreshed successfully!');
    } catch (e) {
      setMessage('Refresh failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="competitor-page">
      <div className="page-header">
        <h1 className="page-title">Competitor Prices</h1>
        <button className="btn btn-primary" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? <><Loader2 size={16} className="spin" /> Refreshing...</> : <><RefreshCw size={16} /> Refresh All Prices</>}
        </button>
      </div>

      {message && (
        <div className={`message-banner ${message.includes('failed') || message.includes('Failed') ? 'message-error' : 'message-success'}`}>
          {message}
        </div>
      )}

      <div className="upload-mode-tabs">
        <button className={`tab-btn ${mode === 'upload' ? 'active' : ''}`} onClick={() => setMode('upload')}>
          <Upload size={16} /> Upload CSV
        </button>
        <button className={`tab-btn ${mode === 'manual' ? 'active' : ''}`} onClick={() => setMode('manual')}>
          <Plus size={16} /> Manual Entry
        </button>
      </div>

      {mode === 'upload' && (
        <div className="card">
          <div className="card-header"><h3 className="card-title">Upload Competitor Price CSV</h3></div>
          <div className={`upload-zone ${file ? 'upload-zone-has-file' : ''}`}
            onClick={() => fileRef.current?.click()}>
            <input ref={fileRef} type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} style={{ display: 'none' }} />
            {file ? (
              <div className="upload-zone-file">
                <p className="upload-zone-filename">{file.name}</p>
                <button className="btn btn-sm btn-secondary" onClick={(e) => { e.stopPropagation(); setFile(null); }}>Remove</button>
              </div>
            ) : (
              <>
                <Upload size={36} className="upload-zone-icon" />
                <p className="upload-zone-text">Drop competitor price CSV here</p>
                <p className="upload-zone-hint">Columns: sku_id, product_name, platform, competitor_url, competitor_price, currency</p>
              </>
            )}
          </div>
          <div className="upload-actions">
            <button className="btn btn-primary" onClick={handleUploadCsv} disabled={!file || uploading}>
              {uploading ? <><Loader2 size={16} className="spin" /> Uploading...</> : 'Upload Prices'}
            </button>
          </div>
        </div>
      )}

      {mode === 'manual' && (
        <div className="card">
          <div className="card-header"><h3 className="card-title">Add Competitor Price</h3></div>
          <form onSubmit={handleManualSubmit} className="manual-form">
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">SKU ID *</label>
                <input className="form-input" required value={manualEntry.sku_id}
                  onChange={(e) => setManualEntry(p => ({ ...p, sku_id: e.target.value }))} placeholder="e.g. SHOE001" />
              </div>
              <div className="form-group">
                <label className="form-label">Platform *</label>
                <select className="form-select" value={manualEntry.platform}
                  onChange={(e) => setManualEntry(p => ({ ...p, platform: e.target.value }))}>
                  {['Amazon', 'Myntra', 'Ajio', 'Nykaa Fashion', 'Tata Cliq', 'Meesho'].map(pl =>
                    <option key={pl} value={pl}>{pl}</option>
                  )}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Product Name</label>
                <input className="form-input" value={manualEntry.product_name}
                  onChange={(e) => setManualEntry(p => ({ ...p, product_name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Price (₹) *</label>
                <input className="form-input" type="number" required value={manualEntry.competitor_price}
                  onChange={(e) => setManualEntry(p => ({ ...p, competitor_price: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Competitor URL</label>
                <input className="form-input" value={manualEntry.competitor_url}
                  onChange={(e) => setManualEntry(p => ({ ...p, competitor_url: e.target.value }))} />
              </div>
            </div>
            <div className="upload-actions">
              <button type="submit" className="btn btn-primary" disabled={!manualEntry.sku_id || !manualEntry.competitor_price || uploading}>
                {uploading ? <><Loader2 size={16} className="spin" /> Adding...</> : <><Plus size={16} /> Add Price</>}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="card-header"><h3 className="card-title">About Price Refresh</h3></div>
        <p className="text-secondary" style={{ padding: '0 0 16px' }}>
          Clicking "Refresh All Prices" simulates fetching updated competitor prices from all platforms.
          Prices will be adjusted by ±3-8% to simulate real market fluctuations. Price history is recorded with each refresh.
        </p>
      </div>
    </div>
  );
}
