// Sortable, filterable entity table component

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Checkbox,
  IconButton,
  Chip,
  Box,
  Typography,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import { Entity, ENTITY_CATEGORIES, EntityType } from '../types/entities';
import { TableLoader } from './Layout/LoadingSpinner';

interface EntityTableProps {
  entities: Entity[];
  loading?: boolean;
  selectedRows?: string[];
  onSelectionChange?: (selectedIds: string[]) => void;
  onEdit?: (entity: Entity) => void;
  onDelete?: (entity: Entity) => void;
  onRowClick?: (entity: Entity) => void;
}

type SortField = keyof Entity;
type SortDirection = 'asc' | 'desc';

const EntityTable: React.FC<EntityTableProps> = ({
  entities,
  loading = false,
  selectedRows = [],
  onSelectionChange,
  onEdit,
  onDelete,
  onRowClick
}) => {
  const [sortField, setSortField] = React.useState<SortField>('name');
  const [sortDirection, setSortDirection] = React.useState<SortDirection>('asc');
  const [menuAnchor, setMenuAnchor] = React.useState<{ anchorEl: HTMLElement; entity: Entity } | null>(null);

  const handleSort = (field: SortField) => {
    const isAsc = sortField === field && sortDirection === 'asc';
    setSortDirection(isAsc ? 'desc' : 'asc');
    setSortField(field);
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!onSelectionChange) return;
    
    if (event.target.checked) {
      const allIds = entities.map(entity => entity.id!).filter(Boolean);
      onSelectionChange(allIds);
    } else {
      onSelectionChange([]);
    }
  };

  const handleSelectRow = (entityId: string) => {
    if (!onSelectionChange) return;
    
    const newSelection = selectedRows.includes(entityId)
      ? selectedRows.filter(id => id !== entityId)
      : [...selectedRows, entityId];
    
    onSelectionChange(newSelection);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, entity: Entity) => {
    event.stopPropagation();
    setMenuAnchor({ anchorEl: event.currentTarget, entity });
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleMenuAction = (action: 'view' | 'edit' | 'delete') => {
    if (!menuAnchor) return;
    
    const { entity } = menuAnchor;
    
    switch (action) {
      case 'view':
        onRowClick?.(entity);
        break;
      case 'edit':
        onEdit?.(entity);
        break;
      case 'delete':
        onDelete?.(entity);
        break;
    }
    
    handleMenuClose();
  };

  const sortedEntities = React.useMemo(() => {
    return [...entities].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      if (aValue === bValue) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;
      
      const comparison = aValue < bValue ? -1 : 1;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [entities, sortField, sortDirection]);

  const getEntityTypeChip = (entityType: string) => {
    const category = Object.entries(ENTITY_CATEGORIES).find(([_, types]) => 
      (types as readonly string[]).includes(entityType)
    );
    
    const categoryName = category ? category[0] : 'other';
    const colors = {
      revenue: 'success',
      expenses: 'error',
      projects: 'info'
    } as const;
    
    return (
      <Chip 
        label={entityType} 
        size="small" 
        color={colors[categoryName as keyof typeof colors] || 'default'}
        sx={{ textTransform: 'capitalize' }}
      />
    );
  };

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString()}`;
  };

  const getEntityValue = (entity: Entity) => {
    switch (entity.type) {
      case 'grant':
      case 'investment':
      case 'sale':
        return (entity as any).amount;
      case 'service':
        return (entity as any).monthly_amount;
      case 'employee':
        return (entity as any).salary;
      case 'facility':
      case 'software':
        return (entity as any).monthly_cost;
      case 'equipment':
        return (entity as any).cost;
      case 'project':
        return (entity as any).total_budget;
      default:
        return 0;
    }
  };

  if (loading) {
    return <TableLoader rows={8} />;
  }

  if (entities.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No entities found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Create your first entity to get started with financial modeling.
        </Typography>
      </Paper>
    );
  }

  const isAllSelected = entities.length > 0 && selectedRows.length === entities.length;
  const isPartiallySelected = selectedRows.length > 0 && selectedRows.length < entities.length;

  return (
    <TableContainer component={Paper}>
      <Table sx={{ minWidth: 750 }}>
        <TableHead>
          <TableRow>
            {onSelectionChange && (
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={isPartiallySelected}
                  checked={isAllSelected}
                  onChange={handleSelectAll}
                />
              </TableCell>
            )}
            
            <TableCell>
              <TableSortLabel
                active={sortField === 'name'}
                direction={sortField === 'name' ? sortDirection : 'asc'}
                onClick={() => handleSort('name')}
              >
                Name
              </TableSortLabel>
            </TableCell>
            
            <TableCell>
              <TableSortLabel
                active={sortField === 'type'}
                direction={sortField === 'type' ? sortDirection : 'asc'}
                onClick={() => handleSort('type')}
              >
                Type
              </TableSortLabel>
            </TableCell>
            
            <TableCell align="right">
              Value
            </TableCell>
            
            <TableCell>
              <TableSortLabel
                active={sortField === 'start_date'}
                direction={sortField === 'start_date' ? sortDirection : 'asc'}
                onClick={() => handleSort('start_date')}
              >
                Start Date
              </TableSortLabel>
            </TableCell>
            
            <TableCell>Tags</TableCell>
            
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        
        <TableBody>
          {sortedEntities.map((entity) => {
            const isSelected = selectedRows.includes(entity.id!);
            
            return (
              <TableRow
                key={entity.id}
                hover
                selected={isSelected}
                onClick={() => onRowClick?.(entity)}
                sx={{ 
                  cursor: onRowClick ? 'pointer' : 'default',
                  '&:hover': {
                    backgroundColor: 'action.hover'
                  }
                }}
              >
                {onSelectionChange && (
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      onChange={() => handleSelectRow(entity.id!)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </TableCell>
                )}
                
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight={500}>
                      {entity.name}
                    </Typography>
                    {entity.notes && (
                      <Typography variant="caption" color="text.secondary" noWrap>
                        {entity.notes.length > 50 ? `${entity.notes.substring(0, 50)}...` : entity.notes}
                      </Typography>
                    )}
                  </Box>
                </TableCell>
                
                <TableCell>
                  {getEntityTypeChip(entity.type)}
                </TableCell>
                
                <TableCell align="right">
                  <Typography variant="body2" fontWeight={500}>
                    {formatCurrency(getEntityValue(entity))}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2">
                    {new Date(entity.start_date).toLocaleDateString()}
                  </Typography>
                  {entity.end_date && (
                    <Typography variant="caption" color="text.secondary">
                      to {new Date(entity.end_date).toLocaleDateString()}
                    </Typography>
                  )}
                </TableCell>
                
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {entity.tags?.slice(0, 2).map((tag, index) => (
                      <Chip
                        key={index}
                        label={tag}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.7rem' }}
                      />
                    ))}
                    {entity.tags && entity.tags.length > 2 && (
                      <Tooltip title={entity.tags.slice(2).join(', ')}>
                        <Chip
                          label={`+${entity.tags.length - 2}`}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      </Tooltip>
                    )}
                  </Box>
                </TableCell>
                
                <TableCell align="center">
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuOpen(e, entity)}
                  >
                    <MoreVertIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      
      {/* Row Actions Menu */}
      <Menu
        anchorEl={menuAnchor?.anchorEl}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleMenuAction('view')}>
          <ListItemIcon>
            <VisibilityIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        
        {onEdit && (
          <MenuItem onClick={() => handleMenuAction('edit')}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
        )}
        
        {onDelete && (
          <MenuItem onClick={() => handleMenuAction('delete')}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        )}
      </Menu>
    </TableContainer>
  );
};

export default EntityTable;