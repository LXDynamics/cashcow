// KPI display component

import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  InfoOutlined as InfoIcon
} from '@mui/icons-material';
import { KPIData } from '../types/api';

interface KPICardProps {
  kpi: KPIData;
  onClick?: () => void;
}

const KPICard: React.FC<KPICardProps> = ({ kpi, onClick }) => {
  const formatValue = () => {
    if (kpi.unit === '$') {
      return `$${kpi.value.toLocaleString()}`;
    } else if (kpi.unit === '%') {
      return `${(kpi.value * 100).toFixed(1)}%`;
    } else if (kpi.unit === '$/month') {
      return `$${kpi.value.toLocaleString()}/mo`;
    }
    return `${kpi.value.toLocaleString()} ${kpi.unit}`;
  };

  const formatChange = () => {
    if (kpi.change === undefined) return null;
    const percent = (Math.abs(kpi.change) * 100).toFixed(1);
    return kpi.change >= 0 ? `+${percent}%` : `-${percent}%`;
  };

  const getTrendIcon = () => {
    switch (kpi.trend) {
      case 'up':
        return <TrendingUpIcon color="success" sx={{ fontSize: 20 }} />;
      case 'down':
        return <TrendingDownIcon color="error" sx={{ fontSize: 20 }} />;
      default:
        return <TrendingFlatIcon color="action" sx={{ fontSize: 20 }} />;
    }
  };

  const getTrendColor = () => {
    switch (kpi.trend) {
      case 'up':
        return 'success.main';
      case 'down':
        return 'error.main';
      default:
        return 'text.secondary';
    }
  };

  return (
    <Card 
      sx={{ 
        height: '100%',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': onClick ? {
          transform: 'translateY(-2px)',
          boxShadow: 3
        } : {}
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography 
            variant="subtitle1" 
            component="div" 
            sx={{ 
              fontSize: '0.95rem', 
              fontWeight: 500,
              lineHeight: 1.2,
              flex: 1
            }}
          >
            {kpi.name}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {kpi.trend && getTrendIcon()}
            <IconButton size="small" sx={{ opacity: 0.6 }}>
              <InfoIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>
        
        <Typography 
          variant="h4" 
          component="div" 
          sx={{ 
            mb: 1.5, 
            fontWeight: 700,
            color: 'text.primary',
            fontSize: { xs: '1.75rem', sm: '2.125rem' }
          }}
        >
          {formatValue()}
        </Typography>
        
        {kpi.change !== undefined && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={formatChange()}
              size="small"
              sx={{
                bgcolor: kpi.trend === 'up' ? 'success.light' : 
                        kpi.trend === 'down' ? 'error.light' : 'grey.200',
                color: kpi.trend === 'up' ? 'success.dark' : 
                       kpi.trend === 'down' ? 'error.dark' : 'text.secondary',
                fontWeight: 600,
                fontSize: '0.75rem'
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
  );
};

export default KPICard;