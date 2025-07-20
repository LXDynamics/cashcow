// Loading indicator component

import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  Backdrop,
  LinearProgress
} from '@mui/material';

interface LoadingSpinnerProps {
  loading?: boolean;
  message?: string;
  variant?: 'circular' | 'linear' | 'backdrop';
  size?: number | string;
  color?: 'primary' | 'secondary' | 'inherit';
  fullscreen?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  loading = true,
  message,
  variant = 'circular',
  size = 40,
  color = 'primary',
  fullscreen = false
}) => {
  if (!loading) {
    return null;
  }

  // Backdrop variant for fullscreen loading
  if (variant === 'backdrop' || fullscreen) {
    return (
      <Backdrop
        sx={{
          color: '#fff',
          zIndex: (theme) => theme.zIndex.drawer + 1,
          flexDirection: 'column',
          gap: 2
        }}
        open={loading}
      >
        <CircularProgress color="inherit" size={size} />
        {message && (
          <Typography variant="body1" color="inherit">
            {message}
          </Typography>
        )}
      </Backdrop>
    );
  }

  // Linear progress variant
  if (variant === 'linear') {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress color={color} />
        {message && (
          <Box sx={{ mt: 1, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {message}
            </Typography>
          </Box>
        )}
      </Box>
    );
  }

  // Default circular variant
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        p: 3,
        minHeight: 100
      }}
    >
      <CircularProgress color={color} size={size} />
      {message && (
        <Typography variant="body2" color="text.secondary" textAlign="center">
          {message}
        </Typography>
      )}
    </Box>
  );
};

// Inline loading component for small areas
export const InlineLoader: React.FC<{ 
  loading?: boolean;
  size?: number;
  message?: string;
}> = ({ loading = true, size = 20, message }) => {
  if (!loading) return null;

  return (
    <Box 
      sx={{ 
        display: 'inline-flex', 
        alignItems: 'center', 
        gap: 1,
        ml: 1
      }}
    >
      <CircularProgress size={size} />
      {message && (
        <Typography variant="caption" color="text.secondary">
          {message}
        </Typography>
      )}
    </Box>
  );
};

// Page loading component with skeleton effect
export const PageLoader: React.FC<{
  loading?: boolean;
  message?: string;
}> = ({ loading = true, message = 'Loading...' }) => {
  if (!loading) return null;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '50vh',
        gap: 3
      }}
    >
      <CircularProgress size={60} />
      <Typography variant="h6" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
};

// Table loading component
export const TableLoader: React.FC<{
  loading?: boolean;
  rows?: number;
}> = ({ loading = true, rows = 5 }) => {
  if (!loading) return null;

  return (
    <Box sx={{ width: '100%' }}>
      <LinearProgress sx={{ mb: 2 }} />
      {Array.from({ length: rows }).map((_, index) => (
        <Box
          key={index}
          sx={{
            height: 52,
            bgcolor: 'action.hover',
            mb: 1,
            borderRadius: 1,
            opacity: 0.7 - (index * 0.1)
          }}
        />
      ))}
    </Box>
  );
};

export default LoadingSpinner;