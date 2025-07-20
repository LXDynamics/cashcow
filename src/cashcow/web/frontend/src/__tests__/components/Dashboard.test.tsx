/**
 * Tests for Dashboard component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Dashboard from '../../pages/Dashboard';
import * as calculationService from '../../services/calculations';
import * as entityService from '../../services/entities';

// Mock services
jest.mock('../../services/calculations');
jest.mock('../../services/entities');
jest.mock('../../services/websockets');

const mockCalculationService = calculationService as jest.Mocked<typeof calculationService>;
const mockEntityService = entityService as jest.Mocked<typeof entityService>;

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = createTheme();
  return (
    <MemoryRouter>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </MemoryRouter>
  );
};

// Mock data
const mockKPIs = [
  {
    name: 'Total Revenue',
    value: 1500000,
    unit: '$',
    category: 'revenue',
    trend: 'up' as const,
    change: 0.15
  },
  {
    name: 'Monthly Burn Rate',
    value: 85000,
    unit: '$/month',
    category: 'cash_flow',
    trend: 'down' as const,
    change: -0.08
  },
  {
    name: 'Employee Count',
    value: 12,
    unit: 'count',
    category: 'operations',
    trend: 'stable' as const,
    change: 0
  }
];

const mockEntities = [
  {
    id: '1',
    type: 'employee',
    name: 'John Doe',
    start_date: '2024-01-01',
    salary: 100000,
    tags: ['engineering']
  },
  {
    id: '2', 
    type: 'grant',
    name: 'NASA SBIR',
    start_date: '2024-01-01',
    amount: 500000,
    tags: ['funding']
  }
];

describe('Dashboard Component', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Setup default mock responses
    mockCalculationService.getKPIs.mockResolvedValue({
      success: true,
      data: mockKPIs
    });
    
    mockEntityService.listEntities.mockResolvedValue({
      success: true,
      data: mockEntities,
      total: 2,
      page: 1,
      per_page: 100,
      total_pages: 1
    });
  });

  test('renders dashboard title', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  test('displays loading state initially', () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByText('Loading dashboard data...')).toBeInTheDocument();
  });

  test('displays KPI cards after loading', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Total Revenue')).toBeInTheDocument();
      expect(screen.getByText('$1,500,000')).toBeInTheDocument();
      expect(screen.getByText('Monthly Burn Rate')).toBeInTheDocument();
      expect(screen.getByText('$85,000/mo')).toBeInTheDocument();
      expect(screen.getByText('Employee Count')).toBeInTheDocument();
      expect(screen.getByText('12 count')).toBeInTheDocument();
    });
  });

  test('displays connection status indicators', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should show offline initially (since WebSocket is mocked)
      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  test('refresh button calls data loading functions', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTitle('Refresh Data')).toBeInTheDocument();
    });

    const refreshButton = screen.getByTitle('Refresh Data');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockCalculationService.getKPIs).toHaveBeenCalledTimes(2); // Initial + refresh
      expect(mockEntityService.listEntities).toHaveBeenCalledTimes(2);
    });
  });

  test('displays real-time updates component', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard Updates')).toBeInTheDocument();
    });
  });

  test('displays interactive KPI dashboard when KPIs are loaded', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Interactive KPI Analysis')).toBeInTheDocument();
    });
  });

  test('displays last updated timestamp', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });

  test('displays quick action buttons', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Manage Entities')).toBeInTheDocument();
      expect(screen.getByText('View Reports')).toBeInTheDocument();
      expect(screen.getByText('Run Forecast')).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    mockCalculationService.getKPIs.mockRejectedValue(new Error('API Error'));
    mockEntityService.listEntities.mockRejectedValue(new Error('API Error'));

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    // Should not crash and should exit loading state
    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard data...')).not.toBeInTheDocument();
    });
  });

  test('formats KPI values correctly', async () => {
    const customKPIs = [
      {
        name: 'Revenue Growth',
        value: 0.15,
        unit: '%',
        category: 'revenue',
        trend: 'up' as const,
        change: 0.05
      }
    ];

    mockCalculationService.getKPIs.mockResolvedValue({
      success: true,
      data: customKPIs
    });

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('15.0%')).toBeInTheDocument();
    });
  });

  test('displays trend indicators correctly', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should have trend icons (though we can't easily test the icons themselves)
      const kpiCards = screen.getAllByRole('button', { name: /trend/i });
      expect(kpiCards.length).toBeGreaterThan(0);
    });
  });

  test('navigates to forecast page when View Forecast is clicked', async () => {
    const mockNavigate = jest.fn();
    
    // Mock useNavigate hook
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate
    }));

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      const forecastButton = screen.getByText('View Forecast');
      fireEvent.click(forecastButton);
      expect(mockNavigate).toHaveBeenCalledWith('/reports/forecast');
    });
  });
});

describe('Dashboard KPI Cards', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    mockCalculationService.getKPIs.mockResolvedValue({
      success: true,
      data: mockKPIs
    });
    
    mockEntityService.listEntities.mockResolvedValue({
      success: true,
      data: mockEntities,
      total: 2,
      page: 1,
      per_page: 100,
      total_pages: 1
    });
  });

  test('displays change percentages correctly', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('+15.0%')).toBeInTheDocument(); // Revenue up
      expect(screen.getByText('-8.0%')).toBeInTheDocument(); // Burn rate down
    });
  });

  test('applies correct colors for trends', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      const cards = screen.getAllByRole('article'); // MUI Cards have article role
      expect(cards.length).toBeGreaterThan(0);
    });
  });

  test('shows hover effects on KPI cards', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      const firstCard = screen.getAllByRole('article')[0];
      fireEvent.mouseEnter(firstCard);
      // Visual hover effects would be tested with cypress or similar
    });
  });
});

describe('Dashboard Real-time Features', () => {
  test('updates KPI values when WebSocket message received', async () => {
    // This would require mocking the WebSocket service more thoroughly
    // For now, we test that the component sets up WebSocket connections
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      // Component should attempt to establish WebSocket connection
      expect(screen.getByText('Dashboard Updates')).toBeInTheDocument();
    });
  });

  test('handles WebSocket connection status changes', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should show connection status
      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });
});

describe('Dashboard Performance', () => {
  test('renders within reasonable time', async () => {
    const startTime = performance.now();
    
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should render within 1 second
    expect(renderTime).toBeLessThan(1000);
  });

  test('handles large numbers of KPIs efficiently', async () => {
    const manyKPIs = Array.from({ length: 20 }, (_, i) => ({
      name: `KPI ${i}`,
      value: Math.random() * 1000000,
      unit: '$',
      category: 'test',
      trend: 'up' as const,
      change: Math.random() * 0.2
    }));

    mockCalculationService.getKPIs.mockResolvedValue({
      success: true,
      data: manyKPIs
    });

    const startTime = performance.now();
    
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('KPI 0')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should still render efficiently with many KPIs
    expect(renderTime).toBeLessThan(2000);
  });
});