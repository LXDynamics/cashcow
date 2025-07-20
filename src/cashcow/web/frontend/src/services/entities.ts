// Entity CRUD operations service

import { api } from './api';
import { 
  Entity, 
  EntityType, 
  GrantEntity, 
  InvestmentEntity, 
  EmployeeEntity,
  FacilityEntity,
  SaleEntity,
  ServiceEntity,
  SoftwareEntity,
  EquipmentEntity,
  ProjectEntity
} from '../types/entities';
import { 
  ApiResponse, 
  PaginatedResponse, 
  EntityListParams, 
  EntityCreateRequest, 
  EntityUpdateRequest 
} from '../types/api';

// Mock data for development
const MOCK_ENTITIES: Entity[] = [
  {
    id: 'grant_1',
    type: 'grant',
    name: 'NASA SBIR Phase II',
    start_date: '2024-01-01',
    end_date: '2025-12-31',
    amount: 750000,
    agency: 'NASA',
    program: 'SBIR',
    grant_number: 'NNX24AA001G',
    indirect_cost_rate: 0.3,
    tags: ['government', 'r&d'],
    notes: 'Phase II funding for rocket engine development'
  } as GrantEntity,
  {
    id: 'investment_1',
    type: 'investment',
    name: 'Series A Round',
    start_date: '2024-03-15',
    amount: 2000000,
    investor: 'Aerospace Ventures',
    round_type: 'series_a',
    pre_money_valuation: 8000000,
    post_money_valuation: 10000000,
    tags: ['venture_capital'],
    notes: 'Series A funding round led by Aerospace Ventures'
  } as InvestmentEntity,
  {
    id: 'employee_1',
    type: 'employee',
    name: 'Jane Smith',
    start_date: '2024-01-15',
    salary: 120000,
    position: 'Senior Propulsion Engineer',
    department: 'Engineering',
    overhead_multiplier: 1.4,
    equity_eligible: true,
    equity_shares: 1000,
    tags: ['engineering', 'full_time'],
    notes: 'Lead engineer for combustion chamber design'
  } as EmployeeEntity,
  {
    id: 'employee_2',
    type: 'employee',
    name: 'Mike Johnson',
    start_date: '2024-02-01',
    salary: 95000,
    position: 'Software Engineer',
    department: 'Engineering',
    overhead_multiplier: 1.3,
    equity_eligible: true,
    equity_shares: 750,
    tags: ['engineering', 'full_time'],
    notes: 'Control systems and data acquisition software'
  } as EmployeeEntity,
  {
    id: 'facility_1',
    type: 'facility',
    name: 'Main Office & Lab',
    start_date: '2024-01-01',
    monthly_cost: 8500,
    location: '123 Aerospace Way, Los Angeles, CA',
    size_sqft: 5000,
    facility_type: 'lab',
    utilities_monthly: 1200,
    insurance_annual: 15000,
    tags: ['headquarters', 'laboratory'],
    notes: 'Primary facility with office space and testing lab'
  } as FacilityEntity,
  {
    id: 'sale_1',
    type: 'sale',
    name: 'Prototype Engine Sale',
    start_date: '2024-06-15',
    amount: 150000,
    customer: 'SpaceTech Corp',
    product: 'Prototype Rocket Engine',
    quantity: 1,
    unit_price: 150000,
    delivery_date: '2024-08-15',
    tags: ['prototype', 'customer_sale'],
    notes: 'First commercial sale of prototype engine'
  } as SaleEntity,
  {
    id: 'service_1',
    type: 'service',
    name: 'Consulting Services',
    start_date: '2024-04-01',
    monthly_amount: 15000,
    customer: 'Rocket Dynamics',
    service_type: 'Engineering Consulting',
    hourly_rate: 200,
    hours_per_month: 75,
    minimum_commitment_months: 6,
    tags: ['consulting', 'recurring'],
    notes: 'Ongoing propulsion system consulting'
  } as ServiceEntity,
  {
    id: 'software_1',
    type: 'software',
    name: 'CAD Software Licenses',
    start_date: '2024-01-01',
    monthly_cost: 2400,
    vendor: 'SolidWorks',
    license_count: 8,
    annual_cost: 28800,
    auto_renewal: true,
    support_included: true,
    tags: ['cad', 'engineering_tools'],
    notes: 'Professional CAD licenses for engineering team'
  } as SoftwareEntity,
  {
    id: 'equipment_1',
    type: 'equipment',
    name: 'Test Stand Assembly',
    start_date: '2024-02-15',
    cost: 85000,
    purchase_date: '2024-02-15',
    vendor: 'TestSystems Inc',
    category: 'lab_equipment',
    depreciation_years: 10,
    maintenance_cost_annual: 8500,
    warranty_years: 3,
    location: 'Test Lab A',
    tags: ['testing', 'lab_equipment'],
    notes: 'Primary engine testing stand for development work'
  } as EquipmentEntity,
  {
    id: 'project_1',
    type: 'project',
    name: 'Next-Gen Engine Development',
    start_date: '2024-01-01',
    end_date: '2025-06-30',
    total_budget: 500000,
    project_manager: 'Jane Smith',
    status: 'active',
    completion_percentage: 35,
    priority: 'high',
    team_members: ['Jane Smith', 'Mike Johnson'],
    planned_end_date: '2025-06-30',
    tags: ['r&d', 'high_priority'],
    notes: 'Development of next generation rocket engine with improved efficiency'
  } as ProjectEntity,
];

class EntityService {
  
  // List entities with filtering and pagination
  async listEntities(params: EntityListParams = {}): Promise<PaginatedResponse<Entity>> {
    const queryParams = new URLSearchParams();
    
    if (params.type) queryParams.set('type', params.type);
    if (params.search) queryParams.set('search', params.search);
    if (params.tags?.length) queryParams.set('tags', params.tags.join(','));
    if (params.page) queryParams.set('page', params.page.toString());
    if (params.per_page) queryParams.set('per_page', params.per_page.toString());
    if (params.sort_by) queryParams.set('sort_by', params.sort_by);
    if (params.sort_order) queryParams.set('sort_order', params.sort_order);
    
    const url = `/entities?${queryParams.toString()}`;
    
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true') {
      return this.getMockEntities(params);
    }
    
    return api.get<Entity[]>(url) as Promise<PaginatedResponse<Entity>>;
  }

  // Get single entity by ID
  async getEntity(id: string): Promise<ApiResponse<Entity>> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true') {
      const entity = MOCK_ENTITIES.find(e => e.id === id);
      if (!entity) {
        throw new Error('Entity not found');
      }
      return { success: true, data: entity };
    }
    
    return api.get<Entity>(`/entities/${id}`);
  }

  // Create new entity
  async createEntity(entityData: Partial<Entity>): Promise<ApiResponse<Entity>> {
    const request: EntityCreateRequest = { entity: entityData };
    
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true') {
      const newEntity: Entity = {
        ...entityData,
        id: `mock_${Date.now()}`,
        tags: entityData.tags || [],
      } as Entity;
      
      MOCK_ENTITIES.push(newEntity);
      return { success: true, data: newEntity };
    }
    
    return api.post<Entity>('/entities', request);
  }

  // Update existing entity
  async updateEntity(id: string, entityData: Partial<Entity>): Promise<ApiResponse<Entity>> {
    const request: EntityUpdateRequest = { entity: entityData };
    
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true') {
      const entityIndex = MOCK_ENTITIES.findIndex(e => e.id === id);
      if (entityIndex === -1) {
        throw new Error('Entity not found');
      }
      
      const updatedEntity = { ...MOCK_ENTITIES[entityIndex], ...entityData } as Entity;
      MOCK_ENTITIES[entityIndex] = updatedEntity;
      return { success: true, data: updatedEntity };
    }
    
    return api.put<Entity>(`/entities/${id}`, request);
  }

  // Delete entity
  async deleteEntity(id: string): Promise<ApiResponse<void>> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true') {
      const entityIndex = MOCK_ENTITIES.findIndex(e => e.id === id);
      if (entityIndex === -1) {
        throw new Error('Entity not found');
      }
      
      MOCK_ENTITIES.splice(entityIndex, 1);
      return { success: true };
    }
    
    return api.delete<void>(`/entities/${id}`);
  }

  // Validate entity data
  async validateEntity(entityData: Partial<Entity>): Promise<ApiResponse<{ valid: boolean; errors: any[] }>> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true') {
      const errors = this.validateEntityMock(entityData);
      return { 
        success: true, 
        data: { 
          valid: errors.length === 0, 
          errors 
        } 
      };
    }
    
    return api.post<{ valid: boolean; errors: any[] }>('/entities/validate', { entity: entityData });
  }

  // Get entities by type
  async getEntitiesByType(type: EntityType): Promise<ApiResponse<Entity[]>> {
    return this.listEntities({ type });
  }

  // Bulk operations
  async bulkDelete(ids: string[]): Promise<ApiResponse<void>> {
    // Mock implementation
    if (process.env.REACT_APP_MOCK_MODE === 'true') {
      ids.forEach(id => {
        const index = MOCK_ENTITIES.findIndex(e => e.id === id);
        if (index !== -1) {
          MOCK_ENTITIES.splice(index, 1);
        }
      });
      return { success: true };
    }
    
    return api.post<void>('/entities/bulk-delete', { ids });
  }

  // Private methods for mock implementation
  private getMockEntities(params: EntityListParams): PaginatedResponse<Entity> {
    let filteredEntities = [...MOCK_ENTITIES];
    
    // Apply filters
    if (params.type) {
      filteredEntities = filteredEntities.filter(e => e.type === params.type);
    }
    
    if (params.search) {
      const searchLower = params.search.toLowerCase();
      filteredEntities = filteredEntities.filter(e => 
        e.name.toLowerCase().includes(searchLower) ||
        e.notes?.toLowerCase().includes(searchLower)
      );
    }
    
    if (params.tags?.length) {
      filteredEntities = filteredEntities.filter(e => 
        params.tags!.some(tag => e.tags?.includes(tag))
      );
    }
    
    // Apply sorting
    if (params.sort_by) {
      const sortField = params.sort_by as keyof Entity;
      const sortOrder = params.sort_order || 'asc';
      
      filteredEntities.sort((a, b) => {
        const aVal = a[sortField];
        const bVal = b[sortField];
        
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;
        
        if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
    }
    
    // Apply pagination
    const page = params.page || 1;
    const perPage = params.per_page || 10;
    const startIndex = (page - 1) * perPage;
    const endIndex = startIndex + perPage;
    const paginatedEntities = filteredEntities.slice(startIndex, endIndex);
    
    return {
      success: true,
      data: paginatedEntities,
      total: filteredEntities.length,
      page,
      per_page: perPage,
      total_pages: Math.ceil(filteredEntities.length / perPage)
    };
  }

  private validateEntityMock(entityData: Partial<Entity>): any[] {
    const errors: any[] = [];
    
    if (!entityData.type) {
      errors.push({ field: 'type', message: 'Entity type is required' });
    }
    
    if (!entityData.name || entityData.name.trim().length === 0) {
      errors.push({ field: 'name', message: 'Entity name is required' });
    }
    
    if (!entityData.start_date) {
      errors.push({ field: 'start_date', message: 'Start date is required' });
    }
    
    // Type-specific validations
    if (entityData.type === 'employee' && !(entityData as any).salary) {
      errors.push({ field: 'salary', message: 'Salary is required for employees' });
    }
    
    if (entityData.type === 'grant' && !(entityData as any).amount) {
      errors.push({ field: 'amount', message: 'Amount is required for grants' });
    }
    
    return errors;
  }
}

export const entityService = new EntityService();
export default entityService;