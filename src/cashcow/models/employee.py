"""Advanced Employee model with comprehensive calculations."""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from pydantic import field_validator

from .base import BaseEntity


class Employee(BaseEntity):
    """Advanced Employee entity with comprehensive cost calculations."""
    
    # Override type default
    type: str = "employee"
    
    # Required fields
    salary: float
    
    # Position and department
    position: Optional[str] = None
    department: Optional[str] = None
    
    # Overhead and benefits
    overhead_multiplier: float = 1.3
    benefits_annual: Optional[float] = None
    
    # Equity compensation
    equity_eligible: bool = False
    equity_shares: Optional[int] = None
    equity_start_date: Optional[date] = None
    equity_cliff_months: int = 12
    equity_vest_years: int = 4
    
    # Bonus structure
    bonus_performance_max: float = 0.0
    bonus_milestones_max: float = 0.0
    commission_rate: Optional[float] = None  # For sales roles
    
    # Allowances and stipends
    home_office_stipend: Optional[float] = None
    professional_development_annual: Optional[float] = None
    equipment_budget_annual: Optional[float] = None
    conference_budget_annual: Optional[float] = None
    
    # One-time costs
    signing_bonus: Optional[float] = None
    relocation_assistance: Optional[float] = None
    
    # Special attributes
    security_clearance: Optional[str] = None
    remote_work_eligible: bool = True
    
    @field_validator('salary')
    @classmethod
    def validate_salary(cls, v: float) -> float:
        """Ensure salary is positive."""
        if v <= 0:
            raise ValueError('salary must be positive')
        return v
    
    @field_validator('overhead_multiplier')
    @classmethod
    def validate_overhead(cls, v: float) -> float:
        """Ensure overhead multiplier is reasonable."""
        if v < 1.0 or v > 3.0:
            raise ValueError('overhead_multiplier must be between 1.0 and 3.0')
        return v
    
    def calculate_base_monthly_cost(self) -> float:
        """Calculate base monthly salary cost."""
        return self.salary / 12
    
    def calculate_overhead_cost(self, as_of_date: date) -> float:
        """Calculate monthly overhead costs (benefits, taxes, etc.)."""
        if not self.is_active(as_of_date):
            return 0.0
        
        base_monthly = self.calculate_base_monthly_cost()
        
        # Calculate overhead
        overhead_cost = base_monthly * (self.overhead_multiplier - 1.0)
        
        # Add explicit benefits if specified
        if self.benefits_annual:
            overhead_cost += self.benefits_annual / 12
        
        return overhead_cost
    
    def calculate_allowances(self, as_of_date: date) -> float:
        """Calculate monthly allowances and stipends."""
        if not self.is_active(as_of_date):
            return 0.0
        
        monthly_allowances = 0.0
        
        # Monthly stipends
        if self.home_office_stipend:
            monthly_allowances += self.home_office_stipend
        
        # Annualized allowances
        annual_allowances = [
            self.professional_development_annual,
            self.equipment_budget_annual,
            self.conference_budget_annual,
        ]
        
        for allowance in annual_allowances:
            if allowance:
                monthly_allowances += allowance / 12
        
        return monthly_allowances
    
    def calculate_one_time_costs(self, as_of_date: date) -> float:
        """Calculate one-time costs for the employee's start month."""
        if not self.is_active(as_of_date):
            return 0.0
        
        # Check if this is the employee's first month
        start_month = self.start_date.replace(day=1)
        current_month = as_of_date.replace(day=1)
        
        if start_month != current_month:
            return 0.0
        
        one_time_cost = 0.0
        
        if self.signing_bonus:
            one_time_cost += self.signing_bonus
        
        if self.relocation_assistance:
            one_time_cost += self.relocation_assistance
        
        return one_time_cost
    
    def calculate_bonus_potential(self, as_of_date: date) -> float:
        """Calculate monthly bonus potential."""
        if not self.is_active(as_of_date):
            return 0.0
        
        monthly_bonus = 0.0
        
        # Performance bonus (annualized)
        if self.bonus_performance_max > 0:
            monthly_bonus += (self.salary * self.bonus_performance_max) / 12
        
        # Milestone bonus (annualized)
        if self.bonus_milestones_max > 0:
            monthly_bonus += (self.salary * self.bonus_milestones_max) / 12
        
        return monthly_bonus
    
    def calculate_total_cost(self, as_of_date: date, include_bonus_potential: bool = True) -> float:
        """Calculate total monthly cost including all components."""
        if not self.is_active(as_of_date):
            return 0.0
        
        total_cost = 0.0
        
        # Base salary
        total_cost += self.calculate_base_monthly_cost()
        
        # Overhead (benefits, taxes, etc.)
        total_cost += self.calculate_overhead_cost(as_of_date)
        
        # Allowances and stipends
        total_cost += self.calculate_allowances(as_of_date)
        
        # One-time costs (only in first month)
        total_cost += self.calculate_one_time_costs(as_of_date)
        
        # Bonus potential
        if include_bonus_potential:
            total_cost += self.calculate_bonus_potential(as_of_date)
        
        return total_cost
    
    def is_equity_vested(self, as_of_date: date) -> bool:
        """Check if employee has passed equity cliff."""
        if not self.equity_eligible or not self.equity_start_date:
            return False
        
        cliff_date = self.equity_start_date + timedelta(days=self.equity_cliff_months * 30)
        return as_of_date >= cliff_date
    
    def calculate_equity_vested_percentage(self, as_of_date: date) -> float:
        """Calculate percentage of equity vested."""
        if not self.is_equity_vested(as_of_date):
            return 0.0
        
        # Calculate months since equity start
        months_since_start = (as_of_date.year - self.equity_start_date.year) * 12 + \
                           (as_of_date.month - self.equity_start_date.month)
        
        # Total vesting period in months
        total_vest_months = self.equity_vest_years * 12
        
        # Vested percentage (capped at 100%)
        return min(months_since_start / total_vest_months, 1.0)
    
    def calculate_equity_vested_shares(self, as_of_date: date) -> int:
        """Calculate number of shares vested."""
        if not self.equity_shares:
            return 0
        
        vested_percentage = self.calculate_equity_vested_percentage(as_of_date)
        return int(self.equity_shares * vested_percentage)
    
    def get_cost_breakdown(self, as_of_date: date) -> Dict[str, float]:
        """Get detailed cost breakdown for analysis."""
        if not self.is_active(as_of_date):
            return {}
        
        return {
            'base_salary': self.calculate_base_monthly_cost(),
            'overhead': self.calculate_overhead_cost(as_of_date),
            'allowances': self.calculate_allowances(as_of_date),
            'one_time_costs': self.calculate_one_time_costs(as_of_date),
            'bonus_potential': self.calculate_bonus_potential(as_of_date),
            'total': self.calculate_total_cost(as_of_date),
        }
    
    def get_employee_summary(self, as_of_date: date) -> Dict[str, Any]:
        """Get comprehensive employee summary."""
        return {
            'name': self.name,
            'position': self.position,
            'department': self.department,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'is_active': self.is_active(as_of_date),
            'salary': self.salary,
            'total_monthly_cost': self.calculate_total_cost(as_of_date),
            'equity_eligible': self.equity_eligible,
            'equity_vested_percentage': self.calculate_equity_vested_percentage(as_of_date),
            'equity_vested_shares': self.calculate_equity_vested_shares(as_of_date),
            'security_clearance': self.security_clearance,
            'remote_eligible': self.remote_work_eligible,
        }