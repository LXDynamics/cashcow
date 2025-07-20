// Base API service configuration

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse, ApiError } from '../types/api';

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000/ws';
const MOCK_MODE = process.env.REACT_APP_MOCK_MODE === 'true';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add request ID for tracking
    config.headers['X-Request-ID'] = generateRequestId();
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    
    // Transform error to standard format
    const apiError: ApiError = {
      code: error.response?.data?.code || error.code || 'UNKNOWN_ERROR',
      message: error.response?.data?.message || error.message || 'An unknown error occurred',
      details: error.response?.data?.details || {},
    };
    
    return Promise.reject(apiError);
  }
);

// Generic API methods
export const api = {
  // GET request
  get: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    if (MOCK_MODE) {
      return mockApiCall('GET', url, undefined, config);
    }
    
    try {
      const response = await apiClient.get<ApiResponse<T>>(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // POST request
  post: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    if (MOCK_MODE) {
      return mockApiCall('POST', url, data, config);
    }
    
    try {
      const response = await apiClient.post<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // PUT request
  put: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    if (MOCK_MODE) {
      return mockApiCall('PUT', url, data, config);
    }
    
    try {
      const response = await apiClient.put<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // DELETE request
  delete: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    if (MOCK_MODE) {
      return mockApiCall('DELETE', url, undefined, config);
    }
    
    try {
      const response = await apiClient.delete<ApiResponse<T>>(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // PATCH request
  patch: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    if (MOCK_MODE) {
      return mockApiCall('PATCH', url, data, config);
    }
    
    try {
      const response = await apiClient.patch<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};

// Mock API implementation for development
async function mockApiCall(
  method: string, 
  url: string, 
  data?: any, 
  config?: AxiosRequestConfig
): Promise<ApiResponse<any>> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 700));
  
  // Simulate occasional errors (5% chance)
  if (Math.random() < 0.05) {
    throw new Error('Simulated network error');
  }
  
  // Route to appropriate mock handler
  if (url.includes('/entities')) {
    return handleEntitiesMock(method, url, data);
  } else if (url.includes('/forecast')) {
    return handleForecastMock(method, url, data);
  } else if (url.includes('/kpis')) {
    return handleKPIsMock(method, url, data);
  } else if (url.includes('/reports')) {
    return handleReportsMock(method, url, data);
  } else if (url.includes('/scenarios')) {
    return handleScenariosMock(method, url, data);
  }
  
  // Default response
  return {
    success: true,
    data: null,
    message: `Mock ${method} ${url} completed successfully`
  };
}

// Mock handlers (basic implementations)
function handleEntitiesMock(method: string, url: string, data?: any): any {
  if (method === 'GET' && url === '/entities') {
    return {
      success: true,
      data: [], // Will be filled by mock data service
      total: 0,
      page: 1,
      per_page: 10,
      total_pages: 0
    };
  }
  
  return { success: true, data: null };
}

function handleForecastMock(method: string, url: string, data?: any): ApiResponse<any> {
  return {
    success: true,
    data: {
      months: [],
      summary: {
        total_revenue: 0,
        total_expenses: 0,
        net_cash_flow: 0,
        average_burn_rate: 0,
        runway_months: 0
      }
    }
  };
}

function handleKPIsMock(method: string, url: string, data?: any): ApiResponse<any> {
  return {
    success: true,
    data: []
  };
}

function handleReportsMock(method: string, url: string, data?: any): any {
  return {
    success: true,
    data: null,
    report_url: '/mock-report.html'
  };
}

function handleScenariosMock(method: string, url: string, data?: any): ApiResponse<any> {
  return {
    success: true,
    data: []
  };
}

// Utility functions
function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Export configuration
export { API_BASE_URL, WS_BASE_URL, MOCK_MODE };
export default apiClient;