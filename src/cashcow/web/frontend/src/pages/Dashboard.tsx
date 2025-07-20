// Main dashboard with KPI overview

import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Chip,
  IconButton,
  Button
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Refresh as RefreshIcon,
  OpenInNew as OpenInNewIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../components/Layout/LoadingSpinner';
import RealTimeUpdates from '../components/RealTimeUpdates';
import KPIDashboard from '../components/Charts/KPIDashboard';
import calculationService from '../services/calculations';
import entityService from '../services/entities';
import { KPIData, WebSocketMessage } from '../types/api';
import { Entity } from '../types/entities';
import { WebSocketService } from '../services/websockets';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [kpis, setKpis] = React.useState<KPIData[]>([]);
  const [entities, setEntities] = React.useState<Entity[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [lastUpdated, setLastUpdated] = React.useState<Date>(new Date());
  const [connected, setConnected] = React.useState(false);
  const [wsService] = React.useState(() => new WebSocketService(`${process.env.REACT_APP_WS_BASE_URL}/status`));

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load KPIs and entities in parallel
      const [kpiResponse, entitiesResponse] = await Promise.all([
        calculationService.getKPIs(),
        entityService.listEntities({ per_page: 100 })
      ]);
      
      if (kpiResponse.success && kpiResponse.data) {
        setKpis(kpiResponse.data);
      }
      
      if (entitiesResponse.success && entitiesResponse.data) {
        setEntities(entitiesResponse.data);
      }
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadDashboardData();
    
    // Set up WebSocket connection for real-time updates
    const handleWebSocketMessage = (message: WebSocketMessage) => {
      if (message.type === 'kpi_update') {
        setKpis(prevKpis => {
          const updatedKpi = message.data.kpi;
          const existingIndex = prevKpis.findIndex(kpi => kpi.name === updatedKpi.name);
          
          if (existingIndex >= 0) {
            const newKpis = [...prevKpis];
            newKpis[existingIndex] = updatedKpi;
            return newKpis;
          } else {
            return [...prevKpis, updatedKpi];
          }
        });
        setLastUpdated(new Date());
      } else if (message.type === 'calculation_complete') {
        // Refresh all data when calculations complete
        loadDashboardData();
      }
    };

    const handleConnect = () => {
      setConnected(true);
      console.log('Dashboard WebSocket connected');
    };

    const handleDisconnect = () => {
      setConnected(false);
      console.log('Dashboard WebSocket disconnected');
    };

    const handleError = (error: Event) => {
      console.error('Dashboard WebSocket error:', error);
      setConnected(false);
    };

    wsService.connect({
      onMessage: handleWebSocketMessage,
      onConnect: handleConnect,
      onDisconnect: handleDisconnect,
      onError: handleError
    });

    // Cleanup on unmount
    return () => {
      wsService.disconnect();
    };
  }, [wsService]);

  const formatKPIValue = (kpi: KPIData) => {
    if (kpi.unit === '$') {
      return `$${kpi.value.toLocaleString()}`;
    } else if (kpi.unit === '%') {
      return `${(kpi.value * 100).toFixed(1)}%`;
    } else if (kpi.unit === '$/month') {
      return `$${kpi.value.toLocaleString()}/mo`;
    }
    return `${kpi.value.toLocaleString()} ${kpi.unit}`;
  };

  const formatChange = (change: number) => {
    const percent = (Math.abs(change) * 100).toFixed(1);
    return change >= 0 ? `+${percent}%` : `-${percent}%`;
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUpIcon color="success" />;
      case 'down':
        return <TrendingDownIcon color="error" />;
      default:
        return <TrendingFlatIcon color="action" />;
    }
  };

  const getTrendColor = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return 'success.main';
      case 'down':
        return 'error.main';
      default:
        return 'text.secondary';
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading dashboard data..." />;
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Dashboard
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Last updated: {lastUpdated.toLocaleString()}
            </Typography>
            <Chip
              label={connected ? "Live" : "Offline"}
              size="small"
              color={connected ? "success" : "default"}
              variant={connected ? "filled" : "outlined"}
            />
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton onClick={loadDashboardData} title="Refresh Data">
            <RefreshIcon />
          </IconButton>
          
          <Button 
            variant="outlined" 
            onClick={() => navigate('/reports/forecast')}
            startIcon={<OpenInNewIcon />}
          >
            View Forecast
          </Button>
        </Box>
      </Box>

      {/* Real-time Updates */}
      <RealTimeUpdates 
        title="Dashboard Updates"
        endpoint="/status"
        showProgress={true}
        maxRecentUpdates={5}
      />

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {kpis.map((kpi, index) => (
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
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" component="div" sx={{ fontSize: '1rem', fontWeight: 500 }}>
                    {kpi.name}
                  </Typography>
                  {kpi.trend && getTrendIcon(kpi.trend)}
                </Box>
                
                <Typography variant="h4" component="div" sx={{ mb: 1, fontWeight: 600 }}>
                  {formatKPIValue(kpi)}
                </Typography>
                
                {kpi.change !== undefined && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={formatChange(kpi.change)}
                      size="small"
                      sx={{
                        bgcolor: kpi.trend === 'up' ? 'success.light' : 
                                kpi.trend === 'down' ? 'error.light' : 'grey.200',
                        color: kpi.trend === 'up' ? 'success.dark' : 
                               kpi.trend === 'down' ? 'error.dark' : 'text.secondary',
                        fontWeight: 500
                      }}
                    />
                    {kpi.change_period && (
                      <Typography variant="caption" color="text.secondary">
                        vs last {kpi.change_period}
                      </Typography>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Interactive KPI Charts */}
      {kpis.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <KPIDashboard kpis={kpis} title="Interactive KPI Analysis" />
        </Box>
      )}

      {/* Quick Actions */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button 
                variant="outlined" 
                fullWidth 
                onClick={() => navigate('/entities')}
              >
                Add New Entity
              </Button>
              <Button 
                variant="outlined" 
                fullWidth 
                onClick={() => navigate('/reports/forecast')}
              >
                Generate Forecast
              </Button>
              <Button 
                variant="outlined" 
                fullWidth 
                onClick={() => navigate('/reports/monte-carlo')}
              >
                Run Monte Carlo Analysis
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Typography variant="body2" color="text.secondary">
                • Updated employee salary for Jane Smith
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Added new grant: NASA SBIR Phase II
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Generated cash flow forecast for Q2 2024
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Completed Monte Carlo analysis
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Summary Cards */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Revenue Sources
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Active revenue streams
              </Typography>
              <Typography variant="h5" color="primary">
                4 Active
              </Typography>
              <Typography variant="body2" color="text.secondary">
                2 Grants • 1 Investment • 1 Service
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Team Size
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Current employees
              </Typography>
              <Typography variant="h5" color="primary">
                8 People
              </Typography>
              <Typography variant="body2" color="text.secondary">
                6 Full-time • 2 Part-time
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Projects
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                In progress
              </Typography>
              <Typography variant="h5" color="primary">
                3 Projects
              </Typography>
              <Typography variant="body2" color="text.secondary">
                1 High Priority • 2 Medium Priority
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;