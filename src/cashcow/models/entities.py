"""Entity type models for the CashCow system."""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import field_validator

from .base import BaseEntity


class Employee(BaseEntity):
    """Employee entity with flexible attributes."""
    
    # Override type default
    type: str = "employee"
    
    # Required employee fields
    salary: float
    
    # Common optional fields with defaults
    position: Optional[str] = None
    department: Optional[str] = None
    overhead_multiplier: float = 1.0
    equity_eligible: bool = False
    equity_shares: Optional[int] = None
    equity_start_date: Optional[date] = None
    
    # Pay frequency and structure
    pay_frequency: str = 'monthly'
    hours_per_week: Optional[float] = None
    bonus_percentage: Optional[float] = None
    allowances: Optional[Dict[str, float]] = None
    benefits: Optional[Dict[str, float]] = None
    
    # Equity vesting parameters
    vesting_years: Optional[int] = None
    cliff_years: Optional[int] = None
    
    @field_validator('salary')
    @classmethod
    def validate_salary(cls, v: float) -> float:
        """Ensure salary is positive."""
        if v <= 0:
            raise ValueError('salary must be positive')
        return v
    
    def calculate_total_cost(self, as_of_date: date) -> float:
        """Calculate total monthly cost including overhead."""
        if not self.is_active(as_of_date):
            return 0.0
        
        monthly_salary = self.salary / 12
        total_cost = monthly_salary * self.overhead_multiplier
        
        # Add any monthly allowances
        for field in ['home_office_stipend', 'professional_development_monthly']:
            value = self.get_field(field, 0)
            if value:
                total_cost += value
        
        return total_cost


class Grant(BaseEntity):
    """Grant funding entity."""
    
    type: str = "grant"
    
    # Required fields
    amount: float
    
    # Common optional fields
    agency: Optional[str] = None
    payment_schedule: Optional[List[Dict[str, Any]]] = None
    reporting_requirements: Optional[str] = None
    indirect_cost_rate: float = 0.0
    milestones: Optional[List[Dict[str, Any]]] = None
    
    def calculate_monthly_disbursement(self, as_of_date: date) -> float:
        """Calculate expected monthly disbursement."""
        if not self.is_active(as_of_date):
            return 0.0
        
        # If payment schedule exists, use it
        if self.payment_schedule:
            return self._calculate_scheduled_payment(as_of_date)
        
        # Otherwise, distribute evenly over grant period
        return self._calculate_even_disbursement(as_of_date)
    
    def _calculate_scheduled_payment(self, as_of_date: date) -> float:
        """Calculate payment based on schedule."""
        current_month = as_of_date.replace(day=1)
        monthly_payment = 0.0
        
        for payment in self.payment_schedule:
            if 'date' in payment and 'amount' in payment:
                payment_date = date.fromisoformat(payment['date']) if isinstance(payment['date'], str) else payment['date']
                payment_month = payment_date.replace(day=1)
                
                if payment_month == current_month:
                    monthly_payment += payment['amount']
        
        return monthly_payment
    
    def _calculate_even_disbursement(self, as_of_date: date) -> float:
        """Calculate even monthly disbursement."""
        if not self.end_date:
            # If no end date, assume 2-year grant
            grant_months = 24
        else:
            grant_months = (self.end_date.year - self.start_date.year) * 12 + \
                         (self.end_date.month - self.start_date.month)
        
        return self.amount / max(grant_months, 1)
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Ensure amount is positive."""
        if v <= 0:
            raise ValueError('amount must be positive')
        return v


class Investment(BaseEntity):
    """Investment funding entity."""
    
    type: str = "investment"
    
    # Required fields
    amount: float
    
    # Common optional fields
    investor: Optional[str] = None
    round_name: Optional[str] = None
    valuation: Optional[float] = None
    terms: Optional[Dict[str, Any]] = None
    disbursement_schedule: Optional[List[Dict[str, Any]]] = None
    
    def calculate_monthly_disbursement(self, as_of_date: date) -> float:
        """Calculate monthly investment disbursement."""
        if not self.is_active(as_of_date):
            return 0.0
        
        # Use disbursement schedule if available
        if self.disbursement_schedule:
            return self._calculate_scheduled_disbursement(as_of_date)
        
        # Otherwise assume lump sum in first month
        return self._calculate_lump_sum(as_of_date)
    
    def _calculate_scheduled_disbursement(self, as_of_date: date) -> float:
        """Calculate scheduled disbursement."""
        current_month = as_of_date.replace(day=1)
        monthly_amount = 0.0
        
        for disbursement in self.disbursement_schedule:
            if 'date' in disbursement and 'amount' in disbursement:
                disbursement_date = date.fromisoformat(disbursement['date']) if isinstance(disbursement['date'], str) else disbursement['date']
                disbursement_month = disbursement_date.replace(day=1)
                
                if disbursement_month == current_month:
                    monthly_amount += disbursement['amount']
        
        return monthly_amount
    
    def _calculate_lump_sum(self, as_of_date: date) -> float:
        """Calculate lump sum disbursement in first month."""
        start_month = self.start_date.replace(day=1)
        current_month = as_of_date.replace(day=1)
        
        if start_month == current_month:
            return self.amount
        
        return 0.0


class Sale(BaseEntity):
    """Product sale entity."""
    
    type: str = "sale"
    
    # Required fields
    amount: float
    
    # Common optional fields
    customer: Optional[str] = None
    product: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    delivery_date: Optional[date] = None


class Service(BaseEntity):
    """Service contract entity."""
    
    type: str = "service"
    
    # Required fields
    monthly_amount: float
    
    # Common optional fields
    customer: Optional[str] = None
    service_type: Optional[str] = None
    hours_per_month: Optional[float] = None
    hourly_rate: Optional[float] = None


class Facility(BaseEntity):
    """Facility expense entity."""
    
    type: str = "facility"
    
    # Required fields
    monthly_cost: float
    
    # Common optional fields
    location: Optional[str] = None
    size_sqft: Optional[int] = None
    utilities_monthly: Optional[float] = None
    insurance_annual: Optional[float] = None
    payment_frequency: str = 'monthly'
    
    def calculate_monthly_cost(self, as_of_date: date) -> float:
        """Calculate total monthly facility cost."""
        if not self.is_active(as_of_date):
            return 0.0
        
        # For annual payment frequency, only charge in January
        if self.payment_frequency == 'annual':
            if as_of_date.month == 1:
                return self.monthly_cost
            else:
                return 0.0
        
        total = self.monthly_cost
        
        # Add utilities
        if self.utilities_monthly:
            total += self.utilities_monthly
        
        # Add monthly portion of annual costs
        if self.insurance_annual:
            total += self.insurance_annual / 12
        
        # Add any other monthly costs
        for field in ['security_monthly', 'maintenance_monthly']:
            value = self.get_field(field, 0)
            if value:
                total += value
        
        return total


class Software(BaseEntity):
    """Software subscription entity."""
    
    type: str = "software"
    
    # Required fields
    monthly_cost: float
    
    # Common optional fields
    vendor: Optional[str] = None
    license_count: Optional[int] = None
    annual_cost: Optional[float] = None  # For annual subscriptions
    purchase_price: Optional[float] = None
    useful_life_years: Optional[int] = None
    depreciation_method: str = 'straight-line'
    maintenance_percentage: Optional[float] = None
    
    def calculate_monthly_cost(self, as_of_date: date) -> float:
        """Calculate monthly cost, converting annual if needed."""
        if not self.is_active(as_of_date):
            return 0.0
        
        if self.annual_cost:
            return self.annual_cost / 12
        return self.monthly_cost
    
    def calculate_monthly_depreciation(self, as_of_date: date) -> float:
        """Calculate monthly depreciation for software."""
        if not self.purchase_price or not self.useful_life_years:
            return 0.0
        
        return self.purchase_price / (self.useful_life_years * 12)
    
    def calculate_monthly_maintenance(self, as_of_date: date) -> float:
        """Calculate monthly maintenance cost for software."""
        if not self.purchase_price or not self.maintenance_percentage:
            return 0.0
        
        return (self.purchase_price * self.maintenance_percentage) / 12


class Equipment(BaseEntity):
    """Equipment purchase entity."""
    
    type: str = "equipment"
    
    # Required fields
    cost: float
    purchase_date: date
    
    # Common optional fields
    vendor: Optional[str] = None
    category: Optional[str] = None
    depreciation_years: Optional[int] = None
    purchase_price: Optional[float] = None
    useful_life_years: Optional[int] = None
    depreciation_method: str = 'straight-line'
    maintenance_percentage: Optional[float] = None
    maintenance_cost: Optional[float] = None
    
    def calculate_monthly_depreciation(self, as_of_date: date) -> float:
        """Calculate monthly depreciation for equipment."""
        if not self.purchase_price or not self.useful_life_years:
            return 0.0
        
        # Check if we're still in depreciation period
        years_since_purchase = (as_of_date - self.purchase_date).days / 365.25
        
        if years_since_purchase > self.useful_life_years:
            return 0.0
        
        return self.purchase_price / (self.useful_life_years * 12)
    
    def calculate_monthly_maintenance(self, as_of_date: date) -> float:
        """Calculate monthly maintenance cost for equipment."""
        if self.maintenance_cost:
            return self.maintenance_cost
        
        if self.purchase_price and self.maintenance_percentage:
            return (self.purchase_price * self.maintenance_percentage) / 12
        
        return 0.0


class Project(BaseEntity):
    """R&D project entity with milestones."""
    
    type: str = "project"
    
    # Required fields
    total_budget: float
    
    # Common optional fields
    milestones: Optional[List[Dict[str, Any]]] = None
    team_members: Optional[List[str]] = None
    status: str = "planned"
    
    def get_active_milestone(self, as_of_date: date) -> Optional[Dict[str, Any]]:
        """Get the current active milestone."""
        if not self.milestones:
            return None
        
        for milestone in self.milestones:
            if 'date' in milestone:
                milestone_date = date.fromisoformat(milestone['date'])
                if milestone_date <= as_of_date and milestone.get('status') != 'completed':
                    return milestone
        
        return None
    
    def calculate_monthly_burn_rate(self, as_of_date: date) -> float:
        """Calculate monthly burn rate for project."""
        if not self.is_active(as_of_date):
            return 0.0
        
        # Simple burn rate calculation based on total budget and duration
        if self.end_date:
            months = (self.end_date.year - self.start_date.year) * 12 + \
                    (self.end_date.month - self.start_date.month)
            return self.total_budget / max(months, 1)
        
        return 0.0


# Entity type mapping for dynamic loading
ENTITY_TYPES = {
    'employee': Employee,
    'grant': Grant,
    'investment': Investment,
    'sale': Sale,
    'service': Service,
    'facility': Facility,
    'software': Software,
    'equipment': Equipment,
    'project': Project,
}


def create_entity(data: Dict[str, Any]) -> BaseEntity:
    """Create the appropriate entity type from a dictionary."""
    entity_type = data.get('type', '').lower()
    
    if entity_type in ENTITY_TYPES:
        entity_class = ENTITY_TYPES[entity_type]
        return entity_class(**data)
    else:
        # Fall back to base entity for unknown types
        return BaseEntity(**data)