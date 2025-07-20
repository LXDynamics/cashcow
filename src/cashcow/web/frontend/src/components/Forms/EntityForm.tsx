// Generic entity creation/editing form with validation

import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Box,
  Grid,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  OutlinedInput,
  Button,
  Typography,
  Alert,
  FormHelperText,
  Switch,
  FormControlLabel,
  Divider
} from '@mui/material';
import { Entity, EntityType, ENTITY_TYPES } from '../../types/entities';
import entityService from '../../services/entities';

interface EntityFormProps {
  entity?: Entity | null;
  defaultType?: EntityType;
  onSave: (entityData: Partial<Entity>) => void;
  onCancel: () => void;
}

interface FormData {
  type: EntityType;
  name: string;
  start_date: string;
  end_date?: string;
  tags: string[];
  notes?: string;
  
  // Common financial fields
  amount?: number;
  monthly_amount?: number;
  salary?: number;
  monthly_cost?: number;
  cost?: number;
  total_budget?: number;
  
  // Specific fields
  agency?: string;
  program?: string;
  investor?: string;
  customer?: string;
  position?: string;
  department?: string;
  location?: string;
  vendor?: string;
  
  // Boolean fields
  equity_eligible?: boolean;
  auto_renewal?: boolean;
  support_included?: boolean;
  
  // Numeric fields
  overhead_multiplier?: number;
  equity_shares?: number;
  license_count?: number;
  size_sqft?: number;
  depreciation_years?: number;
  completion_percentage?: number;
}

const EntityForm: React.FC<EntityFormProps> = ({
  entity,
  defaultType,
  onSave,
  onCancel
}) => {
  const [validationErrors, setValidationErrors] = React.useState<any[]>([]);
  const [isValidating, setIsValidating] = React.useState(false);

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting }
  } = useForm<FormData>({
    defaultValues: {
      type: entity?.type || defaultType || 'employee',
      name: entity?.name || '',
      start_date: entity?.start_date || new Date().toISOString().split('T')[0],
      end_date: entity?.end_date || '',
      tags: entity?.tags || [],
      notes: entity?.notes || '',
      
      // Map entity-specific fields
      ...getEntitySpecificDefaults(entity)
    }
  });

  const watchedType = watch('type');

  function getEntitySpecificDefaults(entity?: Entity | null) {
    if (!entity) return {};

    const defaults: any = {};
    
    // Map common fields based on entity type
    switch (entity.type) {
      case 'grant':
      case 'investment':
      case 'sale':
        defaults.amount = (entity as any).amount;
        break;
      case 'service':
        defaults.monthly_amount = (entity as any).monthly_amount;
        break;
      case 'employee':
        defaults.salary = (entity as any).salary;
        defaults.position = (entity as any).position;
        defaults.department = (entity as any).department;
        defaults.overhead_multiplier = (entity as any).overhead_multiplier;
        defaults.equity_eligible = (entity as any).equity_eligible;
        defaults.equity_shares = (entity as any).equity_shares;
        break;
      case 'facility':
      case 'software':
        defaults.monthly_cost = (entity as any).monthly_cost;
        break;
      case 'equipment':
        defaults.cost = (entity as any).cost;
        break;
      case 'project':
        defaults.total_budget = (entity as any).total_budget;
        break;
    }

    // Add other specific fields
    if ('agency' in entity) defaults.agency = (entity as any).agency;
    if ('investor' in entity) defaults.investor = (entity as any).investor;
    if ('customer' in entity) defaults.customer = (entity as any).customer;
    if ('vendor' in entity) defaults.vendor = (entity as any).vendor;
    if ('location' in entity) defaults.location = (entity as any).location;
    if ('auto_renewal' in entity) defaults.auto_renewal = (entity as any).auto_renewal;
    if ('support_included' in entity) defaults.support_included = (entity as any).support_included;
    if ('license_count' in entity) defaults.license_count = (entity as any).license_count;
    if ('size_sqft' in entity) defaults.size_sqft = (entity as any).size_sqft;
    if ('depreciation_years' in entity) defaults.depreciation_years = (entity as any).depreciation_years;
    if ('completion_percentage' in entity) defaults.completion_percentage = (entity as any).completion_percentage;

    return defaults;
  }

  const onSubmit = async (data: FormData) => {
    try {
      setIsValidating(true);
      setValidationErrors([]);

      // Validate entity data
      const validationResponse = await entityService.validateEntity(data);
      
      if (validationResponse.success && validationResponse.data) {
        if (!validationResponse.data.valid) {
          setValidationErrors(validationResponse.data.errors);
          return;
        }
      }

      // Clean up data - remove empty values
      const cleanedData = Object.entries(data).reduce((acc, [key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          acc[key] = value;
        }
        return acc;
      }, {} as any);

      onSave(cleanedData);
    } catch (error: any) {
      console.error('Form submission error:', error);
      setValidationErrors([{ field: 'general', message: error.message || 'Failed to save entity' }]);
    } finally {
      setIsValidating(false);
    }
  };

  const handleTagsChange = (event: any) => {
    const value = event.target.value;
    setValue('tags', typeof value === 'string' ? value.split(',') : value);
  };

  const renderFieldsForType = (type: EntityType) => {
    switch (type) {
      case 'grant':
        return (
          <>
            <Grid item xs={12} sm={6}>
              <Controller
                name="amount"
                control={control}
                rules={{ required: 'Amount is required', min: { value: 0, message: 'Amount must be positive' } }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Amount"
                    type="number"
                    fullWidth
                    error={!!errors.amount}
                    helperText={errors.amount?.message}
                    InputProps={{ startAdornment: '$' }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="agency"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Agency"
                    fullWidth
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="program"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Program"
                    fullWidth
                  />
                )}
              />
            </Grid>
          </>
        );

      case 'investment':
        return (
          <>
            <Grid item xs={12} sm={6}>
              <Controller
                name="amount"
                control={control}
                rules={{ required: 'Amount is required', min: { value: 0, message: 'Amount must be positive' } }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Amount"
                    type="number"
                    fullWidth
                    error={!!errors.amount}
                    helperText={errors.amount?.message}
                    InputProps={{ startAdornment: '$' }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="investor"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Investor"
                    fullWidth
                  />
                )}
              />
            </Grid>
          </>
        );

      case 'sale':
        return (
          <>
            <Grid item xs={12} sm={6}>
              <Controller
                name="amount"
                control={control}
                rules={{ required: 'Amount is required', min: { value: 0, message: 'Amount must be positive' } }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Amount"
                    type="number"
                    fullWidth
                    error={!!errors.amount}
                    helperText={errors.amount?.message}
                    InputProps={{ startAdornment: '$' }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="customer"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Customer"
                    fullWidth
                  />
                )}
              />
            </Grid>
          </>
        );

      case 'service':
        return (
          <>
            <Grid item xs={12} sm={6}>
              <Controller
                name="monthly_amount"
                control={control}
                rules={{ required: 'Monthly amount is required', min: { value: 0, message: 'Amount must be positive' } }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Monthly Amount"
                    type="number"
                    fullWidth
                    error={!!errors.monthly_amount}
                    helperText={errors.monthly_amount?.message}
                    InputProps={{ startAdornment: '$' }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="customer"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Customer"
                    fullWidth
                  />
                )}
              />
            </Grid>
          </>
        );

      case 'employee':
        return (
          <>
            <Grid item xs={12} sm={6}>
              <Controller
                name="salary"
                control={control}
                rules={{ required: 'Salary is required', min: { value: 0, message: 'Salary must be positive' } }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Annual Salary"
                    type="number"
                    fullWidth
                    error={!!errors.salary}
                    helperText={errors.salary?.message}
                    InputProps={{ startAdornment: '$' }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="position"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Position"
                    fullWidth
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="department"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Department"
                    fullWidth
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="overhead_multiplier"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Overhead Multiplier"
                    type="number"
                    fullWidth
                    helperText="Typically 1.3 - 1.5"
                    inputProps={{ step: 0.1, min: 1.0, max: 3.0 }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="equity_eligible"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Switch {...field} checked={field.value || false} />}
                    label="Equity Eligible"
                  />
                )}
              />
            </Grid>
            {watch('equity_eligible') && (
              <Grid item xs={12} sm={6}>
                <Controller
                  name="equity_shares"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Equity Shares"
                      type="number"
                      fullWidth
                    />
                  )}
                />
              </Grid>
            )}
          </>
        );

      case 'facility':
        return (
          <>
            <Grid item xs={12} sm={6}>
              <Controller
                name="monthly_cost"
                control={control}
                rules={{ required: 'Monthly cost is required', min: { value: 0, message: 'Cost must be positive' } }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Monthly Cost"
                    type="number"
                    fullWidth
                    error={!!errors.monthly_cost}
                    helperText={errors.monthly_cost?.message}
                    InputProps={{ startAdornment: '$' }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="size_sqft"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Size (sq ft)"
                    type="number"
                    fullWidth
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="location"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Location"
                    fullWidth
                  />
                )}
              />
            </Grid>
          </>
        );

      case 'software':
        return (
          <>
            <Grid item xs={12} sm={6}>
              <Controller
                name="monthly_cost"
                control={control}
                rules={{ required: 'Monthly cost is required', min: { value: 0, message: 'Cost must be positive' } }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Monthly Cost"
                    type="number"
                    fullWidth
                    error={!!errors.monthly_cost}
                    helperText={errors.monthly_cost?.message}
                    InputProps={{ startAdornment: '$' }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="vendor"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Vendor"
                    fullWidth
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="license_count"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="License Count"
                    type="number"
                    fullWidth
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="auto_renewal"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Switch {...field} checked={field.value || false} />}
                    label="Auto Renewal"
                  />
                )}
              />
            </Grid>
          </>
        );

      case 'equipment':
        return (
          <>
            <Grid item xs={12} sm={6}>
              <Controller
                name="cost"
                control={control}
                rules={{ required: 'Cost is required', min: { value: 0, message: 'Cost must be positive' } }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Cost"
                    type="number"
                    fullWidth
                    error={!!errors.cost}
                    helperText={errors.cost?.message}
                    InputProps={{ startAdornment: '$' }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="vendor"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Vendor"
                    fullWidth
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="depreciation_years"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Depreciation Years"
                    type="number"
                    fullWidth
                    helperText="Typically 3-10 years"
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="location"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Location"
                    fullWidth
                  />
                )}
              />
            </Grid>
          </>
        );

      case 'project':
        return (
          <>
            <Grid item xs={12} sm={6}>
              <Controller
                name="total_budget"
                control={control}
                rules={{ required: 'Total budget is required', min: { value: 0, message: 'Budget must be positive' } }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Total Budget"
                    type="number"
                    fullWidth
                    error={!!errors.total_budget}
                    helperText={errors.total_budget?.message}
                    InputProps={{ startAdornment: '$' }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="completion_percentage"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Completion %"
                    type="number"
                    fullWidth
                    inputProps={{ min: 0, max: 100 }}
                  />
                )}
              />
            </Grid>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)}>
      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Please fix the following errors:
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {validationErrors.map((error, index) => (
              <li key={index}>{error.message}</li>
            ))}
          </ul>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Basic Information */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            Basic Information
          </Typography>
        </Grid>

        <Grid item xs={12} sm={6}>
          <Controller
            name="type"
            control={control}
            rules={{ required: 'Entity type is required' }}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.type}>
                <InputLabel>Entity Type</InputLabel>
                <Select {...field} label="Entity Type">
                  {ENTITY_TYPES.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
                {errors.type && <FormHelperText>{errors.type.message}</FormHelperText>}
              </FormControl>
            )}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <Controller
            name="name"
            control={control}
            rules={{ required: 'Name is required' }}
            render={({ field }) => (
              <TextField
                {...field}
                label="Name"
                fullWidth
                error={!!errors.name}
                helperText={errors.name?.message}
              />
            )}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <Controller
            name="start_date"
            control={control}
            rules={{ required: 'Start date is required' }}
            render={({ field }) => (
              <TextField
                {...field}
                label="Start Date"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                error={!!errors.start_date}
                helperText={errors.start_date?.message}
              />
            )}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <Controller
            name="end_date"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="End Date (Optional)"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            )}
          />
        </Grid>

        <Grid item xs={12}>
          <Controller
            name="tags"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth>
                <InputLabel>Tags</InputLabel>
                <Select
                  {...field}
                  multiple
                  value={field.value || []}
                  onChange={handleTagsChange}
                  input={<OutlinedInput label="Tags" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {['engineering', 'r&d', 'government', 'commercial', 'full_time', 'part_time', 'consulting', 'recurring'].map((tag) => (
                    <MenuItem key={tag} value={tag}>
                      {tag}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          />
        </Grid>

        {/* Type-specific fields */}
        <Grid item xs={12}>
          <Divider sx={{ my: 2 }} />
          <Typography variant="h6" gutterBottom>
            {watchedType.charAt(0).toUpperCase() + watchedType.slice(1)} Details
          </Typography>
        </Grid>

        {renderFieldsForType(watchedType)}

        {/* Notes */}
        <Grid item xs={12}>
          <Controller
            name="notes"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Notes"
                multiline
                rows={3}
                fullWidth
              />
            )}
          />
        </Grid>

        {/* Form Actions */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 2 }}>
            <Button onClick={onCancel}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              variant="contained"
              disabled={isSubmitting || isValidating}
            >
              {isSubmitting || isValidating ? 'Saving...' : 'Save'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EntityForm;