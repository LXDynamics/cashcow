// Reports and analysis page

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Paper,
  Tabs,
  Tab,
  Alert
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Analytics as AnalyticsIcon,
  ShowChart as ShowChartIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import LoadingSpinner from '../components/Layout/LoadingSpinner';
import LineChart from '../components/Charts/LineChart';
import calculationService from '../services/calculations';
import { ForecastResponse } from '../types/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`reports-tabpanel-${index}`}
      aria-labelledby={`reports-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Reports: React.FC = () => {
  const { type } = useParams<{ type?: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = React.useState(0);
  const [forecast, setForecast] = React.useState<ForecastResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const loadForecast = async (params = {}) => {
    try {
      setLoading(true);
      setError(null);
      const response = await calculationService.generateForecast(params);
      if (response.success && response.data) {
        setForecast(response.data);
      }
    } catch (error: any) {
      console.error('Error loading forecast:', error);
      setError(error.message || 'Failed to load forecast');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (type === 'forecast' || activeTab === 0) {
      loadForecast();
    }
  }, [type, activeTab]);

  const chartData = React.useMemo(() => {
    if (!forecast) return null;

    return {
      labels: forecast.months.map(m => m.month),
      datasets: [
        {
          label: 'Revenue',
          data: forecast.months.map(m => m.revenue),
          backgroundColor: 'rgba(76, 175, 80, 0.2)',
          borderColor: 'rgba(76, 175, 80, 1)',
          borderWidth: 2,
          fill: false
        },
        {
          label: 'Expenses',
          data: forecast.months.map(m => m.expenses),
          backgroundColor: 'rgba(244, 67, 54, 0.2)',
          borderColor: 'rgba(244, 67, 54, 1)',
          borderWidth: 2,
          fill: false
        },
        {
          label: 'Net Cash Flow',
          data: forecast.months.map(m => m.net_cash_flow),
          backgroundColor: 'rgba(33, 150, 243, 0.2)',
          borderColor: 'rgba(33, 150, 243, 1)',
          borderWidth: 2,
          fill: false
        }
      ]
    };
  }, [forecast]);

  const reportCards = [
    {
      title: 'Cash Flow Forecast',
      description: 'Monthly cash flow projections and runway analysis',
      icon: TrendingUpIcon,
      color: 'primary',
      path: '/reports/forecast',
      available: true
    },
    {
      title: 'KPI Dashboard',
      description: 'Key performance indicators and metrics',
      icon: AssessmentIcon,
      color: 'secondary',
      path: '/reports/kpis',
      available: true
    },
    {
      title: 'Monte Carlo Analysis',
      description: 'Risk analysis with probability distributions',
      icon: AnalyticsIcon,
      color: 'success',
      path: '/reports/monte-carlo',
      available: true
    },
    {
      title: 'What-If Analysis',
      description: 'Scenario planning and sensitivity testing',
      icon: ShowChartIcon,
      color: 'warning',
      path: '/reports/what-if',
      available: true
    }
  ];

  if (loading && !forecast) {
    return <LoadingSpinner message="Loading reports..." />;
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Reports & Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Financial reports, forecasts, and analytical insights
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Report Navigation */}
      {!type && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {reportCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <Card 
                  sx={{ 
                    height: '100%',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: 3
                    }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Icon 
                        sx={{ 
                          fontSize: 40,
                          color: `${card.color}.main`,
                          mr: 2
                        }} 
                      />
                      <Typography variant="h6" component="div">
                        {card.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {card.description}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button 
                      size="small" 
                      onClick={() => navigate(card.path)}
                      disabled={!card.available}
                    >
                      View Report
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Detailed Report Views */}
      {(type || forecast) && (
        <Paper sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={activeTab} onChange={handleTabChange}>
              <Tab label="Cash Flow Forecast" />
              <Tab label="Summary Metrics" />
              <Tab label="Scenario Analysis" />
              <Tab label="Export Options" />
            </Tabs>
          </Box>

          <TabPanel value={activeTab} index={0}>
            {/* Cash Flow Forecast */}
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" gutterBottom>
                  Cash Flow Forecast
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => loadForecast()}
                  disabled={loading}
                >
                  {loading ? 'Loading...' : 'Refresh'}
                </Button>
              </Box>

              {chartData && (
                <Box sx={{ mb: 4 }}>
                  <LineChart
                    data={chartData}
                    options={{
                      responsive: true,
                      plugins: {
                        title: {
                          display: true,
                          text: 'Monthly Cash Flow Projection'
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          title: {
                            display: true,
                            text: 'Amount ($)'
                          }
                        }
                      }
                    }}
                  />
                </Box>
              )}

              {forecast && (
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Summary
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography>Total Revenue:</Typography>
                          <Typography fontWeight={600}>
                            ${forecast.summary.total_revenue.toLocaleString()}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography>Total Expenses:</Typography>
                          <Typography fontWeight={600}>
                            ${forecast.summary.total_expenses.toLocaleString()}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography>Net Cash Flow:</Typography>
                          <Typography 
                            fontWeight={600}
                            color={forecast.summary.net_cash_flow >= 0 ? 'success.main' : 'error.main'}
                          >
                            ${forecast.summary.net_cash_flow.toLocaleString()}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography>Average Burn Rate:</Typography>
                          <Typography fontWeight={600}>
                            ${forecast.summary.average_burn_rate.toLocaleString()}/month
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography>Runway:</Typography>
                          <Typography 
                            fontWeight={600}
                            color={forecast.summary.runway_months < 6 ? 'error.main' : 'success.main'}
                          >
                            {forecast.summary.runway_months.toFixed(1)} months
                          </Typography>
                        </Box>
                      </Box>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Key Insights
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Typography variant="body2">
                          • Current runway provides {forecast.summary.runway_months.toFixed(0)} months of operations
                        </Typography>
                        <Typography variant="body2">
                          • Average monthly burn rate: ${forecast.summary.average_burn_rate.toLocaleString()}
                        </Typography>
                        <Typography variant="body2">
                          • {forecast.summary.net_cash_flow >= 0 ? 'Positive' : 'Negative'} net cash flow projected
                        </Typography>
                        <Typography variant="body2">
                          • Revenue trending {forecast.months.length > 6 && 
                            forecast.months[forecast.months.length - 1].revenue > forecast.months[0].revenue ? 'upward' : 'flat'}
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                </Grid>
              )}
            </Box>
          </TabPanel>

          <TabPanel value={activeTab} index={1}>
            <Typography variant="h5" gutterBottom>
              Summary Metrics
            </Typography>
            <Typography variant="body1">
              Detailed financial metrics and KPI analysis will be displayed here.
            </Typography>
          </TabPanel>

          <TabPanel value={activeTab} index={2}>
            <Typography variant="h5" gutterBottom>
              Scenario Analysis
            </Typography>
            <Typography variant="body1">
              Monte Carlo simulations and what-if analysis tools will be available here.
            </Typography>
          </TabPanel>

          <TabPanel value={activeTab} index={3}>
            <Typography variant="h5" gutterBottom>
              Export Options
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button variant="outlined" startIcon={<DownloadIcon />}>
                Export to CSV
              </Button>
              <Button variant="outlined" startIcon={<DownloadIcon />}>
                Export to PDF
              </Button>
              <Button variant="outlined" startIcon={<DownloadIcon />}>
                Export to Excel
              </Button>
            </Box>
          </TabPanel>
        </Paper>
      )}
    </Box>
  );
};

export default Reports;