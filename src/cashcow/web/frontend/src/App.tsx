import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';

// Layout
import MainLayout from './components/Layout/MainLayout';

// Pages
import Dashboard from './pages/Dashboard';
import Entities from './pages/Entities';
import EntityDetails from './pages/EntityDetails';
import Reports from './pages/Reports';
import AnalyticsReports from './pages/AnalyticsReports';

// Create MUI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            
            {/* Entity routes */}
            <Route path="entities" element={<Entities />} />
            <Route path="entities/:type" element={<Entities />} />
            <Route path="entities/:type/:id" element={<EntityDetails />} />
            <Route path="entity/:id" element={<EntityDetails />} />
            
            {/* Report routes */}
            <Route path="reports" element={<Reports />} />
            <Route path="reports/:type" element={<Reports />} />
            <Route path="analytics" element={<AnalyticsReports />} />
            
            {/* Settings and other routes */}
            <Route path="settings" element={<div>Settings page coming soon...</div>} />
            
            {/* 404 fallback */}
            <Route path="*" element={<div>Page not found</div>} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
