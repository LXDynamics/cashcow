// API request and response types

import { Entity, EntityType } from './entities';

// Common API response structure
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Pagination
export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Entity API operations
export interface EntityListParams {
  type?: EntityType;
  search?: string;
  tags?: string[];
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface EntityCreateRequest {
  entity: Partial<Entity>;
}

export interface EntityUpdateRequest {
  entity: Partial<Entity>;
}

export interface EntityDeleteRequest {
  id: string;
}

// Calculation and forecast types
export interface ForecastParams {
  months?: number;
  start_date?: string;
  scenario?: string;
}

export interface ForecastResponse {
  months: ForecastMonth[];
  summary: ForecastSummary;
}

export interface ForecastMonth {
  month: string;
  revenue: number;
  expenses: number;
  net_cash_flow: number;
  cumulative_cash_flow: number;
  burn_rate: number;
}

export interface ForecastSummary {
  total_revenue: number;
  total_expenses: number;
  net_cash_flow: number;
  average_burn_rate: number;
  runway_months: number;
}

// KPI types
export interface KPIData {
  name: string;
  value: number;
  unit: string;
  change?: number;
  change_period?: string;
  trend?: 'up' | 'down' | 'stable';
  category?: 'revenue' | 'expenses' | 'cash_flow' | 'other';
}

export interface KPIResponse extends ApiResponse<KPIData[]> {}

// Report types
export interface ReportParams {
  type: 'kpi' | 'cashflow' | 'summary';
  format?: 'json' | 'html' | 'csv';
  start_date?: string;
  end_date?: string;
  scenario?: string;
}

export interface ReportResponse extends ApiResponse<any> {
  report_url?: string;
  download_url?: string;
}

// Analysis types
export interface MonteCarloParams {
  iterations?: number;
  variables?: string[];
  confidence_level?: number;
}

export interface WhatIfParams {
  scenario: string;
  variables?: Record<string, number>;
}

export interface SensitivityParams {
  variable: string;
  range?: [number, number];
  steps?: number;
}

// Scenario types
export interface Scenario {
  name: string;
  description?: string;
  variables: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface ScenarioListResponse extends ApiResponse<Scenario[]> {}

export interface ScenarioCreateRequest {
  scenario: Omit<Scenario, 'created_at' | 'updated_at'>;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'entity_update' | 'calculation_complete' | 'validation_error' | 'system_status' | 
        'kpi_update' | 'entity_created' | 'entity_updated' | 'entity_deleted' | 
        'calculation_progress' | 'forecast_update';
  data: any;
  timestamp: string;
}

// Error types
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  field?: string;
}

export interface ValidationError extends ApiError {
  field: string;
  value: any;
  constraint: string;
}