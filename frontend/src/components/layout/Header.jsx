import { useLocation, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Search, Bell } from 'lucide-react';
import { alertsApi } from '../../api/client';
import { UserButton } from '@clerk/clerk-react';

const pageTitles = {
  '/': 'Dashboard',
  '/upload': 'Upload Data',
  '/jobs': 'Processing Jobs',
  '/products': 'Products',
  '/alerts': 'Alerts',
  '/competitor-prices': 'Competitor Prices',
};

function getBreadcrumbs(pathname) {
  const parts = pathname.split('/').filter(Boolean);
  const crumbs = [{ label: 'Home', path: '/' }];

  if (parts.length === 0) return crumbs;

  if (parts[0] === 'jobs') {
    crumbs.push({ label: 'Jobs', path: '/jobs' });
    if (parts[1]) crumbs.push({ label: `Job ${parts[1].slice(0, 8)}...`, path: pathname });
  } else if (parts[0] === 'products') {
    crumbs.push({ label: 'Products', path: '/products' });
    if (parts[1]) crumbs.push({ label: parts[1], path: pathname });
  } else {
    const title = pageTitles[`/${parts[0]}`] || parts[0];
    crumbs.push({ label: title, path: pathname });
  }

  return crumbs;
}

export default function Header() {
  const location = useLocation();
  const [unreadCount, setUnreadCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  const breadcrumbs = getBreadcrumbs(location.pathname);
  const pageTitle = pageTitles[location.pathname] || 'Detail';

  useEffect(() => {
    fetchUnread();
    const interval = setInterval(fetchUnread, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchUnread = async () => {
    try {
      const res = await alertsApi.getAll({ is_read: false, limit: 1 });
      const data = res.data;
      setUnreadCount(data.total ?? data.length ?? 0);
    } catch {
      // silently ignore
    }
  };


  return (
    <header className="header">
      <div className="header-left">
        <div>
          <h1 className="header-title">{pageTitle}</h1>
          <div className="header-breadcrumb">
            {breadcrumbs.map((crumb, i) => (
              <span key={i}>
                {i > 0 && <span className="separator"> / </span>}
                {i < breadcrumbs.length - 1 ? (
                  <Link to={crumb.path}>{crumb.label}</Link>
                ) : (
                  <span style={{ color: 'var(--text-secondary)' }}>{crumb.label}</span>
                )}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="header-right">
        <div className="header-search">
          <Search className="header-search-icon" size={16} />
          <input
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && searchQuery.trim()) {
                window.location.href = `/products?search=${encodeURIComponent(searchQuery.trim())}`;
              }
            }}
          />
        </div>


        <Link to="/alerts" className="header-notification">
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className="header-notification-badge">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Link>
        <UserButton />
      </div>
    </header>
  );
}
