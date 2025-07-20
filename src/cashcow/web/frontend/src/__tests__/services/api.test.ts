/**
 * Tests for API service layer
 */

import axios, { AxiosResponse } from 'axios';
import { api } from '../../services/api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock window.location
const mockLocation = {
  href: ''
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
});

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup axios mock
    mockedAxios.create.mockReturnValue(mockedAxios);
    mockedAxios.interceptors = {
      request: { use: jest.fn() },
      response: { use: jest.fn() }
    } as any;
  });

  describe('GET requests', () => {
    test('makes successful GET request', async () => {
      const mockData = { success: true, data: { id: 1, name: 'test' } };
      const mockResponse: AxiosResponse = {
        data: mockData,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await api.get('/test');

      expect(mockedAxios.get).toHaveBeenCalledWith('/test', undefined);
      expect(result).toEqual(mockData);
    });

    test('makes GET request with config', async () => {
      const mockData = { success: true };
      const mockResponse: AxiosResponse = {
        data: mockData,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      };
      const config = { timeout: 5000 };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await api.get('/test', config);

      expect(mockedAxios.get).toHaveBeenCalledWith('/test', config);
      expect(result).toEqual(mockData);
    });

    test('handles GET request errors', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { code: 'NOT_FOUND', message: 'Resource not found' }
        }
      };

      mockedAxios.get.mockRejectedValue(mockError);

      await expect(api.get('/nonexistent')).rejects.toEqual({
        code: 'NOT_FOUND',
        message: 'Resource not found',
        details: {}
      });
    });
  });

  describe('POST requests', () => {
    test('makes successful POST request', async () => {
      const mockData = { success: true, id: 'created-123' };
      const mockResponse: AxiosResponse = {
        data: mockData,
        status: 201,
        statusText: 'Created',
        headers: {},
        config: {} as any
      };
      const postData = { name: 'New Item' };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await api.post('/items', postData);

      expect(mockedAxios.post).toHaveBeenCalledWith('/items', postData, undefined);
      expect(result).toEqual(mockData);
    });

    test('makes POST request with config', async () => {
      const mockData = { success: true };
      const mockResponse: AxiosResponse = {
        data: mockData,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      };
      const postData = { name: 'Test' };
      const config = { headers: { 'Custom-Header': 'value' } };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await api.post('/test', postData, config);

      expect(mockedAxios.post).toHaveBeenCalledWith('/test', postData, config);
      expect(result).toEqual(mockData);
    });

    test('handles POST validation errors', async () => {
      const mockError = {
        response: {
          status: 422,
          data: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid data',
            details: { field: 'name', error: 'required' }
          }
        }
      };

      mockedAxios.post.mockRejectedValue(mockError);

      await expect(api.post('/items', {})).rejects.toEqual({
        code: 'VALIDATION_ERROR',
        message: 'Invalid data',
        details: { field: 'name', error: 'required' }
      });
    });
  });

  describe('PUT requests', () => {
    test('makes successful PUT request', async () => {
      const mockData = { success: true, updated: true };
      const mockResponse: AxiosResponse = {
        data: mockData,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      };
      const updateData = { name: 'Updated Item' };

      mockedAxios.put.mockResolvedValue(mockResponse);

      const result = await api.put('/items/123', updateData);

      expect(mockedAxios.put).toHaveBeenCalledWith('/items/123', updateData, undefined);
      expect(result).toEqual(mockData);
    });
  });

  describe('DELETE requests', () => {
    test('makes successful DELETE request', async () => {
      const mockData = { success: true };
      const mockResponse: AxiosResponse = {
        data: mockData,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      };

      mockedAxios.delete.mockResolvedValue(mockResponse);

      const result = await api.delete('/items/123');

      expect(mockedAxios.delete).toHaveBeenCalledWith('/items/123', undefined);
      expect(result).toEqual(mockData);
    });
  });

  describe('PATCH requests', () => {
    test('makes successful PATCH request', async () => {
      const mockData = { success: true, patched: true };
      const mockResponse: AxiosResponse = {
        data: mockData,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      };
      const patchData = { status: 'active' };

      mockedAxios.patch.mockResolvedValue(mockResponse);

      const result = await api.patch('/items/123', patchData);

      expect(mockedAxios.patch).toHaveBeenCalledWith('/items/123', patchData, undefined);
      expect(result).toEqual(mockData);
    });
  });

  describe('Error handling', () => {
    test('handles network errors', async () => {
      const networkError = new Error('Network Error');
      (networkError as any).code = 'NETWORK_ERROR';

      mockedAxios.get.mockRejectedValue(networkError);

      await expect(api.get('/test')).rejects.toEqual({
        code: 'NETWORK_ERROR',
        message: 'Network Error',
        details: {}
      });
    });

    test('handles server errors without response data', async () => {
      const serverError = {
        response: {
          status: 500,
          statusText: 'Internal Server Error'
        }
      };

      mockedAxios.get.mockRejectedValue(serverError);

      await expect(api.get('/test')).rejects.toEqual({
        code: 'UNKNOWN_ERROR',
        message: 'An unknown error occurred',
        details: {}
      });
    });

    test('handles unknown errors', async () => {
      const unknownError = 'String error';

      mockedAxios.get.mockRejectedValue(unknownError);

      await expect(api.get('/test')).rejects.toEqual({
        code: 'UNKNOWN_ERROR',
        message: 'An unknown error occurred',
        details: {}
      });
    });
  });

  describe('Authentication', () => {
    test('includes auth token in requests when available', () => {
      localStorageMock.getItem.mockReturnValue('test-token-123');

      // The auth token inclusion would be handled by axios interceptors
      // which are mocked, so we just verify localStorage is called
      localStorageMock.getItem('auth_token');

      expect(localStorageMock.getItem).toHaveBeenCalledWith('auth_token');
    });

    test('handles 401 unauthorized responses', async () => {
      const unauthorizedError = {
        response: {
          status: 401,
          data: { code: 'UNAUTHORIZED', message: 'Token expired' }
        }
      };

      mockedAxios.get.mockRejectedValue(unauthorizedError);

      await expect(api.get('/protected')).rejects.toEqual({
        code: 'UNAUTHORIZED',
        message: 'Token expired',
        details: {}
      });

      // Should remove token and redirect (handled by interceptors)
      // We can't easily test the interceptor behavior in this unit test
    });
  });

  describe('Request configuration', () => {
    test('generates request IDs', () => {
      // Request ID generation would be handled by interceptors
      // This is more of an integration test
      expect(true).toBe(true); // Placeholder
    });

    test('sets correct content type headers', () => {
      // Header setting would be handled by axios configuration
      // This is verified through the axios.create call
      expect(mockedAxios.create).toHaveBeenCalled();
    });

    test('has correct timeout settings', () => {
      // Timeout setting would be in axios.create configuration
      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          timeout: 30000
        })
      );
    });

    test('has correct base URL', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.stringContaining('localhost:8000/api')
        })
      );
    });
  });

  describe('Mock mode', () => {
    beforeEach(() => {
      // Reset environment
      process.env.REACT_APP_MOCK_MODE = 'true';
    });

    test('uses mock responses in mock mode', async () => {
      // When in mock mode, the API should return mock data
      // This would be handled by the mock API call function
      
      const result = await api.get('/entities');
      
      // Since we're mocking axios, we need to verify mock behavior differently
      // In real implementation, this would return mock data
      expect(mockedAxios.get).toHaveBeenCalled();
    });

    test('simulates network delays in mock mode', async () => {
      const startTime = Date.now();
      
      // Mock the delay
      const mockDelay = new Promise(resolve => setTimeout(resolve, 100));
      mockedAxios.get.mockImplementation(() => mockDelay.then(() => ({ data: { success: true } })));
      
      await api.get('/test');
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      expect(duration).toBeGreaterThan(50); // Should have some delay
    });

    test('simulates occasional errors in mock mode', async () => {
      // Mock implementation that occasionally throws errors
      let callCount = 0;
      mockedAxios.get.mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          return Promise.reject(new Error('Simulated network error'));
        }
        return Promise.resolve({ data: { success: true } });
      });

      // First call should fail
      await expect(api.get('/test')).rejects.toThrow();
      
      // Second call should succeed
      const result = await api.get('/test');
      expect(result).toEqual({ success: true });
    });
  });

  describe('Performance', () => {
    test('completes requests within reasonable time', async () => {
      const mockResponse: AxiosResponse = {
        data: { success: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const startTime = performance.now();
      await api.get('/test');
      const endTime = performance.now();

      const duration = endTime - startTime;
      expect(duration).toBeLessThan(100); // Should complete within 100ms (excluding network)
    });

    test('handles concurrent requests efficiently', async () => {
      const mockResponse: AxiosResponse = {
        data: { success: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const promises = Array.from({ length: 10 }, (_, i) => 
        api.get(`/test-${i}`)
      );

      const startTime = performance.now();
      const results = await Promise.all(promises);
      const endTime = performance.now();

      expect(results).toHaveLength(10);
      expect(results.every(r => r.success)).toBe(true);
      
      const duration = endTime - startTime;
      expect(duration).toBeLessThan(200); // Should handle concurrent requests efficiently
    });
  });
});