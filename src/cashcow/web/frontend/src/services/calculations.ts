// Calculation and forecast services

import { api } from './api';
import {
  ApiResponse,
  ForecastParams,
  ForecastResponse,
  KPIResponse,
  KPIData,
  MonteCarloParams,
  WhatIfParams,
  SensitivityParams
} from '../types/api';

// Mock data for development
const MOCK_FORECAST_DATA: ForecastResponse = {
  months: [
    {
      month: '2024-01',
      revenue: 85000,
      expenses: 125000,
      net_cash_flow: -40000,
      cumulative_cash_flow: -40000,
      burn_rate: 40000
    },
    {
      month: '2024-02',
      revenue: 92000,
      expenses: 128000,
      net_cash_flow: -36000,
      cumulative_cash_flow: -76000,
      burn_rate: 36000
    },
    {
      month: '2024-03',
      revenue: 165000,
      expenses: 132000,
      net_cash_flow: 33000,
      cumulative_cash_flow: -43000,
      burn_rate: 0
    },
    {
      month: '2024-04',
      revenue: 105000,
      expenses: 135000,
      net_cash_flow: -30000,
      cumulative_cash_flow: -73000,
      burn_rate: 30000
    },
    {
      month: '2024-05',
      revenue: 112000,
      expenses: 138000,
      net_cash_flow: -26000,
      cumulative_cash_flow: -99000,
      burn_rate: 26000
    },
    {
      month: '2024-06',
      revenue: 275000,
      expenses: 142000,
      net_cash_flow: 133000,
      cumulative_cash_flow: 34000,
      burn_rate: 0
    },
    {
      month: '2024-07',
      revenue: 125000,
      expenses: 145000,
      net_cash_flow: -20000,
      cumulative_cash_flow: 14000,
      burn_rate: 20000
    },
    {
      month: '2024-08',
      revenue: 130000,
      expenses: 148000,
      net_cash_flow: -18000,
      cumulative_cash_flow: -4000,
      burn_rate: 18000
    },
    {
      month: '2024-09',
      revenue: 135000,
      expenses: 152000,
      net_cash_flow: -17000,
      cumulative_cash_flow: -21000,
      burn_rate: 17000
    },
    {
      month: '2024-10',
      revenue: 140000,
      expenses: 155000,
      net_cash_flow: -15000,
      cumulative_cash_flow: -36000,
      burn_rate: 15000
    },
    {
      month: '2024-11',
      revenue: 145000,
      expenses: 158000,
      net_cash_flow: -13000,
      cumulative_cash_flow: -49000,
      burn_rate: 13000
    },
    {
      month: '2024-12',
      revenue: 150000,
      expenses: 162000,
      net_cash_flow: -12000,
      cumulative_cash_flow: -61000,
      burn_rate: 12000
    }
  ],
  summary: {
    total_revenue: 1659000,
    total_expenses: 1720000,
    net_cash_flow: -61000,
    average_burn_rate: 22250,
    runway_months: 18.5
  }
};

const MOCK_KPI_DATA: KPIData[] = [
  {
    name: 'Monthly Recurring Revenue',
    value: 15000,
    unit: '$',
    change: 0.125,
    change_period: 'month',
    trend: 'up',
    category: 'revenue'
  },
  {
    name: 'Total Cash Available',
    value: 2750000,
    unit: '$',
    change: -0.045,
    change_period: 'month',
    trend: 'down',
    category: 'cash_flow'
  },
  {
    name: 'Burn Rate',
    value: 22250,
    unit: '$/month',
    change: -0.08,
    change_period: 'month',
    trend: 'down',
    category: 'expenses'
  },
  {
    name: 'Runway',
    value: 18.5,
    unit: 'months',
    change: 0.15,
    change_period: 'month',
    trend: 'up',
    category: 'cash_flow'
  },
  {
    name: 'Employee Count',
    value: 8,
    unit: 'people',
    change: 0.0,
    change_period: 'month',
    trend: 'stable',
    category: 'expenses'
  },
  {
    name: 'Revenue Growth Rate',
    value: 0.125,
    unit: '%',
    change: 0.032,
    change_period: 'month',
    trend: 'up',
    category: 'revenue'
  },
  {
    name: 'Gross Margin',
    value: 0.72,
    unit: '%',
    change: 0.023,
    change_period: 'month',
    trend: 'up',
    category: 'revenue'
  },
  {
    name: 'Customer Acquisition Cost',
    value: 2500,
    unit: '$',
    change: -0.12,
    change_period: 'month',
    trend: 'down',
    category: 'expenses'
  }
];

class CalculationService {
  
  // Generate cash flow forecast
  async generateForecast(params: ForecastParams = {}): Promise<ApiResponse<ForecastResponse>> {
    const queryParams = new URLSearchParams();
    
    if (params.months) queryParams.set('months', params.months.toString());
    if (params.start_date) queryParams.set('start_date', params.start_date);
    if (params.scenario) queryParams.set('scenario', params.scenario);
    
    const url = `/forecast?${queryParams.toString()}`;
    
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true' || true) {
      // Adjust mock data based on parameters
      const forecastData = this.generateMockForecast(params);
      return { success: true, data: forecastData };
    }
    
    return api.get<ForecastResponse>(url);
  }

  // Get forecast data (alias for generateForecast)
  async getForecast(params: ForecastParams = {}): Promise<ApiResponse<ForecastResponse>> {
    return this.generateForecast(params);
  }

  // Get KPI data
  async getKPIs(): Promise<KPIResponse> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true' || true) {
      return { success: true, data: [...MOCK_KPI_DATA] };
    }
    
    return api.get<KPIData[]>('/kpis');
  }

  // Run Monte Carlo simulation
  async runMonteCarloAnalysis(params: MonteCarloParams = {}): Promise<ApiResponse<any>> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true' || true) {
      const results = this.generateMockMonteCarloResults(params);
      return { success: true, data: results };
    }
    
    return api.post<any>('/analysis/monte-carlo', params);
  }

  // Run What-If analysis
  async runWhatIfAnalysis(params: WhatIfParams): Promise<ApiResponse<any>> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true' || true) {
      const results = this.generateMockWhatIfResults(params);
      return { success: true, data: results };
    }
    
    return api.post<any>('/analysis/what-if', params);
  }

  // Run sensitivity analysis
  async runSensitivityAnalysis(params: SensitivityParams): Promise<ApiResponse<any>> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true' || true) {
      const results = this.generateMockSensitivityResults(params);
      return { success: true, data: results };
    }
    
    return api.post<any>('/analysis/sensitivity', params);
  }

  // Recalculate all metrics
  async recalculateMetrics(): Promise<ApiResponse<void>> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true' || true) {
      // Simulate calculation time
      await new Promise(resolve => setTimeout(resolve, 2000));
      return { success: true };
    }
    
    return api.post<void>('/calculations/recalculate');
  }

  // Get calculation status
  async getCalculationStatus(): Promise<ApiResponse<{ status: string; progress?: number }>> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true' || true) {
      return { 
        success: true, 
        data: { 
          status: 'completed', 
          progress: 100 
        } 
      };
    }
    
    return api.get<{ status: string; progress?: number }>('/calculations/status');
  }

  // Private methods for mock data generation
  private generateMockForecast(params: ForecastParams): ForecastResponse {
    const months = params.months || 12;
    const startDate = new Date(params.start_date || '2024-01-01');
    
    const forecastMonths = [];
    let cumulativeCashFlow = 0;
    
    for (let i = 0; i < months; i++) {
      const monthDate = new Date(startDate);
      monthDate.setMonth(monthDate.getMonth() + i);
      
      // Generate some variation in the data
      const baseRevenue = 100000 + (i * 5000) + (Math.random() * 20000 - 10000);
      const baseExpenses = 140000 + (i * 2000) + (Math.random() * 10000 - 5000);
      
      // Add some seasonal effects and scenario adjustments
      let revenueMult = 1.0;
      let expenseMult = 1.0;
      
      if (params.scenario === 'optimistic') {
        revenueMult = 1.2;
        expenseMult = 0.9;
      } else if (params.scenario === 'conservative') {
        revenueMult = 0.8;
        expenseMult = 1.1;
      }
      
      const revenue = Math.round(baseRevenue * revenueMult);
      const expenses = Math.round(baseExpenses * expenseMult);
      const netCashFlow = revenue - expenses;
      cumulativeCashFlow += netCashFlow;
      
      forecastMonths.push({
        month: monthDate.toISOString().substring(0, 7),
        revenue,
        expenses,
        net_cash_flow: netCashFlow,
        cumulative_cash_flow: cumulativeCashFlow,
        burn_rate: netCashFlow < 0 ? Math.abs(netCashFlow) : 0
      });
    }
    
    // Calculate summary
    const totalRevenue = forecastMonths.reduce((sum, month) => sum + month.revenue, 0);
    const totalExpenses = forecastMonths.reduce((sum, month) => sum + month.expenses, 0);
    const netCashFlow = totalRevenue - totalExpenses;
    const burnMonths = forecastMonths.filter(m => m.burn_rate > 0);
    const averageBurnRate = burnMonths.length > 0 
      ? burnMonths.reduce((sum, month) => sum + month.burn_rate, 0) / burnMonths.length
      : 0;
    
    // Estimate runway (simplified)
    const currentCash = 2750000; // Mock current cash
    const runwayMonths = averageBurnRate > 0 ? currentCash / averageBurnRate : Infinity;
    
    return {
      months: forecastMonths,
      summary: {
        total_revenue: totalRevenue,
        total_expenses: totalExpenses,
        net_cash_flow: netCashFlow,
        average_burn_rate: averageBurnRate,
        runway_months: Math.min(runwayMonths, 999)
      }
    };
  }

  private generateMockMonteCarloResults(params: MonteCarloParams): any {
    const iterations = params.iterations || 1000;
    
    // Generate mock results
    const scenarios = [];
    for (let i = 0; i < iterations; i++) {
      scenarios.push({
        iteration: i + 1,
        revenue: 1500000 + (Math.random() * 1000000 - 500000),
        expenses: 1600000 + (Math.random() * 400000 - 200000),
        runway: 12 + (Math.random() * 24 - 12)
      });
    }
    
    // Calculate percentiles
    const revenueValues = scenarios.map(s => s.revenue).sort((a, b) => a - b);
    const runwayValues = scenarios.map(s => s.runway).sort((a, b) => a - b);
    
    return {
      scenarios: scenarios.slice(0, 100), // Return subset for display
      statistics: {
        revenue: {
          mean: revenueValues.reduce((sum, val) => sum + val, 0) / revenueValues.length,
          p10: revenueValues[Math.floor(iterations * 0.1)],
          p50: revenueValues[Math.floor(iterations * 0.5)],
          p90: revenueValues[Math.floor(iterations * 0.9)]
        },
        runway: {
          mean: runwayValues.reduce((sum, val) => sum + val, 0) / runwayValues.length,
          p10: runwayValues[Math.floor(iterations * 0.1)],
          p50: runwayValues[Math.floor(iterations * 0.5)],
          p90: runwayValues[Math.floor(iterations * 0.9)]
        }
      }
    };
  }

  private generateMockWhatIfResults(params: WhatIfParams): any {
    const baseline = MOCK_FORECAST_DATA.summary;
    
    // Apply variable changes
    const changes = params.variables || {};
    let revenueChange = 1.0;
    let expenseChange = 1.0;
    
    if (changes.revenue_growth) {
      revenueChange = 1 + changes.revenue_growth;
    }
    if (changes.expense_reduction) {
      expenseChange = 1 - changes.expense_reduction;
    }
    
    return {
      scenario: params.scenario,
      baseline: baseline,
      modified: {
        total_revenue: baseline.total_revenue * revenueChange,
        total_expenses: baseline.total_expenses * expenseChange,
        net_cash_flow: (baseline.total_revenue * revenueChange) - (baseline.total_expenses * expenseChange),
        runway_months: baseline.runway_months * (1 / expenseChange)
      },
      changes: changes
    };
  }

  private generateMockSensitivityResults(params: SensitivityParams): any {
    const variable = params.variable;
    const range = params.range || [-0.2, 0.2];
    const steps = params.steps || 10;
    
    const results = [];
    const stepSize = (range[1] - range[0]) / (steps - 1);
    
    for (let i = 0; i < steps; i++) {
      const variableValue = range[0] + (i * stepSize);
      const baselineRevenue = 1659000;
      const baselineRunway = 18.5;
      
      // Simple linear relationship for demo
      const impactFactor = 1 + variableValue;
      
      results.push({
        variable_value: variableValue,
        revenue: baselineRevenue * impactFactor,
        runway: baselineRunway * (1 / impactFactor)
      });
    }
    
    return {
      variable: variable,
      range: range,
      results: results
    };
  }
}

export const calculationService = new CalculationService();
export default calculationService;