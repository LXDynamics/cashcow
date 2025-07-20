// Entity breakdown visualization with pie charts and statistics

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
import { Pie, Bar } from 'react-chartjs-2';
import { 
  Box, 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import { Entity, ENTITY_CATEGORIES } from '../../types/entities';

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

interface EntityBreakdownChartProps {
  entities: Entity[];
  title?: string;
}

const EntityBreakdownChart: React.FC<EntityBreakdownChartProps> = ({
  entities,
  title = "Entity Analysis"
}) => {
  // Calculate entity statistics
  const entityStats = React.useMemo(() => {
    const stats = {
      byType: {} as Record<string, number>,
      byCategory: {} as Record<string, number>,
      byValue: {} as Record<string, number>,
      total: entities.length
    };

    entities.forEach(entity => {
      // Count by type
      stats.byType[entity.type] = (stats.byType[entity.type] || 0) + 1;
      
      // Count by category
      const category = Object.entries(ENTITY_CATEGORIES).find(([_, types]) => 
        types.includes(entity.type)
      )?.[0] || 'other';
      stats.byCategory[category] = (stats.byCategory[category] || 0) + 1;
      
      // Sum values by type
      const value = getEntityValue(entity);
      if (value > 0) {
        stats.byValue[entity.type] = (stats.byValue[entity.type] || 0) + value;
      }
    });

    return stats;
  }, [entities]);

  // Get entity monetary value
  const getEntityValue = (entity: Entity): number => {
    const anyEntity = entity as any;
    return anyEntity.amount || anyEntity.salary || anyEntity.monthly_cost || 
           anyEntity.cost || anyEntity.total_budget || anyEntity.monthly_amount || 0;
  };

  // Entity type distribution pie chart
  const typeDistributionData = React.useMemo(() => {
    const types = Object.keys(entityStats.byType);
    const colors = [
      'rgba(33, 150, 243, 0.8)',
      'rgba(76, 175, 80, 0.8)',
      'rgba(244, 67, 54, 0.8)',
      'rgba(255, 152, 0, 0.8)',
      'rgba(156, 39, 176, 0.8)',
      'rgba(0, 188, 212, 0.8)',
      'rgba(139, 195, 74, 0.8)',
      'rgba(255, 193, 7, 0.8)',
      'rgba(121, 85, 72, 0.8)',
      'rgba(158, 158, 158, 0.8)'
    ];

    return {
      labels: types.map(type => type.charAt(0).toUpperCase() + type.slice(1)),
      datasets: [
        {
          data: types.map(type => entityStats.byType[type]),
          backgroundColor: colors.slice(0, types.length),
          borderColor: colors.slice(0, types.length).map(color => color.replace('0.8', '1')),
          borderWidth: 2,
          hoverBackgroundColor: colors.slice(0, types.length).map(color => color.replace('0.8', '0.9'))
        }
      ]
    };
  }, [entityStats.byType]);

  // Entity value by type bar chart
  const valueByTypeData = React.useMemo(() => {
    const types = Object.keys(entityStats.byValue);
    const colors = [
      'rgba(33, 150, 243, 0.8)',
      'rgba(76, 175, 80, 0.8)',
      'rgba(244, 67, 54, 0.8)',
      'rgba(255, 152, 0, 0.8)',
      'rgba(156, 39, 176, 0.8)',
      'rgba(0, 188, 212, 0.8)',
      'rgba(139, 195, 74, 0.8)',
      'rgba(255, 193, 7, 0.8)'
    ];

    return {
      labels: types.map(type => type.charAt(0).toUpperCase() + type.slice(1)),
      datasets: [
        {
          label: 'Total Value ($)',
          data: types.map(type => entityStats.byValue[type]),
          backgroundColor: colors.slice(0, types.length),
          borderColor: colors.slice(0, types.length).map(color => color.replace('0.8', '1')),
          borderWidth: 1
        }
      ]
    };
  }, [entityStats.byValue]);

  const pieOptions: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 10,
          usePointStyle: true
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    }
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
          text: 'Entity Type'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Total Value ($)'
        },
        ticks: {
          callback: function(value) {
            return `$${(value as number).toLocaleString()}`;
          }
        }
      }
    }
  };

  // Category breakdown for summary
  const categoryBreakdown = Object.entries(entityStats.byCategory).map(([category, count]) => ({
    category: category.charAt(0).toUpperCase() + category.slice(1),
    count,
    percentage: ((count / entityStats.total) * 100).toFixed(1)
  }));

  // Top entities by value
  const topEntitiesByValue = entities
    .map(entity => ({
      ...entity,
      value: getEntityValue(entity)
    }))
    .filter(entity => entity.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        {title}
      </Typography>
      
      <Grid container spacing={3}>
        {/* Entity Type Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Entity Distribution by Type
              </Typography>
              <Box sx={{ height: 300, position: 'relative' }}>
                <Pie 
                  data={typeDistributionData} 
                  options={pieOptions}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Value by Type */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Value by Entity Type
              </Typography>
              <Box sx={{ height: 300, position: 'relative' }}>
                <Bar 
                  data={valueByTypeData} 
                  options={barOptions}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Category Summary */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Category Breakdown
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {categoryBreakdown.map((item, index) => (
                  <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body1">{item.category}</Typography>
                      <Chip 
                        label={item.count} 
                        size="small" 
                        color={index === 0 ? 'primary' : 'default'}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {item.percentage}%
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Entities by Value */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Entities by Value
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Value</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {topEntitiesByValue.map((entity, index) => (
                      <TableRow key={entity.id}>
                        <TableCell>
                          <Typography variant="body2" noWrap>
                            {entity.name.length > 20 ? entity.name.substring(0, 20) + '...' : entity.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={entity.type} 
                            size="small" 
                            variant="outlined"
                            color={index < 3 ? 'primary' : 'default'}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="bold">
                            ${entity.value.toLocaleString()}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Summary Stats */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Summary Statistics
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">
                      {entityStats.total}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Entities
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="success.main">
                      {Object.keys(entityStats.byType).length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Entity Types
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="info.main">
                      ${Object.values(entityStats.byValue).reduce((sum, val) => sum + val, 0).toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Value
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="warning.main">
                      ${(Object.values(entityStats.byValue).reduce((sum, val) => sum + val, 0) / entityStats.total).toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg Value
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EntityBreakdownChart;