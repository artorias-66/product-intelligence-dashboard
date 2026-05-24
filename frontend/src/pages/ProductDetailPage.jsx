import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { RefreshCw, Sparkles, AlertTriangle, TrendingDown, TrendingUp, Minus, ArrowRight, Loader2 } from 'lucide-react';
import { productsApi } from '../api/client';
import { competitorApi } from '../api/client';

const PLATFORM_COLORS = { Amazon: '#ff9900', Myntra: '#ff3f6c', Ajio: '#3880ff', 'Nykaa Fashion': '#fc2779', 'Tata Cliq': '#f0f', Meesho: '#570a57', Flipkart: '#2874f0', 'Our Price': '#22c55e' };

function formatPrice(p) { return p != null ? `₹${Number(p).toLocaleString('en-IN')}` : '—'; }
function scoreClass(s) { return s >= 80 ? 'quality-good' : s >= 50 ? 'quality-medium' : 'quality-bad'; }

export default function ProductDetailPage() {
  const { id: skuId } = useParams();
  const [product, setProduct] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enhancing, setEnhancing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => { loadProduct(); }, [skuId]);

  const loadProduct = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [res, historyRes, recRes] = await Promise.all([
        productsApi.getById(skuId),
        competitorApi.getPriceHistory(skuId),
        productsApi.getRecommendations(skuId)
      ]);
      setProduct(res.data);
      setPriceHistory(historyRes.data);
      setRecommendations(recRes.data);
    } catch (e) { console.error(e); }
    finally { if (!silent) setLoading(false); }
  };

  const handleEnhanceTitle = async () => {
    setEnhancing(true);
    try {
      await productsApi.enhanceTitle(skuId);
      await loadProduct();
    } catch (e) { alert('Enhancement failed: ' + (e.response?.data?.detail || e.message)); }
    finally { setEnhancing(false); }
  };

  const handleRefreshPrices = async () => {
    setRefreshing(true);
    try {
      await competitorApi.refreshForProduct(skuId);
      await loadProduct(true);
    } catch (e) { console.error(e); }
    finally { setRefreshing(false); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!product) return <div className="card"><div className="empty-state"><h3>Product not found</h3></div></div>;

  const p = product;
  const issues = p.issues || [];
  const enhancedTitles = p.enhanced_titles || [];
  const latestEnhanced = enhancedTitles.length > 0 ? enhancedTitles[enhancedTitles.length - 1] : null;
  const competitors = p.competitor_prices || [];

  // Compute price summary
  const compPrices = competitors.map(c => c.competitor_price).filter(Boolean);
  const lowest = compPrices.length ? Math.min(...compPrices) : null;
  const highest = compPrices.length ? Math.max(...compPrices) : null;
  const average = compPrices.length ? compPrices.reduce((a, b) => a + b, 0) / compPrices.length : null;
  const priceGap = lowest != null && p.price ? p.price - lowest : null;
  const priceGapPct = lowest != null && p.price ? ((p.price - lowest) / lowest * 100) : null;
  const recommendation = priceGapPct > 10 ? 'Lower Price' : priceGapPct > 0 ? 'Price Competitive' : 'Well Priced';
  const recColor = priceGapPct > 10 ? '#ef4444' : priceGapPct > 0 ? '#f59e0b' : '#22c55e';

  // Prep price history chart data
  const historyMap = {};
  priceHistory.forEach(h => {
    const date = new Date(h.checked_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    if (!historyMap[date]) historyMap[date] = { date };
    historyMap[date][h.platform] = h.price;
  });
  const chartData = Object.values(historyMap).sort((a, b) => new Date(a.date) - new Date(b.date));
  const platforms = [...new Set(priceHistory.map(h => h.platform))];

  const fields = [
    { label: 'SKU ID', value: p.sku_id },
    { label: 'Brand', value: p.brand },
    { label: 'Category', value: p.category },
    { label: 'Price', value: formatPrice(p.price) },
    { label: 'MRP', value: formatPrice(p.mrp) },
    { label: 'Availability', value: p.availability?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) },
    { label: 'Color', value: p.color },
    { label: 'Size', value: p.size },
    { label: 'Material', value: p.material },
  ];

  return (
    <div className="product-detail-page">
      <div className="breadcrumb">
        <Link to="/products">Products</Link> <span>/</span> <span>{p.sku_id}</span>
      </div>

      <div className="page-header">
        <div>
          <h1 className="page-title">{p.product_title || 'Untitled Product'}</h1>
          <span className="text-secondary">{p.sku_id} · {p.category}</span>
        </div>
        <span className={`quality-score quality-score-lg ${scoreClass(p.quality_score || 0)}`}>
          {(p.quality_score || 0).toFixed(0)}
        </span>
      </div>

      <div className="detail-grid">
        <div className="detail-left">
          {/* Product Info */}
          <div className="card">
            <div className="card-header"><h3 className="card-title">Product Information</h3></div>
            <div className="info-grid">
              {fields.map(f => (
                <div key={f.label} className="info-item">
                  <span className="info-label">{f.label}</span>
                  <span className="info-value">{f.value || <span className="text-secondary">—</span>}</span>
                </div>
              ))}
            </div>
            {p.description && (
              <div className="info-description">
                <span className="info-label">Description</span>
                <p className="info-value">{p.description}</p>
              </div>
            )}
          </div>

          {/* Enhanced Title */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title"><Sparkles size={16} /> Enhanced Title</h3>
              <button className="btn btn-sm btn-primary" onClick={handleEnhanceTitle} disabled={enhancing}>
                {enhancing ? <><Loader2 size={14} className="spin" /> Generating...</> : <><Sparkles size={14} /> {latestEnhanced ? 'Regenerate' : 'Generate'}</>}
              </button>
            </div>
            {latestEnhanced ? (
              <div className="enhanced-title-section">
                <div className="enhanced-title-comparison">
                  <div className="title-box title-original">
                    <span className="title-box-label">Original</span>
                    <p>{latestEnhanced.original_title || p.product_title || '—'}</p>
                  </div>
                  <ArrowRight size={20} className="title-arrow" />
                  <div className="title-box title-enhanced">
                    <span className="title-box-label">Enhanced</span>
                    <p>{latestEnhanced.enhanced_title}</p>
                  </div>
                </div>
                {latestEnhanced.extracted_attributes && (
                  <div className="title-tags">
                    <span className="title-tags-label">Attributes:</span>
                    {Object.entries(latestEnhanced.extracted_attributes).map(([k, v]) => (
                      <span key={k} className="tag tag-primary">{k}: {v}</span>
                    ))}
                  </div>
                )}
                {latestEnhanced.suggested_keywords && (
                  <div className="title-tags">
                    <span className="title-tags-label">Keywords:</span>
                    {(Array.isArray(latestEnhanced.suggested_keywords) ? latestEnhanced.suggested_keywords : []).map((kwObj, i) => {
                      const kw = typeof kwObj === 'string' ? kwObj : kwObj.keyword;
                      const score = typeof kwObj === 'string' ? null : kwObj.trend_score;
                      return (
                        <span key={i} className="tag tag-success" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          {kw} {score && <span style={{ fontSize: '0.7rem', opacity: 0.8 }}>(🔥 {score})</span>}
                        </span>
                      );
                    })}
                  </div>
                )}
                {latestEnhanced.reason && <p className="enhancement-reason">{latestEnhanced.reason}</p>}
              </div>
            ) : (
              <div className="empty-state-sm"><p>Click "Generate" to create an AI-enhanced title.</p></div>
            )}
          </div>
        </div>

        <div className="detail-right">
          {/* Issues */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Listing Issues</h3>
              <span className="badge">{issues.length} issue{issues.length !== 1 ? 's' : ''}</span>
            </div>
            {issues.length > 0 ? (
              <div className="issues-list">
                {issues.map(issue => (
                  <div key={issue.id} className="issue-item">
                    <span className={`badge badge-${issue.severity.toLowerCase()}`}>{issue.severity}</span>
                    <div className="issue-content">
                      <span className="issue-message">{issue.message}</span>
                      {issue.suggested_fix && <span className="issue-fix">💡 {issue.suggested_fix}</span>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state-sm"><p>No issues found. This product listing looks good! ✅</p></div>
            )}
          </div>

          {/* Competitor Prices */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Competitor Prices</h3>
              <button className="btn btn-sm btn-secondary" onClick={handleRefreshPrices} disabled={refreshing}>
                {refreshing ? <Loader2 size={14} className="spin" /> : <RefreshCw size={14} />} Refresh
              </button>
            </div>
            {competitors.length > 0 ? (
              <>
                <table className="data-table">
                  <thead>
                    <tr><th>Platform</th><th>Price</th><th>Gap</th><th>Last Checked</th></tr>
                  </thead>
                  <tbody>
                    {competitors.map(c => {
                      const gap = p.price ? c.competitor_price - p.price : 0;
                      return (
                        <tr key={c.id}>
                          <td>
                            <span className="platform-dot" style={{ backgroundColor: PLATFORM_COLORS[c.platform] || '#6366f1' }} />
                            {c.platform}
                          </td>
                          <td className="font-mono">{formatPrice(c.competitor_price)}</td>
                          <td className="font-mono" style={{ color: gap < 0 ? '#22c55e' : gap > 0 ? '#ef4444' : '#94a3b8' }}>
                            {gap < 0 ? <TrendingDown size={12} /> : gap > 0 ? <TrendingUp size={12} /> : <Minus size={12} />}
                            {' '}{formatPrice(Math.abs(gap))}
                          </td>
                          <td className="text-secondary">{new Date(c.last_checked_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <div className="price-summary">
                  <div className="price-summary-item"><span>Our Price (Flipkart)</span><span className="font-mono">{formatPrice(p.price)}</span></div>
                  <div className="price-summary-item"><span>Lowest Competitor</span><span className="font-mono" style={{ color: '#22c55e' }}>{formatPrice(lowest)}</span></div>
                  <div className="price-summary-item"><span>Highest Competitor</span><span className="font-mono" style={{ color: '#ef4444' }}>{formatPrice(highest)}</span></div>
                  <div className="price-summary-item"><span>Average</span><span className="font-mono">{formatPrice(average?.toFixed(0))}</span></div>
                  {priceGap != null && (
                    <div className="price-summary-item"><span>Price Gap</span><span className="font-mono" style={{ color: recColor }}>{formatPrice(priceGap)} ({priceGapPct?.toFixed(1)}%)</span></div>
                  )}
                  <div className="price-summary-action">
                    <span className="badge" style={{ backgroundColor: recColor + '20', color: recColor }}>{recommendation}</span>
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-state-sm"><p>No competitor prices available.</p></div>
            )}
          </div>

          {/* Price History Chart */}
          {chartData.length > 0 && (
            <div className="card">
              <div className="card-header"><h3 className="card-title">Price History</h3></div>
              <div className="chart-container" style={{ height: 280 }}>
                <ResponsiveContainer>
                  <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={v => `₹${v}`} />
                    <Tooltip contentStyle={{ backgroundColor: '#1a1d27', border: '1px solid #334155', borderRadius: 8, color: '#f1f5f9' }}
                      formatter={(val) => [`₹${Number(val).toLocaleString('en-IN')}`, '']} />
                    <Legend wrapperStyle={{ color: '#94a3b8' }} />
                    {platforms.map(pl => (
                      <Line key={pl} type="monotone" dataKey={pl} stroke={PLATFORM_COLORS[pl] || '#6366f1'} strokeWidth={2} dot={false} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          {/* Recommendations */}
          <div className="card">
            <div className="card-header"><h3 className="card-title">Similar Products</h3></div>
            {recommendations.length === 0 ? (
              <div className="empty-state-sm">No similar products found.</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                {recommendations.map(r => (
                  <Link to={`/products/${r.sku_id}`} key={r.sku_id} className="card" style={{ padding: '1rem', textDecoration: 'none', color: 'inherit' }}>
                    <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{r.product_title || r.sku_id}</div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{r.brand || 'No Brand'} · {r.category || 'No Category'}</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: '500' }}>{formatPrice(r.price)}</span>
                      <span className={`quality-score ${scoreClass(r.quality_score || 0)}`} style={{ fontSize: '0.875rem', padding: '2px 6px' }}>{(r.quality_score || 0).toFixed(0)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
