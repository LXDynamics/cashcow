// Entity management page

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  FilterList as FilterListIcon,
  Search as SearchIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import LoadingSpinner from '../components/Layout/LoadingSpinner';
import EntityTable from '../components/EntityTable';
import EntityForm from '../components/Forms/EntityForm';
import entityService from '../services/entities';
import { Entity, EntityType, ENTITY_TYPES, ENTITY_CATEGORIES } from '../types/entities';
import { WebSocketMessage } from '../types/api';
import { WebSocketService } from '../services/websockets';

const Entities: React.FC = () => {
  const { type } = useParams<{ type?: string }>();
  const navigate = useNavigate();
  
  const [entities, setEntities] = React.useState<Entity[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [selectedEntity, setSelectedEntity] = React.useState<Entity | null>(null);
  const [showForm, setShowForm] = React.useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);
  const [selectedRows, setSelectedRows] = React.useState<string[]>([]);
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [connected, setConnected] = React.useState(false);
  const [wsService] = React.useState(() => new WebSocketService(`${process.env.REACT_APP_WS_BASE_URL}/entities`));

  const currentEntityType = type as EntityType | undefined;

  const loadEntities = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await entityService.listEntities({
        type: currentEntityType,
        per_page: 100
      });
      
      if (response.success && response.data) {
        setEntities(response.data);
      }
    } catch (error: any) {
      console.error('Error loading entities:', error);
      setError(error.message || 'Failed to load entities');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadEntities();
    
    // Set up WebSocket connection for real-time entity updates
    const handleWebSocketMessage = (message: WebSocketMessage) => {
      if (message.type === 'entity_created') {
        const newEntity = message.data.entity;
        setEntities(prevEntities => [...prevEntities, newEntity]);
      } else if (message.type === 'entity_updated') {
        const updatedEntity = message.data.entity;
        setEntities(prevEntities => 
          prevEntities.map(entity => 
            entity.id === updatedEntity.id ? updatedEntity : entity
          )
        );
      } else if (message.type === 'entity_deleted') {
        const deletedEntityId = message.data.entityId;
        setEntities(prevEntities => 
          prevEntities.filter(entity => entity.id !== deletedEntityId)
        );
      }
    };

    const handleConnect = () => {
      setConnected(true);
      console.log('Entities WebSocket connected');
    };

    const handleDisconnect = () => {
      setConnected(false);
      console.log('Entities WebSocket disconnected');
    };

    wsService.connect({
      onMessage: handleWebSocketMessage,
      onConnect: handleConnect,
      onDisconnect: handleDisconnect,
      onError: (error) => console.error('Entities WebSocket error:', error)
    });

    return () => {
      wsService.disconnect();
    };
  }, [currentEntityType, wsService]);

  const handleCreateEntity = () => {
    setSelectedEntity(null);
    setShowForm(true);
  };

  const handleEditEntity = (entity: Entity) => {
    setSelectedEntity(entity);
    setShowForm(true);
  };

  const handleDeleteEntity = (entity: Entity) => {
    setSelectedEntity(entity);
    setShowDeleteDialog(true);
  };

  const handleFormSave = async (entityData: Partial<Entity>) => {
    try {
      if (selectedEntity) {
        // Update existing entity
        await entityService.updateEntity(selectedEntity.id!, entityData);
      } else {
        // Create new entity
        await entityService.createEntity(entityData);
      }
      
      setShowForm(false);
      setSelectedEntity(null);
      loadEntities();
    } catch (error: any) {
      console.error('Error saving entity:', error);
      setError(error.message || 'Failed to save entity');
    }
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setSelectedEntity(null);
  };

  const confirmDelete = async () => {
    if (!selectedEntity) return;

    try {
      await entityService.deleteEntity(selectedEntity.id!);
      setShowDeleteDialog(false);
      setSelectedEntity(null);
      loadEntities();
    } catch (error: any) {
      console.error('Error deleting entity:', error);
      setError(error.message || 'Failed to delete entity');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedRows.length === 0) return;

    try {
      await entityService.bulkDelete(selectedRows);
      setSelectedRows([]);
      loadEntities();
    } catch (error: any) {
      console.error('Error deleting entities:', error);
      setError(error.message || 'Failed to delete entities');
    }
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getPageTitle = () => {
    if (!currentEntityType) return 'All Entities';
    
    const category = Object.entries(ENTITY_CATEGORIES).find(([_, types]) => 
      currentEntityType && (types as readonly string[]).includes(currentEntityType)
    );
    
    const categoryName = category ? category[0] : '';
    const typeName = currentEntityType.charAt(0).toUpperCase() + currentEntityType.slice(1);
    
    return categoryName ? `${categoryName.charAt(0).toUpperCase() + categoryName.slice(1)} - ${typeName}` : typeName;
  };

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
      />
    );
  };

  if (loading) {
    return <LoadingSpinner message="Loading entities..." />;
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            {getPageTitle()}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {entities.length} {entities.length === 1 ? 'entity' : 'entities'} found
            </Typography>
            <Chip
              label={connected ? "Live Updates" : "Offline"}
              size="small"
              color={connected ? "success" : "default"}
              variant={connected ? "filled" : "outlined"}
            />
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<FilterListIcon />}
            onClick={() => navigate('/entities')}
            disabled={!currentEntityType}
          >
            All Types
          </Button>
          
          <IconButton onClick={handleMenuClick}>
            <MoreVertIcon />
          </IconButton>
          
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateEntity}
          >
            Add Entity
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Bulk Actions */}
      {selectedRows.length > 0 && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'primary.light' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">
              {selectedRows.length} {selectedRows.length === 1 ? 'entity' : 'entities'} selected
            </Typography>
            <Button
              variant="contained"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleBulkDelete}
            >
              Delete Selected
            </Button>
          </Box>
        </Paper>
      )}

      {/* Entity Table */}
      <EntityTable
        entities={entities}
        loading={false}
        selectedRows={selectedRows}
        onSelectionChange={setSelectedRows}
        onEdit={handleEditEntity}
        onDelete={handleDeleteEntity}
        onRowClick={(entity) => navigate(`/entities/${entity.id}`)}
      />

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => { handleMenuClose(); /* TODO: Export */ }}>
          <ListItemIcon>
            <DownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Export Data</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => { handleMenuClose(); loadEntities(); }}>
          <ListItemIcon>
            <SearchIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Refresh</ListItemText>
        </MenuItem>
      </Menu>

      {/* Entity Form Dialog */}
      <Dialog 
        open={showForm} 
        onClose={handleFormCancel}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedEntity ? 'Edit Entity' : 'Create New Entity'}
        </DialogTitle>
        <DialogContent>
          <EntityForm
            entity={selectedEntity}
            defaultType={currentEntityType}
            onSave={handleFormSave}
            onCancel={handleFormCancel}
          />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedEntity?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDeleteDialog(false)}>
            Cancel
          </Button>
          <Button onClick={confirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Entities;