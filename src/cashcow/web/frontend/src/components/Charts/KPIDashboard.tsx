// KPI Dashboard with various chart types for key metrics

import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import { 
  Box, 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Paper,
  Chip
} from '@mui/material';
import { KPIData } from '../../types/api';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface KPIDashboardProps {
  kpis: KPIData[];
  title?: string;
}

const KPIDashboard: React.FC<KPIDashboardProps> = ({
  kpis,
  title = "KPI Dashboard"
}) => {
  // Separate KPIs by category
  const revenueKPIs = kpis.filter(kpi => 
    kpi.category === 'revenue' || kpi.name.toLowerCase().includes('revenue')
  );
  
  const expenseKPIs = kpis.filter(kpi => 
    kpi.category === 'expenses' || kpi.name.toLowerCase().includes('expense') || kpi.name.toLowerCase().includes('cost')
  );
  
  const cashFlowKPIs = kpis.filter(kpi => 
    kpi.category === 'cash_flow' || kpi.name.toLowerCase().includes('cash') || kpi.name.toLowerCase().includes('burn')
  );

  // Revenue vs Expenses Doughnut Chart
  const revenueExpenseData = React.useMemo(() => {
    const totalRevenue = revenueKPIs.reduce((sum, kpi) => sum + kpi.value, 0);
    const totalExpenses = expenseKPIs.reduce((sum, kpi) => sum + kpi.value, 0);
    
    return {
      labels: ['Revenue', 'Expenses'],
      datasets: [
        {
          data: [totalRevenue, totalExpenses],
          backgroundColor: [
            'rgba(76, 175, 80, 0.8)',
            'rgba(244, 67, 54, 0.8)'
          ],
          borderColor: [
            'rgba(76, 175, 80, 1)',
            'rgba(244, 67, 54, 1)'
          ],
          borderWidth: 2,
          hoverBackgroundColor: [
            'rgba(76, 175, 80, 0.9)',
            'rgba(244, 67, 54, 0.9)'
          ]
        }
      ]
    };
  }, [revenueKPIs, expenseKPIs]);

  // KPI Comparison Bar Chart
  const kpiComparisonData = React.useMemo(() => {
    const topKPIs = kpis
      .filter(kpi => kpi.unit === '$')
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);

    return {
      labels: topKPIs.map(kpi => kpi.name.length > 15 ? kpi.name.substring(0, 15) + '...' : kpi.name),
      datasets: [
        {
          label: 'Value ($)',
          data: topKPIs.map(kpi => kpi.value),
          backgroundColor: topKPIs.map((kpi, index) => {
            const colors = [
              'rgba(33, 150, 243, 0.8)',
              'rgba(76, 175, 80, 0.8)',
              'rgba(255, 152, 0, 0.8)',
              'rgba(156, 39, 176, 0.8)',
              'rgba(233, 30, 99, 0.8)',
              'rgba(0, 188, 212, 0.8)',
              'rgba(139, 195, 74, 0.8)',
              'rgba(255, 193, 7, 0.8)'
            ];
            return colors[index % colors.length];
          }),
          borderColor: topKPIs.map((kpi, index) => {
            const colors = [
              'rgba(33, 150, 243, 1)',
              'rgba(76, 175, 80, 1)',
              'rgba(255, 152, 0, 1)',
              'rgba(156, 39, 176, 1)',
              'rgba(233, 30, 99, 1)',
              'rgba(0, 188, 212, 1)',
              'rgba(139, 195, 74, 1)',
              'rgba(255, 193, 7, 1)'
            ];
            return colors[index % colors.length];
          }),
          borderWidth: 1
        }
      ]
    };
  }, [kpis]);

  const doughnutOptions: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 20,
          usePointStyle: true
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed;
            return `${label}: $${value.toLocaleString()}`;
          }
        }
      }
    },
    cutout: '60%'
  };

  const barOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `$${context.parsed.y.toLocaleString()}`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'KPIs'
        },
        ticks: {
          maxRotation: 45,
          minRotation: 0
        }
      },
      y: {
        title: {
          display: true,
          text: 'Value ($)'
        },
        ticks: {
          callback: function(value) {
            return `$${(value as number).toLocaleString()}`;
          }
        }
      }
    }
  };

  const getTrendChip = (kpi: KPIData) => {
    if (!kpi.trend || kpi.change === undefined) return null;
    
    const color = kpi.trend === 'up' ? 'success' : kpi.trend === 'down' ? 'error' : 'default';
    const changePercent = (Math.abs(kpi.change) * 100).toFixed(1);
    const sign = kpi.change >= 0 ? '+' : '-';
    
    return (
      <Chip
        size="small"
        label={`${sign}${changePercent}%`}
        color={color}
        variant="outlined"
      />
    );
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        {title}
      </Typography>
      
      <Grid container spacing={3}>
        {/* Revenue vs Expenses Doughnut */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Revenue vs Expenses
              </Typography>
              <Box sx={{ height: 300, position: 'relative' }}>
                <Doughnut 
                  data={revenueExpenseData} 
                  options={doughnutOptions}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Top KPIs Bar Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Financial KPIs
              </Typography>
              <Box sx={{ height: 300, position: 'relative' }}>
                <Bar 
                  data={kpiComparisonData} 
                  options={barOptions}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* KPI Summary Cards */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                All KPIs Summary
              </Typography>
              <Grid container spacing={2}>
                {kpis.map((kpi, index) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
                    <Paper 
                      sx={{ 
                        p: 2, 
                        textAlign: 'center',
                        background: 'linear-gradient(45deg, #f5f5f5 30%, #fafafa 90%)',
                        border: '1px solid #e0e0e0'
                      }}
                    >
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {kpi.name}
                      </Typography>
                      <Typography variant="h6" component="div" gutterBottom>
                        {kpi.unit === '$' ? `$${kpi.value.toLocaleString()}` :
                         kpi.unit === '%' ? `${(kpi.value * 100).toFixed(1)}%` :
                         `${kpi.value.toLocaleString()} ${kpi.unit}`}
                      </Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, alignItems: 'center' }}>
                        {getTrendChip(kpi)}
                        {kpi.category && (
                          <Chip
                            size="small"
                            label={kpi.category}
                            variant="outlined"
                            color="primary"
                          />
                        )}
                      </Box>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default KPIDashboard;