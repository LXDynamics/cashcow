// Navigation sidebar with menu items

import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Collapse,
  Box,
  Typography,
  Chip
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Business as BusinessIcon,
  Computer as ComputerIcon,
  Build as BuildIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  AccountBalance as AccountBalanceIcon,
  Sell as SellIcon,
  Engineering as EngineeringIcon,
  ExpandLess,
  ExpandMore,
  Assignment as AssignmentIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { NavItem } from '../../types/common';

const DRAWER_WIDTH = 280;

interface SidebarProps {
  open: boolean;
  onClose?: () => void;
  variant?: 'permanent' | 'persistent' | 'temporary';
}

const navItems: NavItem[] = [
  {
    key: 'dashboard',
    label: 'Dashboard',
    path: '/',
    icon: DashboardIcon
  },
  {
    key: 'entities',
    label: 'Entity Management',
    path: '/entities',
    icon: BusinessIcon,
    children: [
      {
        key: 'revenue',
        label: 'Revenue',
        path: '/entities/revenue',
        icon: TrendingUpIcon,
        children: [
          { key: 'grants', label: 'Grants', path: '/entities/grants', icon: AccountBalanceIcon },
          { key: 'investments', label: 'Investments', path: '/entities/investments', icon: TrendingUpIcon },
          { key: 'sales', label: 'Sales', path: '/entities/sales', icon: SellIcon },
          { key: 'services', label: 'Services', path: '/entities/services', icon: EngineeringIcon }
        ]
      },
      {
        key: 'expenses',
        label: 'Expenses',
        path: '/entities/expenses',
        icon: AssessmentIcon,
        children: [
          { key: 'employees', label: 'Employees', path: '/entities/employees', icon: PeopleIcon },
          { key: 'facilities', label: 'Facilities', path: '/entities/facilities', icon: BusinessIcon },
          { key: 'software', label: 'Software', path: '/entities/software', icon: ComputerIcon },
          { key: 'equipment', label: 'Equipment', path: '/entities/equipment', icon: BuildIcon }
        ]
      },
      {
        key: 'projects',
        label: 'Projects',
        path: '/entities/projects',
        icon: AssignmentIcon
      }
    ]
  },
  {
    key: 'reports',
    label: 'Reports & Analysis',
    path: '/reports',
    icon: AnalyticsIcon,
    children: [
      { key: 'forecast', label: 'Cash Flow Forecast', path: '/reports/forecast', icon: TrendingUpIcon },
      { key: 'kpis', label: 'KPI Dashboard', path: '/reports/kpis', icon: DashboardIcon },
      { key: 'monte-carlo', label: 'Monte Carlo Analysis', path: '/reports/monte-carlo', icon: AnalyticsIcon },
      { key: 'what-if', label: 'What-If Analysis', path: '/reports/what-if', icon: AssessmentIcon },
      { key: 'sensitivity', label: 'Sensitivity Analysis', path: '/reports/sensitivity', icon: TrendingUpIcon }
    ]
  },
  {
    key: 'settings',
    label: 'Settings',
    path: '/settings',
    icon: SettingsIcon
  }
];

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, variant = 'permanent' }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [expandedItems, setExpandedItems] = React.useState<string[]>(['entities', 'reports']);

  const handleItemClick = (item: NavItem) => {
    if (item.children) {
      toggleExpanded(item.key);
    } else {
      navigate(item.path);
      if (variant === 'temporary' && onClose) {
        onClose();
      }
    }
  };

  const toggleExpanded = (key: string) => {
    setExpandedItems(prev => 
      prev.includes(key) 
        ? prev.filter(k => k !== key)
        : [...prev, key]
    );
  };

  const isSelected = (path: string) => {
    return location.pathname === path || 
           (path !== '/' && location.pathname.startsWith(path));
  };

  const renderNavItem = (item: NavItem, level: number = 0) => {
    const Icon = item.icon;
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.key);
    const selected = isSelected(item.path);

    return (
      <React.Fragment key={item.key}>
        <ListItem disablePadding>
          <ListItemButton
            selected={selected && !hasChildren}
            onClick={() => handleItemClick(item)}
            sx={{
              pl: 2 + level * 2,
              minHeight: 48,
              '&.Mui-selected': {
                backgroundColor: 'primary.main',
                color: 'primary.contrastText',
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
                '& .MuiListItemIcon-root': {
                  color: 'primary.contrastText',
                },
              },
            }}
          >
            {Icon && (
              <ListItemIcon
                sx={{
                  minWidth: 40,
                  color: selected && !hasChildren ? 'inherit' : 'text.secondary',
                }}
              >
                <Icon />
              </ListItemIcon>
            )}
            
            <ListItemText 
              primary={item.label}
              primaryTypographyProps={{
                fontSize: level === 0 ? '0.95rem' : '0.9rem',
                fontWeight: level === 0 ? 500 : 400
              }}
            />
            
            {item.badge && (
              <Chip 
                label={item.badge} 
                size="small" 
                color="primary" 
                sx={{ ml: 1, height: 20, fontSize: '0.75rem' }}
              />
            )}
            
            {hasChildren && (
              isExpanded ? <ExpandLess /> : <ExpandMore />
            )}
          </ListItemButton>
        </ListItem>
        
        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children!.map(child => renderNavItem(child, level + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  const drawerContent = (
    <Box sx={{ overflow: 'auto', height: '100%' }}>
      <Box sx={{ p: 2, pt: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
          CashCow
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          Financial Modeling Platform
        </Typography>
      </Box>
      
      <Divider />
      
      <List sx={{ pt: 1 }}>
        {navItems.map(item => renderNavItem(item))}
      </List>
      
      <Box sx={{ flexGrow: 1 }} />
      
      <Divider />
      
      <Box sx={{ p: 2 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          Version 1.0.0
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          borderRight: '1px solid',
          borderColor: 'divider',
        },
      }}
    >
      {drawerContent}
    </Drawer>
  );
};

export default Sidebar;
export { DRAWER_WIDTH };