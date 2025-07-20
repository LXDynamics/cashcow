// Entity type definitions matching the backend API

export interface BaseEntity {
  id?: string;
  type: string;
  name: string;
  start_date: string;
  end_date?: string | null;
  tags?: string[];
  notes?: string | null;
}

export interface GrantEntity extends BaseEntity {
  type: 'grant';
  amount: number;
  agency?: string;
  program?: string;
  grant_number?: string;
  indirect_cost_rate?: number;
  payment_schedule?: PaymentScheduleItem[];
  milestones?: Milestone[];
  reporting_requirements?: string;
  reporting_frequency?: string;
}

export interface InvestmentEntity extends BaseEntity {
  type: 'investment';
  amount: number;
  investor?: string;
  round_type?: string;
  pre_money_valuation?: number;
  post_money_valuation?: number;
  share_price?: number;
  shares_issued?: number;
  liquidation_preference?: number;
  board_seats?: number;
  disbursement_schedule?: PaymentScheduleItem[];
}

export interface SaleEntity extends BaseEntity {
  type: 'sale';
  amount: number;
  customer?: string;
  product?: string;
  quantity?: number;
  unit_price?: number;
  delivery_date?: string;
  payment_terms?: string;
  payment_schedule?: PaymentScheduleItem[];
}

export interface ServiceEntity extends BaseEntity {
  type: 'service';
  monthly_amount: number;
  customer?: string;
  service_type?: string;
  hourly_rate?: number;
  hours_per_month?: number;
  minimum_commitment_months?: number;
  auto_renewal?: boolean;
}

export interface EmployeeEntity extends BaseEntity {
  type: 'employee';
  salary: number;
  position?: string;
  department?: string;
  overhead_multiplier?: number;
  equity_eligible?: boolean;
  equity_shares?: number;
  equity_start_date?: string;
  equity_cliff_months?: number;
  equity_vest_years?: number;
  bonus_performance_max?: number;
  signing_bonus?: number;
  benefits_annual?: number;
  home_office_stipend?: number;
}

export interface FacilityEntity extends BaseEntity {
  type: 'facility';
  monthly_cost: number;
  location?: string;
  size_sqft?: number;
  facility_type?: string;
  utilities_monthly?: number;
  insurance_annual?: number;
  lease_start_date?: string;
  lease_end_date?: string;
  maintenance_monthly?: number;
  certifications?: Certification[];
}

export interface SoftwareEntity extends BaseEntity {
  type: 'software';
  monthly_cost: number;
  vendor?: string;
  license_count?: number;
  annual_cost?: number;
  contract_end_date?: string;
  auto_renewal?: boolean;
  per_user_cost?: number;
  support_included?: boolean;
}

export interface EquipmentEntity extends BaseEntity {
  type: 'equipment';
  cost: number;
  purchase_date: string;
  vendor?: string;
  category?: string;
  depreciation_years?: number;
  maintenance_cost_annual?: number;
  warranty_years?: number;
  location?: string;
  assigned_to?: string;
}

export interface ProjectEntity extends BaseEntity {
  type: 'project';
  total_budget: number;
  project_manager?: string;
  status?: 'planned' | 'active' | 'on_hold' | 'completed' | 'cancelled';
  completion_percentage?: number;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  milestones?: Milestone[];
  team_members?: string[];
  planned_end_date?: string;
  budget_categories?: Record<string, number>;
}

// Supporting types
export interface PaymentScheduleItem {
  date: string;
  amount: number;
}

export interface Milestone {
  name: string;
  date: string;
  amount?: number;
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled';
}

export interface Certification {
  name: string;
  renewal_date: string;
  cost?: number;
}

// Union type for all entities
export type Entity = 
  | GrantEntity 
  | InvestmentEntity 
  | SaleEntity 
  | ServiceEntity 
  | EmployeeEntity 
  | FacilityEntity 
  | SoftwareEntity 
  | EquipmentEntity 
  | ProjectEntity;

// Entity type enumeration
export const ENTITY_TYPES = [
  'grant',
  'investment', 
  'sale',
  'service',
  'employee',
  'facility',
  'software',
  'equipment',
  'project'
] as const;

export type EntityType = typeof ENTITY_TYPES[number];

// Entity categories for grouping
export const ENTITY_CATEGORIES: Record<string, EntityType[]> = {
  revenue: ['grant', 'investment', 'sale', 'service'],
  expenses: ['employee', 'facility', 'software', 'equipment'],
  projects: ['project']
};