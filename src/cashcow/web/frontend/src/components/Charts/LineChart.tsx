// Basic line chart component using Chart.js

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Box } from '@mui/material';
import { ChartData } from '../../types/common';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface LineChartProps {
  data: ChartData;
  options?: ChartOptions<'line'>;
  height?: number;
  width?: number;
}

const defaultOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
    },
    title: {
      display: false,
    },
  },
  scales: {
    x: {
      display: true,
      title: {
        display: true,
        text: 'Time Period'
      }
    },
    y: {
      display: true,
      title: {
        display: true,
        text: 'Value'
      },
      beginAtZero: true
    }
  },
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  elements: {
    point: {
      radius: 4,
      hoverRadius: 6
    }
  }
};

const LineChart: React.FC<LineChartProps> = ({
  data,
  options = {},
  height = 400,
  width
}) => {
  // Merge default options with provided options
  const chartOptions = React.useMemo(() => {
    return {
      ...defaultOptions,
      ...options,
      plugins: {
        ...defaultOptions.plugins,
        ...options.plugins
      },
      scales: {
        ...defaultOptions.scales,
        ...options.scales
      }
    };
  }, [options]);

  return (
    <Box 
      sx={{ 
        height: height,
        width: width || '100%',
        position: 'relative'
      }}
    >
      <Line 
        data={data} 
        options={chartOptions}
      />
    </Box>
  );
};

export default LineChart;