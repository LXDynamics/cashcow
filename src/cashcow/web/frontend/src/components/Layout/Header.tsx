// App header with navigation and user menu

import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Avatar,
  Box,
  Tooltip
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountCircleIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

interface HeaderProps {
  onMenuToggle: () => void;
  sidebarOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuToggle, sidebarOpen }) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [notificationCount] = React.useState(3);

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const handleRefreshData = () => {
    // TODO: Trigger data refresh
    console.log('Refreshing data...');
  };

  const handleSettings = () => {
    // TODO: Navigate to settings
    console.log('Opening settings...');
    handleUserMenuClose();
  };

  const handleLogout = () => {
    // TODO: Handle logout
    console.log('Logging out...');
    handleUserMenuClose();
  };

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: '#1976d2'
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          onClick={onMenuToggle}
          edge="start"
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        <Typography 
          variant="h6" 
          noWrap 
          component="div" 
          sx={{ 
            flexGrow: 0,
            mr: 3,
            fontWeight: 600
          }}
        >
          CashCow
        </Typography>

        <Typography 
          variant="subtitle1" 
          noWrap 
          component="div" 
          sx={{ 
            flexGrow: 1,
            opacity: 0.9,
            fontSize: '0.9rem'
          }}
        >
          Financial Modeling & Cash Flow Management
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Refresh Data">
            <IconButton color="inherit" onClick={handleRefreshData}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Notifications">
            <IconButton color="inherit">
              <Badge badgeContent={notificationCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>

          <Tooltip title="User Account">
            <IconButton
              size="large"
              edge="end"
              aria-label="account of current user"
              aria-controls="user-menu"
              aria-haspopup="true"
              onClick={handleUserMenuOpen}
              color="inherit"
            >
              <Avatar 
                sx={{ 
                  width: 32, 
                  height: 32,
                  bgcolor: 'rgba(255, 255, 255, 0.2)'
                }}
              >
                <AccountCircleIcon />
              </Avatar>
            </IconButton>
          </Tooltip>
        </Box>

        <Menu
          id="user-menu"
          anchorEl={anchorEl}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          keepMounted
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          open={Boolean(anchorEl)}
          onClose={handleUserMenuClose}
        >
          <MenuItem onClick={handleUserMenuClose}>
            <Avatar sx={{ width: 24, height: 24, mr: 2 }}>
              <AccountCircleIcon />
            </Avatar>
            Profile
          </MenuItem>
          
          <MenuItem onClick={handleSettings}>
            <SettingsIcon sx={{ width: 24, height: 24, mr: 2 }} />
            Settings
          </MenuItem>
          
          <MenuItem onClick={handleLogout}>
            <AccountCircleIcon sx={{ width: 24, height: 24, mr: 2 }} />
            Logout
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;