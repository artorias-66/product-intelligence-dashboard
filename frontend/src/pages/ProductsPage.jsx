import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Package, Search, ChevronLeft, ChevronRight, Download } from 'lucide-react';
import { productsApi } from '../api/client';

function scoreClass(score) {
  if (score >= 80) return 'quality-good';
  if (score >= 50) return 'quality-medium';
  return 'quality-bad';
}

export default function ProductsPage() {
  const [searchParams] = useSearchParams();
  const initialSearch = searchParams.get('search') || '';

  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(initialSearch);
  const [searchInput, setSearchInput] = useState(initialSearch);
  const [category, setCategory] = useState('');
  const [minScore, setMinScore] = useState('');
  const [maxScore, setMaxScore] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  useEffect(() => { loadProducts(); }, [page, search, category, minScore, maxScore, sortBy, sortOrder]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize, sort_by: sortBy, sort_order: sortOrder };
      if (search) params.search = search;
      if (category) params.category = category;
      if (minScore) params.min_score = parseFloat(minScore);
      if (maxScore) params.max_score = parseFloat(maxScore);
      const res = await productsApi.getAll(params);
      setProducts(res.data.products || []);
      setTotal(res.data.total || 0);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleSort = (field) => {
    if (sortBy === field) setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    else { setSortBy(field); setSortOrder('asc'); }
  };

  const totalPages = Math.ceil(total / pageSize);
  const formatPrice = (p) => p != null ? `₹${Number(p).toLocaleString('en-IN')}` : '—';

  const handleDownloadReport = () => {
    const baseUrl = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? 'https://product-intelligence-api-dkuo.onrender.com' : 'http://localhost:8000');
    window.location.href = `${baseUrl}/api/dashboard/quality-report-csv`;
  };

  return (
    <div className="products-page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Products</h1>
          <span className="text-secondary">{total} product{total !== 1 ? 's' : ''}</span>
        </div>
        <button className="btn btn-primary" onClick={handleDownloadReport}>
          <Download size={16} /> Download CSV Report
        </button>
      </div>

      <div className="filter-bar">
        <form className="search-form" onSubmit={handleSearch}>
          <div className="search-input-wrap">
            <Search size={16} />
            <input className="form-input" placeholder="Search by title or SKU..." value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)} />
          </div>
        </form>
        <div className="filter-group">
          <select className="filter-select" value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }}>
            <option value="">All Categories</option>
            {['Shoes', 'Dresses', 'Bags', 'Electronics', 'Watches'].map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="filter-select" value={`${minScore || ''}-${maxScore || ''}`} onChange={(e) => {
            const [min, max] = e.target.value.split('-');
            setMinScore(min); setMaxScore(max); setPage(1);
          }}>
            <option value="-">All Scores</option>
            <option value="80-100">Excellent (80-100)</option>
            <option value="50-79">Good (50-79)</option>
            <option value="0-49">Poor (0-49)</option>
          </select>
        </div>
      </div>

      {loading ? <div className="loading-spinner"><div className="spinner" /></div> : products.length === 0 ? (
        <div className="card"><div className="empty-state"><Package size={48} /><h3>No products found</h3><p>Try adjusting your filters or upload new products.</p></div></div>
      ) : (
        <>
          <div className="card table-card">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="sortable" onClick={() => handleSort('sku_id')}>SKU {sortBy === 'sku_id' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                  <th className="sortable" onClick={() => handleSort('product_title')}>Title {sortBy === 'product_title' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                  <th>Brand</th>
                  <th>Category</th>
                  <th className="sortable" onClick={() => handleSort('price')}>Price {sortBy === 'price' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                  <th>MRP</th>
                  <th className="sortable" onClick={() => handleSort('quality_score')}>Quality {sortBy === 'quality_score' && (sortOrder === 'asc' ? '↑' : '↓')}</th>
                  <th>Availability</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.id}>
                    <td className="font-mono">{p.sku_id}</td>
                    <td className="td-title">{p.product_title || <span className="text-danger">Missing</span>}</td>
                    <td>{p.brand || <span className="text-secondary">—</span>}</td>
                    <td><span className="badge-type">{p.category || '—'}</span></td>
                    <td className="font-mono">{formatPrice(p.price)}</td>
                    <td className="font-mono text-secondary">{formatPrice(p.mrp)}</td>
                    <td>
                      <span className={`quality-score ${scoreClass(p.quality_score || 0)}`}>
                        {(p.quality_score || 0).toFixed(0)}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${p.availability === 'in_stock' ? 'badge-completed' : 'badge-failed'}`}>
                        {p.availability === 'in_stock' ? 'In Stock' : 'Out of Stock'}
                      </span>
                    </td>
                    <td><Link to={`/products/${p.sku_id}`} className="btn btn-sm btn-primary">View</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <span className="pagination-info">Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}</span>
            <div className="pagination-controls">
              <button className="btn btn-sm btn-secondary" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                <ChevronLeft size={14} /> Prev
              </button>
              <span className="pagination-page">Page {page} of {totalPages}</span>
              <button className="btn btn-sm btn-secondary" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
