import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Log API URL in development for debugging
if (import.meta.env.DEV) {
  console.log('[API Client] Using API URL:', API_BASE_URL);
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add auth token to requests if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('curator_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Log errors in development
    if (import.meta.env.DEV) {
      console.error('[API Error]', {
        url: error.config?.url,
        fullURL: (error.config?.baseURL || '') + (error.config?.url || ''),
        method: error.config?.method,
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
        code: error.code,
        isNetworkError: !error.response,
      });
    }

    // Handle 401 by clearing token (session expired)
    if (error.response?.status === 401) {
      localStorage.removeItem('curator_token');
    }

    return Promise.reject(error);
  }
);
