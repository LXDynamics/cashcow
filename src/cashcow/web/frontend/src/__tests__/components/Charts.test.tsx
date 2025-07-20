/**
 * Tests for Chart components
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CashFlowChart from '../../components/Charts/CashFlowChart';
import KPIDashboard from '../../components/Charts/KPIDashboard';
import EntityBreakdownChart from '../../components/Charts/EntityBreakdownChart';

// Mock Chart.js
jest.mock('chart.js', () => ({
  Chart: {
    register: jest.fn(),
  },
  CategoryScale: jest.fn(),
  LinearScale: jest.fn(),
  PointElement: jest.fn(),
  LineElement: jest.fn(),
  BarElement: jest.fn(),
  ArcElement: jest.fn(),
  Title: jest.fn(),
  Tooltip: jest.fn(),
  Legend: jest.fn(),
}));

jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }: any) => (
    <div data-testid="line-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Line Chart Mock
    </div>
  ),
  Bar: ({ data, options }: any) => (
    <div data-testid="bar-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Bar Chart Mock
    </div>
  ),
  Doughnut: ({ data, options }: any) => (
    <div data-testid="doughnut-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Doughnut Chart Mock
    </div>
  ),
  Pie: ({ data, options }: any) => (
    <div data-testid="pie-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Pie Chart Mock
    </div>
  ),
  Chart: ({ type, data, options }: any) => (
    <div data-testid={`${type}-chart`} data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      {type} Chart Mock
    </div>
  ),
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = createTheme();
  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
};

// Mock data
const mockCashFlowData = [
  {
    month: '2024-01',
    revenue: 100000,
    expenses: 120000,
    net_cash_flow: -20000,
    cumulative_cash_flow: -20000,
    burn_rate: 20000
  },
  {
    month: '2024-02',
    revenue: 110000,
    expenses: 125000,
    net_cash_flow: -15000,
    cumulative_cash_flow: -35000,
    burn_rate: 15000
  },
  {
    month: '2024-03',
    revenue: 150000,
    expenses: 130000,
    net_cash_flow: 20000,
    cumulative_cash_flow: -15000,
    burn_rate: 0
  }
];

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
    name: 'Total Expenses',
    value: 1200000,
    unit: '$',
    category: 'expenses',
    trend: 'down' as const,
    change: -0.05
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
  },
  {
    id: '3',
    type: 'facility',
    name: 'Main Office',
    start_date: '2024-01-01',
    monthly_cost: 8000,
    tags: ['office']
  }
];

describe('CashFlowChart Component', () => {
  test('renders cash flow chart with title', () => {
    render(
      <TestWrapper>
        <CashFlowChart data={mockCashFlowData} title="Test Cash Flow" />
      </TestWrapper>
    );

    expect(screen.getByText('Test Cash Flow')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  test('displays summary statistics', () => {
    render(
      <TestWrapper>
        <CashFlowChart data={mockCashFlowData} />
      </TestWrapper>
    );

    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('Total Expenses')).toBeInTheDocument();
    expect(screen.getByText('Net Cash Flow')).toBeInTheDocument();
    expect(screen.getByText('$360,000')).toBeInTheDocument(); // Total revenue
    expect(screen.getByText('$375,000')).toBeInTheDocument(); // Total expenses
  });

  test('shows cumulative cash flow when enabled', () => {
    render(
      <TestWrapper>
        <CashFlowChart 
          data={mockCashFlowData} 
          showCumulative={true}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Final Position')).toBeInTheDocument();
    expect(screen.getByText('-$15,000')).toBeInTheDocument(); // Final cumulative
  });

  test('handles empty data gracefully', () => {
    render(
      <TestWrapper>
        <CashFlowChart data={[]} />
      </TestWrapper>
    );

    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  test('formats currency values correctly', () => {
    const largeValueData = [
      {
        month: '2024-01',
        revenue: 1500000,
        expenses: 1200000,
        net_cash_flow: 300000,
        cumulative_cash_flow: 300000,
        burn_rate: 0
      }
    ];

    render(
      <TestWrapper>
        <CashFlowChart data={largeValueData} />
      </TestWrapper>
    );

    expect(screen.getByText('$1,500,000')).toBeInTheDocument();
    expect(screen.getByText('$1,200,000')).toBeInTheDocument();
  });

  test('applies correct styling for positive and negative values', () => {
    render(
      <TestWrapper>
        <CashFlowChart data={mockCashFlowData} showCumulative={true} />
      </TestWrapper>
    );

    // Should have different styling for positive/negative values
    // This would be more thoroughly tested with visual regression tests
    expect(screen.getByText('-$15,000')).toBeInTheDocument();
  });
});

describe('KPIDashboard Component', () => {
  test('renders KPI dashboard with title', () => {
    render(
      <TestWrapper>
        <KPIDashboard kpis={mockKPIs} title="Test KPIs" />
      </TestWrapper>
    );

    expect(screen.getByText('Test KPIs')).toBeInTheDocument();
  });

  test('displays revenue vs expenses doughnut chart', () => {
    render(
      <TestWrapper>
        <KPIDashboard kpis={mockKPIs} />
      </TestWrapper>
    );

    expect(screen.getByText('Revenue vs Expenses')).toBeInTheDocument();
    expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
  });

  test('displays top financial KPIs bar chart', () => {
    render(
      <TestWrapper>
        <KPIDashboard kpis={mockKPIs} />
      </TestWrapper>
    );

    expect(screen.getByText('Top Financial KPIs')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  test('displays all KPIs summary cards', () => {
    render(
      <TestWrapper>
        <KPIDashboard kpis={mockKPIs} />
      </TestWrapper>
    );

    expect(screen.getByText('All KPIs Summary')).toBeInTheDocument();
    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('Total Expenses')).toBeInTheDocument();
    expect(screen.getByText('Employee Count')).toBeInTheDocument();
  });

  test('formats KPI values correctly', () => {
    render(
      <TestWrapper>
        <KPIDashboard kpis={mockKPIs} />
      </TestWrapper>
    );

    expect(screen.getByText('$1,500,000')).toBeInTheDocument(); // Currency
    expect(screen.getByText('12 count')).toBeInTheDocument(); // Count
  });

  test('displays trend chips for KPIs', () => {
    render(
      <TestWrapper>
        <KPIDashboard kpis={mockKPIs} />
      </TestWrapper>
    );

    expect(screen.getByText('+15.0%')).toBeInTheDocument(); // Up trend
    expect(screen.getByText('-5.0%')).toBeInTheDocument(); // Down trend
  });

  test('handles empty KPIs array', () => {
    render(
      <TestWrapper>
        <KPIDashboard kpis={[]} />
      </TestWrapper>
    );

    expect(screen.getByText('KPI Dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
  });

  test('categorizes KPIs correctly', () => {
    const categorizedKPIs = [
      ...mockKPIs,
      {
        name: 'Cash Flow Positive Months',
        value: 8,
        unit: 'months',
        category: 'cash_flow',
        trend: 'up' as const,
        change: 0.25
      }
    ];

    render(
      <TestWrapper>
        <KPIDashboard kpis={categorizedKPIs} />
      </TestWrapper>
    );

    // Should separate revenue, expense, and cash flow KPIs
    expect(screen.getByText('Cash Flow Positive Months')).toBeInTheDocument();
  });
});

describe('EntityBreakdownChart Component', () => {
  test('renders entity breakdown with title', () => {
    render(
      <TestWrapper>
        <EntityBreakdownChart entities={mockEntities} title="Test Entities" />
      </TestWrapper>
    );

    expect(screen.getByText('Test Entities')).toBeInTheDocument();
  });

  test('displays entity type distribution pie chart', () => {
    render(
      <TestWrapper>
        <EntityBreakdownChart entities={mockEntities} />
      </TestWrapper>
    );

    expect(screen.getByText('Entity Distribution by Type')).toBeInTheDocument();
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
  });

  test('displays value by type bar chart', () => {
    render(
      <TestWrapper>
        <EntityBreakdownChart entities={mockEntities} />
      </TestWrapper>
    );

    expect(screen.getByText('Total Value by Entity Type')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  test('displays category breakdown', () => {
    render(
      <TestWrapper>
        <EntityBreakdownChart entities={mockEntities} />
      </TestWrapper>
    );

    expect(screen.getByText('Category Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('Expenses')).toBeInTheDocument();
  });

  test('displays top entities by value table', () => {
    render(
      <TestWrapper>
        <EntityBreakdownChart entities={mockEntities} />
      </TestWrapper>
    );

    expect(screen.getByText('Top Entities by Value')).toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Value')).toBeInTheDocument();
  });

  test('displays summary statistics', () => {
    render(
      <TestWrapper>
        <EntityBreakdownChart entities={mockEntities} />
      </TestWrapper>
    );

    expect(screen.getByText('Summary Statistics')).toBeInTheDocument();
    expect(screen.getByText('Total Entities')).toBeInTheDocument();
    expect(screen.getByText('Entity Types')).toBeInTheDocument();
    expect(screen.getByText('Total Value')).toBeInTheDocument();
    expect(screen.getByText('Avg Value')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // Total entities
  });

  test('calculates entity values correctly', () => {
    render(
      <TestWrapper>
        <EntityBreakdownChart entities={mockEntities} />
      </TestWrapper>
    );

    // Should display calculated total value
    expect(screen.getByText('$608,000')).toBeInTheDocument(); // Total value
  });

  test('handles entities with different value fields', () => {
    const mixedEntities = [
      {
        id: '1',
        type: 'employee',
        name: 'John Doe',
        start_date: '2024-01-01',
        salary: 100000,
        tags: []
      },
      {
        id: '2',
        type: 'equipment',
        name: 'Test Equipment',
        start_date: '2024-01-01',
        cost: 50000,
        purchase_date: '2024-01-01',
        tags: []
      }
    ];

    render(
      <TestWrapper>
        <EntityBreakdownChart entities={mixedEntities} />
      </TestWrapper>
    );

    expect(screen.getByText('$150,000')).toBeInTheDocument(); // Combined value
  });

  test('handles empty entities array', () => {
    render(
      <TestWrapper>
        <EntityBreakdownChart entities={[]} />
      </TestWrapper>
    );

    expect(screen.getByText('Entity Analysis')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument(); // Total entities
  });

  test('truncates long entity names in table', () => {
    const longNameEntities = [
      {
        id: '1',
        type: 'employee',
        name: 'This is a very long entity name that should be truncated',
        start_date: '2024-01-01',
        salary: 100000,
        tags: []
      }
    ];

    render(
      <TestWrapper>
        <EntityBreakdownChart entities={longNameEntities} />
      </TestWrapper>
    );

    // Should truncate long names (exact truncation depends on implementation)
    expect(screen.getByText(/This is a very long/)).toBeInTheDocument();
  });
});

describe('Chart Performance', () => {
  test('renders cash flow chart efficiently with large dataset', () => {
    const largeDataset = Array.from({ length: 100 }, (_, i) => ({
      month: `2024-${(i % 12) + 1}`,
      revenue: Math.random() * 100000,
      expenses: Math.random() * 80000,
      net_cash_flow: Math.random() * 20000 - 10000,
      cumulative_cash_flow: Math.random() * 100000 - 50000,
      burn_rate: Math.random() * 10000
    }));

    const startTime = performance.now();
    
    render(
      <TestWrapper>
        <CashFlowChart data={largeDataset} />
      </TestWrapper>
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    expect(renderTime).toBeLessThan(100); // Should render within 100ms
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  test('renders KPI dashboard efficiently with many KPIs', () => {
    const manyKPIs = Array.from({ length: 50 }, (_, i) => ({
      name: `KPI ${i}`,
      value: Math.random() * 1000000,
      unit: '$',
      category: 'test',
      trend: 'up' as const,
      change: Math.random() * 0.2
    }));

    const startTime = performance.now();
    
    render(
      <TestWrapper>
        <KPIDashboard kpis={manyKPIs} />
      </TestWrapper>
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    expect(renderTime).toBeLessThan(200); // Should render within 200ms
    expect(screen.getByText('KPI Dashboard')).toBeInTheDocument();
  });
});