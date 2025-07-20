// Cash flow visualization chart with revenue/expenses breakdown

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js';
import { Chart } from 'react-chartjs-2';
import { Box, Typography, Card, CardContent } from '@mui/material';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

interface CashFlowData {
  month: string;
  revenue: number;
  expenses: number;
  net_cash_flow: number;
  cumulative_cash_flow: number;
  burn_rate?: number;
}

interface CashFlowChartProps {
  data: CashFlowData[];
  title?: string;
  height?: number;
  showCumulative?: boolean;
  showBurnRate?: boolean;
}

const CashFlowChart: React.FC<CashFlowChartProps> = ({
  data,
  title = "Cash Flow Analysis",
  height = 400,
  showCumulative = true,
  showBurnRate = false
}) => {
  const chartData = React.useMemo(() => {
    const labels = data.map(item => item.month);
    
    const datasets = [
      {
        type: 'bar' as const,
        label: 'Revenue',
        data: data.map(item => item.revenue),
        backgroundColor: 'rgba(76, 175, 80, 0.7)',
        borderColor: 'rgba(76, 175, 80, 1)',
        borderWidth: 1,
        yAxisID: 'y'
      },
      {
        type: 'bar' as const,
        label: 'Expenses',
        data: data.map(item => -item.expenses), // Negative for visual representation
        backgroundColor: 'rgba(244, 67, 54, 0.7)',
        borderColor: 'rgba(244, 67, 54, 1)',
        borderWidth: 1,
        yAxisID: 'y'
      },
      {
        type: 'line' as const,
        label: 'Net Cash Flow',
        data: data.map(item => item.net_cash_flow),
        borderColor: 'rgba(33, 150, 243, 1)',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        borderWidth: 3,
        fill: false,
        tension: 0.4,
        pointRadius: 5,
        pointHoverRadius: 7,
        yAxisID: 'y'
      }
    ];

    if (showCumulative) {
      datasets.push({
        type: 'line' as const,
        label: 'Cumulative Cash Flow',
        data: data.map(item => item.cumulative_cash_flow),
        borderColor: 'rgba(156, 39, 176, 1)',
        backgroundColor: 'rgba(156, 39, 176, 0.1)',
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        yAxisID: 'y1'
      });
    }

    if (showBurnRate && data.some(item => item.burn_rate !== undefined)) {
      datasets.push({
        type: 'line' as const,
        label: 'Burn Rate',
        data: data.map(item => item.burn_rate || 0),
        borderColor: 'rgba(255, 152, 0, 1)',
        backgroundColor: 'rgba(255, 152, 0, 0.1)',
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
        yAxisID: 'y'
      });
    }

    return {
      labels,
      datasets
    };
  }, [data, showCumulative, showBurnRate]);

  const options: ChartOptions<'bar' | 'line'> = React.useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      title: {
        display: !!title,
        text: title,
        font: {
          size: 16,
          weight: 'bold'
        }
      },
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              const value = Math.abs(context.parsed.y);
              label += new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              }).format(value);
            }
            return label;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Month'
        }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Monthly Cash Flow ($)'
        },
        ticks: {
          callback: function(value) {
            return new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(value as number);
          }
        },
        grid: {
          drawOnChartArea: true,
        },
      },
      ...(showCumulative && {
        y1: {
          type: 'linear' as const,
          display: true,
          position: 'right' as const,
          title: {
            display: true,
            text: 'Cumulative Cash Flow ($)'
          },
          ticks: {
            callback: function(value) {
              return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              }).format(value as number);
            }
          },
          grid: {
            drawOnChartArea: false,
          },
        }
      })
    }
  }), [title, showCumulative]);

  const summary = React.useMemo(() => {
    if (data.length === 0) return null;
    
    const totalRevenue = data.reduce((sum, item) => sum + item.revenue, 0);
    const totalExpenses = data.reduce((sum, item) => sum + item.expenses, 0);
    const finalCumulativeCashFlow = data[data.length - 1]?.cumulative_cash_flow || 0;
    const avgBurnRate = data.reduce((sum, item) => sum + (item.burn_rate || 0), 0) / data.length;

    return {
      totalRevenue,
      totalExpenses,
      netCashFlow: totalRevenue - totalExpenses,
      finalCumulativeCashFlow,
      avgBurnRate
    };
  }, [data]);

  return (
    <Card>
      <CardContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          
          {summary && (
            <Box sx={{ display: 'flex', gap: 4, mb: 2, flexWrap: 'wrap' }}>
              <Box>
                <Typography variant="caption" color="text.secondary">Total Revenue</Typography>
                <Typography variant="body2" fontWeight="bold" color="success.main">
                  ${summary.totalRevenue.toLocaleString()}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Total Expenses</Typography>
                <Typography variant="body2" fontWeight="bold" color="error.main">
                  ${summary.totalExpenses.toLocaleString()}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Net Cash Flow</Typography>
                <Typography 
                  variant="body2" 
                  fontWeight="bold" 
                  color={summary.netCashFlow >= 0 ? "success.main" : "error.main"}
                >
                  ${summary.netCashFlow.toLocaleString()}
                </Typography>
              </Box>
              {showCumulative && (
                <Box>
                  <Typography variant="caption" color="text.secondary">Final Position</Typography>
                  <Typography 
                    variant="body2" 
                    fontWeight="bold"
                    color={summary.finalCumulativeCashFlow >= 0 ? "success.main" : "error.main"}
                  >
                    ${summary.finalCumulativeCashFlow.toLocaleString()}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </Box>
        
        <Box sx={{ height: height, position: 'relative' }}>
          <Chart 
            type="bar"
            data={chartData} 
            options={options}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

export default CashFlowChart;