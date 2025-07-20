// Real-time updates indicator component

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse,
  IconButton
} from '@mui/material';
import {
  Speed as SpeedIcon,
  TrendingUp as TrendingUpIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Sync as SyncIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { WebSocketMessage } from '../types/api';
import { WebSocketService } from '../services/websockets';

interface RealTimeUpdatesProps {
  title?: string;
  endpoint?: string;
  showProgress?: boolean;
  maxRecentUpdates?: number;
}

interface UpdateEvent {
  id: string;
  type: string;
  message: string;
  timestamp: Date;
  status: 'success' | 'error' | 'info' | 'progress';
  progress?: number;
}

const RealTimeUpdates: React.FC<RealTimeUpdatesProps> = ({
  title = "Real-time Updates",
  endpoint = "/status",
  showProgress = true,
  maxRecentUpdates = 10
}) => {
  const [connected, setConnected] = React.useState(false);
  const [recentUpdates, setRecentUpdates] = React.useState<UpdateEvent[]>([]);
  const [currentProgress, setCurrentProgress] = React.useState<{ message: string; progress: number } | null>(null);
  const [expanded, setExpanded] = React.useState(false);
  const [wsService] = React.useState(() => 
    new WebSocketService(`${process.env.REACT_APP_WS_BASE_URL}${endpoint}`)
  );

  React.useEffect(() => {
    const handleWebSocketMessage = (message: WebSocketMessage) => {
      const update: UpdateEvent = {
        id: Date.now().toString(),
        type: message.type,
        message: getMessageText(message),
        timestamp: new Date(),
        status: getMessageStatus(message.type),
        progress: message.data.progress
      };

      setRecentUpdates(prevUpdates => 
        [update, ...prevUpdates].slice(0, maxRecentUpdates)
      );

      // Handle progress updates
      if (message.type === 'calculation_progress' && message.data.progress !== undefined) {
        setCurrentProgress({
          message: message.data.message || 'Processing...',
          progress: message.data.progress
        });
      } else if (message.type === 'calculation_complete') {
        setCurrentProgress(null);
      }
    };

    const handleConnect = () => {
      setConnected(true);
      const connectUpdate: UpdateEvent = {
        id: 'connect-' + Date.now(),
        type: 'connected',
        message: 'Connected to real-time updates',
        timestamp: new Date(),
        status: 'success'
      };
      setRecentUpdates(prev => [connectUpdate, ...prev].slice(0, maxRecentUpdates));
    };

    const handleDisconnect = () => {
      setConnected(false);
      setCurrentProgress(null);
      const disconnectUpdate: UpdateEvent = {
        id: 'disconnect-' + Date.now(),
        type: 'disconnected',
        message: 'Disconnected from real-time updates',
        timestamp: new Date(),
        status: 'error'
      };
      setRecentUpdates(prev => [disconnectUpdate, ...prev].slice(0, maxRecentUpdates));
    };

    wsService.connect({
      onMessage: handleWebSocketMessage,
      onConnect: handleConnect,
      onDisconnect: handleDisconnect,
      onError: (error) => {
        const errorUpdate: UpdateEvent = {
          id: 'error-' + Date.now(),
          type: 'error',
          message: 'WebSocket connection error',
          timestamp: new Date(),
          status: 'error'
        };
        setRecentUpdates(prev => [errorUpdate, ...prev].slice(0, maxRecentUpdates));
      }
    });

    return () => {
      wsService.disconnect();
    };
  }, [wsService, maxRecentUpdates]);

  const getMessageText = (message: WebSocketMessage): string => {
    switch (message.type) {
      case 'kpi_update':
        return `KPI updated: ${message.data.kpi?.name || 'Unknown'}`;
      case 'entity_created':
        return `New entity: ${message.data.entity?.name || 'Unknown'}`;
      case 'entity_updated':
        return `Entity updated: ${message.data.entity?.name || 'Unknown'}`;
      case 'entity_deleted':
        return `Entity deleted`;
      case 'calculation_progress':
        return message.data.message || 'Calculation in progress...';
      case 'calculation_complete':
        return 'Calculation completed';
      case 'forecast_update':
        return 'Forecast data updated';
      default:
        return message.data.message || `${message.type} event`;
    }
  };

  const getMessageStatus = (type: string): UpdateEvent['status'] => {
    if (type.includes('error') || type.includes('failed')) return 'error';
    if (type.includes('progress') || type.includes('calculating')) return 'progress';
    if (type.includes('complete') || type.includes('updated') || type.includes('created')) return 'success';
    return 'info';
  };

  const getStatusIcon = (status: UpdateEvent['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'progress':
        return <SyncIcon color="primary" fontSize="small" />;
      default:
        return <SpeedIcon color="action" fontSize="small" />;
    }
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUpIcon color="primary" />
            <Typography variant="h6">{title}</Typography>
            <Chip
              label={connected ? "Live" : "Offline"}
              size="small"
              color={connected ? "success" : "default"}
              variant={connected ? "filled" : "outlined"}
            />
          </Box>
          
          <IconButton
            onClick={() => setExpanded(!expanded)}
            size="small"
          >
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        {/* Current Progress */}
        {showProgress && currentProgress && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {currentProgress.message}
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={currentProgress.progress} 
              sx={{ height: 6, borderRadius: 3 }}
            />
            <Typography variant="caption" color="text.secondary">
              {Math.round(currentProgress.progress)}%
            </Typography>
          </Box>
        )}

        {/* Recent Updates */}
        <Collapse in={expanded}>
          <Typography variant="subtitle2" gutterBottom>
            Recent Updates ({recentUpdates.length})
          </Typography>
          
          {recentUpdates.length > 0 ? (
            <List dense>
              {recentUpdates.map((update) => (
                <ListItem key={update.id} sx={{ px: 0 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    {getStatusIcon(update.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={update.message}
                    secondary={update.timestamp.toLocaleTimeString()}
                    primaryTypographyProps={{ variant: 'body2' }}
                    secondaryTypographyProps={{ variant: 'caption' }}
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              No recent updates
            </Typography>
          )}
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default RealTimeUpdates;