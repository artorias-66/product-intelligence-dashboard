import { useEffect, useState } from 'react';
import { useAuth } from '@clerk/clerk-react';
import api, { uploadClient } from '../../api/client';

export default function AxiosInterceptor({ children }) {
  const { getToken } = useAuth();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const requestInterceptor = async (config) => {
      try {
        const token = await getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch (err) {
        console.error("Error getting Clerk token:", err);
      }
      return config;
    };

    const apiInterceptorId = api.interceptors.request.use(requestInterceptor);
    const uploadInterceptorId = uploadClient.interceptors.request.use(requestInterceptor);

    setIsReady(true);

    return () => {
      api.interceptors.request.eject(apiInterceptorId);
      uploadClient.interceptors.request.eject(uploadInterceptorId);
    };
  }, [getToken]);

  if (!isReady) return null;

  return children;
}
