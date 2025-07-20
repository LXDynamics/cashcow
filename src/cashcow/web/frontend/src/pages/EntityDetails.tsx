// Individual entity view/edit page

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  Button,
  IconButton,
  Divider,
  Card,
  CardContent,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Breadcrumbs,
  Link
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
  History as HistoryIcon,
  Share as ShareIcon
} from '@mui/icons-material';
import LoadingSpinner from '../components/Layout/LoadingSpinner';
import EntityForm from '../components/Forms/EntityForm';
import entityService from '../services/entities';
import { Entity, ENTITY_CATEGORIES, EntityType } from '../types/entities';

const EntityDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [entity, setEntity] = React.useState<Entity | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [showEditForm, setShowEditForm] = React.useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);

  const loadEntity = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      const response = await entityService.getEntity(id);
      if (response.success && response.data) {
        setEntity(response.data);
      }
    } catch (error: any) {
      console.error('Error loading entity:', error);
      setError(error.message || 'Failed to load entity');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadEntity();
  }, [id]);

  const handleEdit = () => {
    setShowEditForm(true);
  };

  const handleFormSave = async (entityData: Partial<Entity>) => {
    try {
      if (entity?.id) {
        await entityService.updateEntity(entity.id, entityData);
        setShowEditForm(false);
        loadEntity();
      }
    } catch (error: any) {
      console.error('Error updating entity:', error);
      setError(error.message || 'Failed to update entity');
    }
  };

  const handleFormCancel = () => {
    setShowEditForm(false);
  };

  const handleDelete = () => {
    setShowDeleteDialog(true);
  };

  const confirmDelete = async () => {
    if (!entity?.id) return;

    try {
      await entityService.deleteEntity(entity.id);
      navigate('/entities');
    } catch (error: any) {
      console.error('Error deleting entity:', error);
      setError(error.message || 'Failed to delete entity');
    }
  };

  const getEntityCategory = (type: string) => {
    const category = Object.entries(ENTITY_CATEGORIES).find(([_, types]) => 
      (types as readonly string[]).includes(type)
    );
    return category ? category[0] : 'other';
  };

  const getEntityTypeChip = (entityType: string) => {
    const category = getEntityCategory(entityType);
    const colors = {
      revenue: 'success',
      expenses: 'error',
      projects: 'info'
    } as const;
    
    return (
      <Chip 
        label={entityType} 
        size="small" 
        color={colors[category as keyof typeof colors] || 'default'}
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
        return { label: 'Amount', value: (entity as any).amount };
      case 'service':
        return { label: 'Monthly Amount', value: (entity as any).monthly_amount };
      case 'employee':
        return { label: 'Annual Salary', value: (entity as any).salary };
      case 'facility':
      case 'software':
        return { label: 'Monthly Cost', value: (entity as any).monthly_cost };
      case 'equipment':
        return { label: 'Cost', value: (entity as any).cost };
      case 'project':
        return { label: 'Total Budget', value: (entity as any).total_budget };
      default:
        return null;
    }
  };

  const renderEntitySpecificFields = (entity: Entity) => {
    const fields: Array<{ label: string; value: any }> = [];

    switch (entity.type) {
      case 'grant':
        const grant = entity as any;
        if (grant.agency) fields.push({ label: 'Agency', value: grant.agency });
        if (grant.program) fields.push({ label: 'Program', value: grant.program });
        if (grant.grant_number) fields.push({ label: 'Grant Number', value: grant.grant_number });
        if (grant.indirect_cost_rate !== undefined) {
          fields.push({ label: 'Indirect Cost Rate', value: `${(grant.indirect_cost_rate * 100).toFixed(1)}%` });
        }
        break;

      case 'investment':
        const investment = entity as any;
        if (investment.investor) fields.push({ label: 'Investor', value: investment.investor });
        if (investment.round_type) fields.push({ label: 'Round Type', value: investment.round_type });
        if (investment.pre_money_valuation) {
          fields.push({ label: 'Pre-Money Valuation', value: formatCurrency(investment.pre_money_valuation) });
        }
        break;

      case 'employee':
        const employee = entity as any;
        if (employee.position) fields.push({ label: 'Position', value: employee.position });
        if (employee.department) fields.push({ label: 'Department', value: employee.department });
        if (employee.overhead_multiplier) {
          fields.push({ label: 'Overhead Multiplier', value: employee.overhead_multiplier });
        }
        if (employee.equity_eligible) {
          fields.push({ label: 'Equity Eligible', value: 'Yes' });
          if (employee.equity_shares) {
            fields.push({ label: 'Equity Shares', value: employee.equity_shares.toLocaleString() });
          }
        }
        break;

      case 'facility':
        const facility = entity as any;
        if (facility.location) fields.push({ label: 'Location', value: facility.location });
        if (facility.size_sqft) fields.push({ label: 'Size', value: `${facility.size_sqft.toLocaleString()} sq ft` });
        if (facility.facility_type) fields.push({ label: 'Type', value: facility.facility_type });
        break;

      case 'software':
        const software = entity as any;
        if (software.vendor) fields.push({ label: 'Vendor', value: software.vendor });
        if (software.license_count) fields.push({ label: 'Licenses', value: software.license_count });
        if (software.auto_renewal !== undefined) {
          fields.push({ label: 'Auto Renewal', value: software.auto_renewal ? 'Yes' : 'No' });
        }
        break;

      case 'equipment':
        const equipment = entity as any;
        if (equipment.vendor) fields.push({ label: 'Vendor', value: equipment.vendor });
        if (equipment.category) fields.push({ label: 'Category', value: equipment.category });
        if (equipment.location) fields.push({ label: 'Location', value: equipment.location });
        if (equipment.depreciation_years) {
          fields.push({ label: 'Depreciation Period', value: `${equipment.depreciation_years} years` });
        }
        break;

      case 'project':
        const project = entity as any;
        if (project.project_manager) fields.push({ label: 'Project Manager', value: project.project_manager });
        if (project.status) fields.push({ label: 'Status', value: project.status });
        if (project.completion_percentage !== undefined) {
          fields.push({ label: 'Completion', value: `${project.completion_percentage}%` });
        }
        if (project.priority) fields.push({ label: 'Priority', value: project.priority });
        break;
    }

    return fields;
  };

  if (loading) {
    return <LoadingSpinner message="Loading entity details..." />;
  }

  if (error || !entity) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error || 'Entity not found'}
        </Alert>
        <Button onClick={() => navigate('/entities')}>
          Back to Entities
        </Button>
      </Box>
    );
  }

  const entityValue = getEntityValue(entity);
  const specificFields = renderEntitySpecificFields(entity);

  return (
    <Box>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link 
          color="inherit" 
          href="/entities"
          onClick={(e) => { e.preventDefault(); navigate('/entities'); }}
          sx={{ cursor: 'pointer' }}
        >
          Entities
        </Link>
        <Link 
          color="inherit" 
          href={`/entities/${getEntityCategory(entity.type)}`}
          onClick={(e) => { e.preventDefault(); navigate(`/entities/${getEntityCategory(entity.type)}`); }}
          sx={{ cursor: 'pointer' }}
        >
          {getEntityCategory(entity.type).charAt(0).toUpperCase() + getEntityCategory(entity.type).slice(1)}
        </Link>
        <Typography color="text.primary">{entity.name}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <IconButton onClick={() => navigate('/entities')} size="small">
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4" component="h1">
              {entity.name}
            </Typography>
            {getEntityTypeChip(entity.type)}
          </Box>
          <Typography variant="body2" color="text.secondary">
            Created: {new Date(entity.start_date).toLocaleDateString()}
            {entity.end_date && ` • Ends: ${new Date(entity.end_date).toLocaleDateString()}`}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton title="View History">
            <HistoryIcon />
          </IconButton>
          <IconButton title="Share">
            <ShareIcon />
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={handleEdit}
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDelete}
          >
            Delete
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Main Information */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  Name
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {entity.name}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  Type
                </Typography>
                <Box sx={{ mb: 2 }}>
                  {getEntityTypeChip(entity.type)}
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  Start Date
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {new Date(entity.start_date).toLocaleDateString()}
                </Typography>
              </Grid>
              
              {entity.end_date && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    End Date
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {new Date(entity.end_date).toLocaleDateString()}
                  </Typography>
                </Grid>
              )}
              
              {entity.tags && entity.tags.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Tags
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {entity.tags.map((tag, index) => (
                      <Chip
                        key={index}
                        label={tag}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Grid>
              )}
              
              {entity.notes && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Notes
                  </Typography>
                  <Typography variant="body1">
                    {entity.notes}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </Paper>

          {/* Type-specific Information */}
          {specificFields.length > 0 && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                {entity.type.charAt(0).toUpperCase() + entity.type.slice(1)} Details
              </Typography>
              
              <Grid container spacing={2}>
                {specificFields.map((field, index) => (
                  <Grid item xs={12} sm={6} key={index}>
                    <Typography variant="body2" color="text.secondary">
                      {field.label}
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      {field.value}
                    </Typography>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          )}
        </Grid>

        {/* Summary Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Summary
              </Typography>
              
              {entityValue && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    {entityValue.label}
                  </Typography>
                  <Typography variant="h5" color="primary">
                    {formatCurrency(entityValue.value)}
                  </Typography>
                </Box>
              )}
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Category:</Typography>
                  <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                    {getEntityCategory(entity.type)}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Status:</Typography>
                  <Chip 
                    label={entity.end_date && new Date(entity.end_date) < new Date() ? 'Inactive' : 'Active'}
                    size="small"
                    color={entity.end_date && new Date(entity.end_date) < new Date() ? 'default' : 'success'}
                  />
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Duration:</Typography>
                  <Typography variant="body2">
                    {entity.end_date 
                      ? `${Math.ceil((new Date(entity.end_date).getTime() - new Date(entity.start_date).getTime()) / (1000 * 60 * 60 * 24 * 30.44))} months`
                      : 'Ongoing'
                    }
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Edit Form Dialog */}
      <Dialog 
        open={showEditForm} 
        onClose={handleFormCancel}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Edit {entity.name}
        </DialogTitle>
        <DialogContent>
          <EntityForm
            entity={entity}
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
            Are you sure you want to delete "{entity.name}"? This action cannot be undone.
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

export default EntityDetails;