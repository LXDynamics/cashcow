// Comprehensive reports page with interactive charts and analysis

import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Tabs,
  Tab,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../components/Layout/LoadingSpinner';
import CashFlowChart from '../components/Charts/CashFlowChart';
import KPIDashboard from '../components/Charts/KPIDashboard';
import EntityBreakdownChart from '../components/Charts/EntityBreakdownChart';
import calculationService from '../services/calculations';
import entityService from '../services/entities';
import { KPIData, ForecastResponse } from '../types/api';
import { Entity } from '../types/entities';

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
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const AnalyticsReports: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = React.useState(0);
  const [loading, setLoading] = React.useState(true);
  const [kpis, setKpis] = React.useState<KPIData[]>([]);
  const [entities, setEntities] = React.useState<Entity[]>([]);
  const [forecast, setForecast] = React.useState<ForecastResponse | null>(null);
  const [timeRange, setTimeRange] = React.useState('12');
  const [error, setError] = React.useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = React.useState<Date>(new Date());

  const loadReportsData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load data in parallel
      const [kpiResponse, entitiesResponse, forecastResponse] = await Promise.all([
        calculationService.getKPIs(),
        entityService.listEntities({ per_page: 1000 }),
        calculationService.getForecast({ months: parseInt(timeRange) })
      ]);

      if (kpiResponse.success && kpiResponse.data) {
        setKpis(kpiResponse.data);
      }

      if (entitiesResponse.success && entitiesResponse.data) {
        setEntities(entitiesResponse.data);
      }

      if (forecastResponse.success && forecastResponse.data) {
        setForecast(forecastResponse.data);
      }

      setLastUpdated(new Date());
    } catch (error: any) {
      console.error('Error loading reports data:', error);
      setError(error.message || 'Failed to load reports data');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadReportsData();
  }, [timeRange]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleExportReport = async () => {
    try {
      // This would integrate with the reports API
      console.log('Exporting report...');
      // TODO: Implement actual export functionality
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading reports data..." />;
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Reports & Analytics
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Last updated: {lastUpdated.toLocaleString()}
            </Typography>
            <Chip 
              label={`${entities.length} entities`} 
              size="small" 
              color="primary" 
              variant="outlined" 
            />
            <Chip 
              label={`${kpis.length} KPIs`} 
              size="small" 
              color="success" 
              variant="outlined" 
            />
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="6">6 months</MenuItem>
              <MenuItem value="12">12 months</MenuItem>
              <MenuItem value="18">18 months</MenuItem>
              <MenuItem value="24">24 months</MenuItem>
            </Select>
          </FormControl>
          
          <Tooltip title="Refresh Data">
            <IconButton onClick={loadReportsData}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Export Report">
            <IconButton onClick={handleExportReport}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          
          <Button
            variant="outlined"
            startIcon={<TrendingUpIcon />}
            onClick={() => navigate('/forecast')}
          >
            Advanced Forecast
          </Button>
        </Box>
      </Box>

      {error && (
        <Card sx={{ mb: 3, bgcolor: 'error.light' }}>
          <CardContent>
            <Typography color="error">
              {error}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="reports tabs">
          <Tab label="Cash Flow Analysis" />
          <Tab label="KPI Dashboard" />
          <Tab label="Entity Analysis" />
          <Tab label="Financial Summary" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={activeTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            {forecast && forecast.months ? (
              <CashFlowChart
                data={forecast.months}
                title="Cash Flow Forecast"
                height={500}
                showCumulative={true}
                showBurnRate={true}
              />
            ) : (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Cash Flow Analysis
                  </Typography>
                  <Typography color="text.secondary">
                    No forecast data available. Please run a forecast calculation first.
                  </Typography>
                  <Button 
                    variant="contained" 
                    sx={{ mt: 2 }}
                    onClick={() => navigate('/forecast')}
                  >
                    Generate Forecast
                  </Button>
                </CardContent>
              </Card>
            )}
          </Grid>
          
          {forecast && forecast.summary && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Forecast Summary
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h5" color="success.main">
                          ${forecast.summary.total_revenue.toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Revenue
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h5" color="error.main">
                          ${forecast.summary.total_expenses.toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Expenses
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center">
                        <Typography 
                          variant="h5" 
                          color={forecast.summary.net_cash_flow >= 0 ? "success.main" : "error.main"}
                        >
                          ${forecast.summary.net_cash_flow.toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Net Cash Flow
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h5" color="warning.main">
                          {forecast.summary.runway_months}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Runway (months)
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <KPIDashboard kpis={kpis} title="Key Performance Indicators" />
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <EntityBreakdownChart entities={entities} title="Entity Analysis & Breakdown" />
      </TabPanel>

      <TabPanel value={activeTab} index={3}>
        <Grid container spacing={3}>
          {/* Financial Overview */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Financial Overview
                </Typography>
                <Grid container spacing={3}>
                  {kpis.map((kpi, index) => (
                    <Grid item xs={12} sm={6} md={4} key={index}>
                      <Box 
                        sx={{ 
                          p: 2, 
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1,
                          textAlign: 'center'
                        }}
                      >
                        <Typography variant="h6" component="div">
                          {kpi.unit === '$' ? `$${kpi.value.toLocaleString()}` :
                           kpi.unit === '%' ? `${(kpi.value * 100).toFixed(1)}%` :
                           `${kpi.value.toLocaleString()} ${kpi.unit}`}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {kpi.name}
                        </Typography>
                        {kpi.trend && (
                          <Chip
                            size="small"
                            label={kpi.trend}
                            color={kpi.trend === 'up' ? 'success' : kpi.trend === 'down' ? 'error' : 'default'}
                            sx={{ mt: 1 }}
                          />
                        )}
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Quick Actions */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Actions
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button variant="outlined" onClick={() => navigate('/forecast')}>
                    Run Forecast
                  </Button>
                  <Button variant="outlined" onClick={() => navigate('/entities')}>
                    Manage Entities
                  </Button>
                  <Button variant="outlined" onClick={() => navigate('/scenarios')}>
                    Create Scenario
                  </Button>
                  <Button variant="outlined" onClick={handleExportReport}>
                    Export Report
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
};

export default AnalyticsReports;