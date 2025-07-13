"""Cash flow calculation engine for CashCow."""

import asyncio
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.base import BaseEntity
from ..storage.database import EntityStore
from .calculators import CalculationContext, get_calculator_registry


class CashFlowEngine:
    """Core cash flow calculation engine."""
    
    def __init__(self, store: EntityStore):
        """Initialize the cash flow engine.
        
        Args:
            store: Entity store for data access
        """
        self.store = store
        self.registry = get_calculator_registry()
        self._cache: Dict[str, Any] = {}
        self._enable_cache: bool = True
        self._entity_cache: Dict[str, List[BaseEntity]] = {}
    
    def calculate_period(self, 
                        start_date: date, 
                        end_date: date, 
                        scenario: str = "baseline") -> pd.DataFrame:
        """Calculate cash flow for a date range.
        
        Args:
            start_date: Start of calculation period
            end_date: End of calculation period
            scenario: Scenario name for calculations
            
        Returns:
            DataFrame with monthly cash flow data
        """
        # Validate date range
        if start_date > end_date:
            raise ValueError(f"Start date ({start_date}) must be before or equal to end date ({end_date})")
        
        # Check cache first
        cache_key = self.get_cache_key(start_date, end_date, scenario)
        if self._enable_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        # Generate monthly periods
        periods = self._generate_monthly_periods(start_date, end_date)
        
        # Get all entities (with caching)
        entities = self._get_entities_cached()
        
        # Calculate for each period
        results = []
        
        for period_date in periods:
            period_result = self._calculate_single_period(
                period_date, entities, scenario
            )
            period_result['period'] = period_date
            results.append(period_result)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Calculate cumulative values
        df = self._add_cumulative_calculations(df)
        
        # Cache the result
        if self._enable_cache:
            self._cache[cache_key] = df.copy()
        
        return df
    
    async def calculate_period_async(self,
                                   start_date: date,
                                   end_date: date,
                                   scenario: str = "baseline") -> pd.DataFrame:
        """Calculate cash flow for a date range using async processing.
        
        Args:
            start_date: Start of calculation period
            end_date: End of calculation period
            scenario: Scenario name for calculations
            
        Returns:
            DataFrame with monthly cash flow data
        """
        # Validate date range
        if start_date > end_date:
            raise ValueError(f"Start date ({start_date}) must be before or equal to end date ({end_date})")
        
        # Check cache first
        cache_key = self.get_cache_key(start_date, end_date, scenario)
        if self._enable_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        periods = self._generate_monthly_periods(start_date, end_date)
        entities = self._get_entities_cached()
        
        # Create tasks for parallel processing
        tasks = []
        for period_date in periods:
            task = self._calculate_single_period_async(
                period_date, entities, scenario
            )
            tasks.append(task)
        
        # Execute all calculations in parallel
        results = await asyncio.gather(*tasks)
        
        # Add period dates and convert to DataFrame
        for i, result in enumerate(results):
            result['period'] = periods[i]
        
        df = pd.DataFrame(results)
        df = self._add_cumulative_calculations(df)
        
        # Cache the result
        if self._enable_cache:
            self._cache[cache_key] = df.copy()
        
        return df
    
    def calculate_parallel(self,
                          start_date: date,
                          end_date: date,
                          scenario: str = "baseline",
                          max_workers: int = 4) -> pd.DataFrame:
        """Calculate cash flow using thread pool for parallel processing.
        
        Args:
            start_date: Start of calculation period
            end_date: End of calculation period
            scenario: Scenario name for calculations
            max_workers: Maximum number of worker threads
            
        Returns:
            DataFrame with monthly cash flow data
        """
        # Validate date range
        if start_date > end_date:
            raise ValueError(f"Start date ({start_date}) must be before or equal to end date ({end_date})")
        
        # Check cache first
        cache_key = self.get_cache_key(start_date, end_date, scenario)
        if self._enable_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        periods = self._generate_monthly_periods(start_date, end_date)
        entities = self._get_entities_cached()
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all period calculations
            future_to_period = {
                executor.submit(
                    self._calculate_single_period, 
                    period_date, 
                    entities, 
                    scenario
                ): period_date 
                for period_date in periods
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_period):
                period_date = future_to_period[future]
                try:
                    result = future.result()
                    result['period'] = period_date
                    results.append(result)
                except Exception as e:
                    print(f"Error calculating period {period_date}: {e}")
        
        # Sort by period date and convert to DataFrame
        results.sort(key=lambda x: x['period'])
        df = pd.DataFrame(results)
        df = self._add_cumulative_calculations(df)
        
        # Cache the result
        if self._enable_cache:
            self._cache[cache_key] = df.copy()
        
        return df
    
    def _generate_monthly_periods(self, start_date: date, end_date: date) -> List[date]:
        """Generate list of monthly period start dates."""
        periods = []
        current = start_date.replace(day=1)  # Start of month
        end = end_date.replace(day=1)
        
        while current <= end:
            periods.append(current)
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        return periods
    
    def _calculate_single_period(self,
                                period_date: date,
                                entities: List[BaseEntity],
                                scenario: str) -> Dict[str, float]:
        """Calculate cash flow for a single period.
        
        Args:
            period_date: Date for calculation period
            entities: List of all entities
            scenario: Scenario name
            
        Returns:
            Dictionary with calculated values for the period
        """
        context = CalculationContext(
            as_of_date=period_date,
            scenario=scenario
        )
        
        # Initialize result
        result = {
            'total_revenue': 0.0,
            'total_expenses': 0.0,
            'net_cash_flow': 0.0,
            'employee_costs': 0.0,
            'facility_costs': 0.0,
            'software_costs': 0.0,
            'equipment_costs': 0.0,
            'project_costs': 0.0,
            'grant_revenue': 0.0,
            'investment_revenue': 0.0,
            'sales_revenue': 0.0,
            'service_revenue': 0.0,
            'active_employees': 0,
            'active_projects': 0,
        }
        
        # Calculate for each entity
        for entity in entities:
            if not entity.is_active(period_date):
                continue
            
            entity_calculations = self.registry.calculate_all(entity, context.to_dict())
            
            # Aggregate by entity type
            self._aggregate_entity_calculations(
                entity, entity_calculations, result
            )
        
        # Calculate totals
        result['total_revenue'] = (
            result['grant_revenue'] + 
            result['investment_revenue'] + 
            result['sales_revenue'] + 
            result['service_revenue']
        )
        
        result['total_expenses'] = (
            result['employee_costs'] + 
            result['facility_costs'] + 
            result['software_costs'] + 
            result['equipment_costs'] + 
            result['project_costs']
        )
        
        result['net_cash_flow'] = result['total_revenue'] - result['total_expenses']
        
        return result
    
    async def _calculate_single_period_async(self,
                                           period_date: date,
                                           entities: List[BaseEntity],
                                           scenario: str) -> Dict[str, float]:
        """Async version of single period calculation."""
        # Run the synchronous calculation in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._calculate_single_period,
            period_date,
            entities,
            scenario
        )
    
    def _aggregate_entity_calculations(self,
                                     entity: BaseEntity,
                                     calculations: Dict[str, float],
                                     result: Dict[str, float]) -> None:
        """Aggregate entity calculations into period result."""
        entity_type = entity.type.lower()
        
        # Map entity types to result categories
        if entity_type == 'employee':
            result['employee_costs'] += calculations.get('total_cost_calc', 0.0)
            result['active_employees'] += 1
            
        elif entity_type == 'facility':
            result['facility_costs'] += calculations.get('recurring_calc', 0.0)
            
        elif entity_type == 'software':
            result['software_costs'] += calculations.get('recurring_calc', 0.0)
            
        elif entity_type == 'equipment':
            result['equipment_costs'] += (
                calculations.get('depreciation_calc', 0.0) +
                calculations.get('maintenance_calc', 0.0) +
                calculations.get('one_time_calc', 0.0)
            )
            
        elif entity_type == 'project':
            result['project_costs'] += calculations.get('burn_calc', 0.0)
            result['active_projects'] += 1
            
        elif entity_type == 'grant':
            result['grant_revenue'] += calculations.get('disbursement_calc', 0.0)
            
        elif entity_type == 'investment':
            result['investment_revenue'] += calculations.get('disbursement_calc', 0.0)
            
        elif entity_type == 'sale':
            result['sales_revenue'] += calculations.get('revenue_calc', 0.0)
            
        elif entity_type == 'service':
            result['service_revenue'] += calculations.get('recurring_calc', 0.0)
    
    def _add_cumulative_calculations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add cumulative calculations to the DataFrame."""
        # Validate DataFrame before processing
        if df.empty:
            # Return empty DataFrame with expected structure for consistency
            return pd.DataFrame(columns=[
                'period', 'total_revenue', 'total_expenses', 'net_cash_flow',
                'cumulative_cash_flow', 'cash_balance', 'revenue_growth_rate', 'expense_growth_rate',
                'revenue_per_employee', 'cost_per_employee', 'employee_cost_percentage',
                'facility_cost_percentage', 'project_cost_percentage', 'active_employees'
            ])
        
        # Validate that 'period' column exists
        if 'period' not in df.columns:
            raise ValueError(f"DataFrame missing required 'period' column. Available columns: {list(df.columns)}")
        
        # Sort by period to ensure correct order
        df = df.sort_values('period').copy()
        
        # Add cumulative cash flow
        df['cumulative_cash_flow'] = df['net_cash_flow'].cumsum()
        
        # Add running cash balance (assumes starting balance of 0)
        df['cash_balance'] = df['cumulative_cash_flow']
        
        # Add growth rates (fill NaN values from pct_change with 0)
        if 'total_revenue' in df.columns:
            df['revenue_growth_rate'] = df['total_revenue'].pct_change().fillna(0) * 100
        else:
            df['revenue_growth_rate'] = 0.0
        
        if 'total_expenses' in df.columns:
            df['expense_growth_rate'] = df['total_expenses'].pct_change().fillna(0) * 100
        else:
            df['expense_growth_rate'] = 0.0
        
        # Add efficiency metrics with safe division
        if 'active_employees' in df.columns and 'total_revenue' in df.columns:
            df['revenue_per_employee'] = df['total_revenue'] / df['active_employees'].replace(0, 1)
        else:
            df['revenue_per_employee'] = 0.0
        
        if 'active_employees' in df.columns and 'employee_costs' in df.columns:
            df['cost_per_employee'] = df['employee_costs'] / df['active_employees'].replace(0, 1)
        else:
            df['cost_per_employee'] = 0.0
        
        # Add percentage breakdowns with safe column access
        if 'total_expenses' in df.columns:
            total_expenses = df['total_expenses'].replace(0, 1)  # Avoid division by zero
            
            if 'employee_costs' in df.columns:
                df['employee_cost_percentage'] = (df['employee_costs'] / total_expenses) * 100
            else:
                df['employee_cost_percentage'] = 0.0
            
            if 'facility_costs' in df.columns:
                df['facility_cost_percentage'] = (df['facility_costs'] / total_expenses) * 100
            else:
                df['facility_cost_percentage'] = 0.0
            
            if 'project_costs' in df.columns:
                df['project_cost_percentage'] = (df['project_costs'] / total_expenses) * 100
            else:
                df['project_cost_percentage'] = 0.0
        else:
            df['employee_cost_percentage'] = 0.0
            df['facility_cost_percentage'] = 0.0
            df['project_cost_percentage'] = 0.0
        
        return df
    
    def aggregate_by_category(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Aggregate cash flow data by different categories.
        
        Args:
            df: Cash flow DataFrame
            
        Returns:
            Dictionary of aggregated DataFrames by category
        """
        # Validate DataFrame before processing
        if df.empty:
            # Return empty DataFrames for each category
            return {
                'revenue': pd.DataFrame(),
                'expenses': pd.DataFrame(),
                'summary': pd.DataFrame(),
                'growth': pd.DataFrame()
            }
        
        if 'period' not in df.columns:
            raise ValueError(f"DataFrame missing required 'period' column for aggregation. Available columns: {list(df.columns)}")
        
        aggregations = {}
        
        # Revenue breakdown - only include columns that exist
        revenue_cols = ['grant_revenue', 'investment_revenue', 'sales_revenue', 'service_revenue']
        available_revenue_cols = [col for col in revenue_cols if col in df.columns]
        aggregations['revenue'] = df[['period'] + available_revenue_cols].copy()
        
        # Expense breakdown - only include columns that exist
        expense_cols = ['employee_costs', 'facility_costs', 'software_costs', 'equipment_costs', 'project_costs']
        available_expense_cols = [col for col in expense_cols if col in df.columns]
        aggregations['expenses'] = df[['period'] + available_expense_cols].copy()
        
        # Summary metrics - only include columns that exist
        summary_cols = ['total_revenue', 'total_expenses', 'net_cash_flow', 'cash_balance']
        available_summary_cols = [col for col in summary_cols if col in df.columns]
        aggregations['summary'] = df[['period'] + available_summary_cols].copy()
        
        # Growth metrics - only include columns that exist
        growth_cols = ['revenue_growth_rate', 'expense_growth_rate', 'revenue_per_employee']
        available_growth_cols = [col for col in growth_cols if col in df.columns]
        aggregations['growth'] = df[['period'] + available_growth_cols].copy()
        
        return aggregations
    
    def get_cache_key(self, start_date: date, end_date: date, scenario: str) -> str:
        """Generate cache key for calculation results."""
        return f"{start_date}_{end_date}_{scenario}"
    
    def clear_cache(self) -> None:
        """Clear the calculation cache."""
        self._cache.clear()
        self._entity_cache.clear()
    
    def _get_entities_cached(self) -> List[BaseEntity]:
        """Get entities with caching to avoid repeated database queries."""
        cache_key = "all_entities"
        if self._enable_cache and cache_key in self._entity_cache:
            return self._entity_cache[cache_key]
        
        entities = self.store.query()
        if self._enable_cache:
            self._entity_cache[cache_key] = entities
        
        return entities
    
    def get_calculation_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics for a calculation period.
        
        Args:
            df: Cash flow DataFrame
            
        Returns:
            Dictionary with summary statistics
        """
        # Handle empty DataFrame case
        if df.empty:
            return {
                'total_periods': 0,
                'start_date': None,
                'end_date': None,
                'total_revenue': 0.0,
                'total_expenses': 0.0,
                'net_cash_flow': 0.0,
                'final_cash_balance': 0.0,
                'average_monthly_revenue': 0.0,
                'average_monthly_expenses': 0.0,
                'average_monthly_burn': 0.0,
                'peak_employees': 0,
                'peak_projects': 0,
                'months_cash_positive': 0,
                'months_cash_negative': 0,
            }
        
        # Safe access to columns with defaults
        def safe_column_access(df, col_name, default=0.0, operation='sum'):
            if col_name not in df.columns:
                return default
            col = df[col_name]
            if operation == 'sum':
                return col.sum()
            elif operation == 'mean':
                return col.mean()
            elif operation == 'max':
                return col.max()
            elif operation == 'min':
                return col.min()
            elif operation == 'last':
                return col.iloc[-1] if len(col) > 0 else default
            return default
        
        # Calculate summary with safe column access
        summary = {
            'total_periods': len(df),
            'start_date': safe_column_access(df, 'period', None, 'min'),
            'end_date': safe_column_access(df, 'period', None, 'max'),
            'total_revenue': safe_column_access(df, 'total_revenue', 0.0, 'sum'),
            'total_expenses': safe_column_access(df, 'total_expenses', 0.0, 'sum'),
            'net_cash_flow': safe_column_access(df, 'net_cash_flow', 0.0, 'sum'),
            'final_cash_balance': safe_column_access(df, 'cash_balance', 0.0, 'last'),
            'average_monthly_revenue': safe_column_access(df, 'total_revenue', 0.0, 'mean'),
            'average_monthly_expenses': safe_column_access(df, 'total_expenses', 0.0, 'mean'),
            'average_monthly_burn': -safe_column_access(df, 'net_cash_flow', 0.0, 'mean'),  # Negative for burn
            'peak_employees': safe_column_access(df, 'active_employees', 0, 'max'),
            'peak_projects': safe_column_access(df, 'active_projects', 0, 'max'),
        }
        
        # Calculate positive/negative cash flow months with safe column access
        if 'net_cash_flow' in df.columns:
            summary['months_cash_positive'] = (df['net_cash_flow'] > 0).sum()
            summary['months_cash_negative'] = (df['net_cash_flow'] < 0).sum()
        else:
            summary['months_cash_positive'] = 0
            summary['months_cash_negative'] = 0
        
        return summary