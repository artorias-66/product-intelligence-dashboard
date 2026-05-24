import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Film, Check, Loader2 } from 'lucide-react';
import { uploadApi } from '../api/client';

export default function UploadPage() {
  const [mode, setMode] = useState('video');
  const [file, setFile] = useState(null);
  const [enhanceTitles, setEnhanceTitles] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [videoHint, setVideoHint] = useState('');
  const [manualProduct, setManualProduct] = useState({
    sku_id: '', product_title: '', description: '', brand: '', category: '',
    price: '', mrp: '', image_url: '', product_url: '', color: '', size: '', material: '', availability: 'in_stock'
  });
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleDrag = (e) => { e.preventDefault(); e.stopPropagation(); setDragActive(e.type === 'dragenter' || e.type === 'dragover'); };
  const handleDrop = (e) => { e.preventDefault(); e.stopPropagation(); setDragActive(false); if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]); };
  const handleFileChange = (e) => { if (e.target.files?.[0]) setFile(e.target.files[0]); };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('enhance_titles', enhanceTitles);
      if (mode === 'video' && videoHint.trim()) {
        formData.append('video_hint', videoHint.trim());
      }
      const res = mode === 'video' ? await uploadApi.uploadVideo(formData) : await uploadApi.uploadCsv(formData);
      const jobId = res.data.job_id;
      navigate(`/jobs/${jobId}`);
    } catch (e) {
      alert('Upload failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setUploading(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    setUploading(true);
    try {
      const csvHeader = 'sku_id,product_title,description,brand,category,price,mrp,image_url,product_url,color,size,material,availability';
      const csvRow = Object.values(manualProduct).map(v => `"${(v || '').replace(/"/g, '""')}"`).join(',');
      const blob = new Blob([csvHeader + '\n' + csvRow], { type: 'text/csv' });
      const formData = new FormData();
      formData.append('file', blob, 'manual_entry.csv');
      formData.append('enhance_titles', enhanceTitles);
      const res = await uploadApi.uploadCsv(formData);
      navigate(`/jobs/${res.data.job_id}`);
    } catch (e) {
      alert('Submit failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setUploading(false);
    }
  };

  const acceptTypes = mode === 'video' ? '.mp4,.avi,.mov,.mkv,.webm' : '.csv';
  const acceptLabel = mode === 'video' ? 'MP4, AVI, MOV, MKV, WebM — Max 50MB' : 'CSV — Max 10MB';

  return (
    <div className="upload-page">
      <div className="page-header"><h1 className="page-title">Upload Products</h1></div>

      <div className="upload-mode-tabs">
        {[{ key: 'video', label: 'Product Video', icon: Film }, { key: 'csv', label: 'Product CSV', icon: FileText }, { key: 'manual', label: 'Manual Entry', icon: Upload }].map(t => (
          <button key={t.key} className={`tab-btn ${mode === t.key ? 'active' : ''}`} onClick={() => { setMode(t.key); setFile(null); }}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {(mode === 'video' || mode === 'csv') && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">{mode === 'video' ? 'Upload Product Video' : 'Upload Product CSV'}</h3>
          </div>
          <div
            className={`upload-zone ${dragActive ? 'upload-zone-active' : ''} ${file ? 'upload-zone-has-file' : ''}`}
            onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input ref={fileInputRef} type="file" accept={acceptTypes} onChange={handleFileChange} style={{ display: 'none' }} />
            {file ? (
              <div className="upload-zone-file">
                <Check size={32} className="upload-zone-check" />
                <p className="upload-zone-filename">{file.name}</p>
                <p className="upload-zone-size">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                <button className="btn btn-sm btn-secondary" onClick={(e) => { e.stopPropagation(); setFile(null); }}>Remove</button>
              </div>
            ) : (
              <>
                <Upload size={40} className="upload-zone-icon" />
                <p className="upload-zone-text">Drag & drop your file here or click to browse</p>
                <p className="upload-zone-hint">{acceptLabel}</p>
              </>
            )}
          </div>

          {mode === 'video' && (
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="form-label" style={{ marginBottom: '0.5rem', display: 'block' }}>
                <span style={{ color: '#6366f1', marginRight: 6 }}>💡</span>
                What products are in this video? <span style={{ color: '#64748b', fontWeight: 400 }}>(optional but helps AI accuracy)</span>
              </label>
              <input
                className="form-input"
                type="text"
                placeholder="e.g. Razer gaming mouse on Redgear mousepad with RGB lighting"
                value={videoHint}
                onChange={e => setVideoHint(e.target.value)}
                style={{ fontSize: '0.875rem' }}
              />
              <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.4rem' }}>
                Describing the video content helps Gemini identify products accurately, especially for WhatsApp/generic filenames.
              </p>
            </div>
          )}

          <div className="enhance-toggle">
            <label className="toggle-label">
              <span>Enhance product titles using AI?</span>
              <div className={`toggle-switch ${enhanceTitles ? 'active' : ''}`} onClick={() => setEnhanceTitles(!enhanceTitles)}>
                <div className="toggle-knob" />
              </div>
            </label>
            <p className="toggle-hint">When enabled, AI will generate improved SEO-optimized titles using product attributes and trending keywords.</p>
          </div>

          <div className="upload-actions">
            <button className="btn btn-primary btn-lg" onClick={handleUpload} disabled={!file || uploading}>
              {uploading ? <><Loader2 size={18} className="spin" /> Processing...</> : <><Upload size={18} /> Start Processing</>}
            </button>
          </div>

          {mode === 'csv' && (
            <div className="sample-download">
              <p>Need a template? <a href="/sample_products.csv" download>Download sample product CSV</a></p>
            </div>
          )}
        </div>
      )}

      {mode === 'manual' && (
        <div className="card">
          <div className="card-header"><h3 className="card-title">Enter Product Details</h3></div>
          <form onSubmit={handleManualSubmit} className="manual-form">
            <div className="form-grid">
              {[
                { key: 'sku_id', label: 'SKU ID *', required: true },
                { key: 'product_title', label: 'Product Title' },
                { key: 'brand', label: 'Brand' },
                { key: 'category', label: 'Category' },
                { key: 'price', label: 'Price (₹)', type: 'number' },
                { key: 'mrp', label: 'MRP (₹)', type: 'number' },
                { key: 'color', label: 'Color' },
                { key: 'size', label: 'Size' },
                { key: 'material', label: 'Material' },
                { key: 'image_url', label: 'Image URL' },
                { key: 'product_url', label: 'Product URL' },
              ].map(f => (
                <div className="form-group" key={f.key}>
                  <label className="form-label">{f.label}</label>
                  <input className="form-input" type={f.type || 'text'} required={f.required} value={manualProduct[f.key]}
                    onChange={(e) => setManualProduct(p => ({ ...p, [f.key]: e.target.value }))} />
                </div>
              ))}
              <div className="form-group">
                <label className="form-label">Availability</label>
                <select className="form-select" value={manualProduct.availability}
                  onChange={(e) => setManualProduct(p => ({ ...p, availability: e.target.value }))}>
                  <option value="in_stock">In Stock</option>
                  <option value="out_of_stock">Out of Stock</option>
                </select>
              </div>
            </div>
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label className="form-label">Description</label>
              <textarea className="form-textarea" rows={3} value={manualProduct.description}
                onChange={(e) => setManualProduct(p => ({ ...p, description: e.target.value }))} />
            </div>

            <div className="enhance-toggle">
              <label className="toggle-label">
                <span>Enhance product title using AI?</span>
                <div className={`toggle-switch ${enhanceTitles ? 'active' : ''}`} onClick={() => setEnhanceTitles(!enhanceTitles)}>
                  <div className="toggle-knob" />
                </div>
              </label>
            </div>

            <div className="upload-actions">
              <button type="submit" className="btn btn-primary btn-lg" disabled={!manualProduct.sku_id || uploading}>
                {uploading ? <><Loader2 size={18} className="spin" /> Submitting...</> : 'Submit Product'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
