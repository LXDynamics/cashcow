// Main layout wrapper component

import React from 'react';
import { Outlet } from 'react-router-dom';
import {
  Box,
  CssBaseline,
  useTheme,
  useMediaQuery,
  Toolbar
} from '@mui/material';
import Header from './Header';
import Sidebar, { DRAWER_WIDTH } from './Sidebar';

const MainLayout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [sidebarOpen, setSidebarOpen] = React.useState(!isMobile);

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  // Close sidebar on mobile when screen size changes
  React.useEffect(() => {
    if (isMobile && sidebarOpen) {
      setSidebarOpen(false);
    } else if (!isMobile && !sidebarOpen) {
      setSidebarOpen(true);
    }
  }, [isMobile]);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />
      
      <Header 
        onMenuToggle={handleSidebarToggle}
        sidebarOpen={sidebarOpen}
      />
      
      <Sidebar
        open={sidebarOpen}
        onClose={handleSidebarClose}
        variant={isMobile ? 'temporary' : 'permanent'}
      />
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${sidebarOpen ? DRAWER_WIDTH : 0}px)` },
          ml: { sm: sidebarOpen ? 0 : 0 },
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          backgroundColor: theme.palette.grey[50],
          minHeight: '100vh'
        }}
      >
        <Toolbar /> {/* Spacer for fixed header */}
        
        <Box sx={{ mt: 2 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};

export default MainLayout;