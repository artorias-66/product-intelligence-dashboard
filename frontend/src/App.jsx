import { Routes, Route } from 'react-router-dom';
import { SignedIn, SignedOut, RedirectToSignIn } from '@clerk/clerk-react';
import AxiosInterceptor from './components/auth/AxiosInterceptor';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import JobsPage from './pages/JobsPage';
import JobDetailPage from './pages/JobDetailPage';
import ProductsPage from './pages/ProductsPage';
import ProductDetailPage from './pages/ProductDetailPage';
import AlertsPage from './pages/AlertsPage';
import CompetitorPricesPage from './pages/CompetitorPricesPage';

function App() {
  return (
    <>
      <SignedIn>
        <AxiosInterceptor>
          <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/jobs/:id" element={<JobDetailPage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/products/:id" element={<ProductDetailPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/competitor-prices" element={<CompetitorPricesPage />} />
          </Route>
        </Routes>
        </AxiosInterceptor>
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  );
}

export default App;
