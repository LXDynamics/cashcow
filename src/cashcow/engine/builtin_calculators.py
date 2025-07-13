"""Built-in calculators for CashCow entities."""

from datetime import date
from typing import Any, Dict

from ..models.base import BaseEntity
from ..models.entities import Employee, Grant, Investment, Sale, Service, Facility, Software, Equipment, Project
from .calculators import register_calculator, CalculatorRegistry


# Employee Calculators
@register_calculator(
    "employee", 
    "salary_calc",
    "Calculate monthly salary cost"
)
def calculate_employee_salary(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly salary for an employee."""
    if not isinstance(entity, Employee):
        return 0.0
    
    as_of_date = context.get('as_of_date', context.get('period_start', date.today()))
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Calculate base monthly salary
    monthly_salary = entity.salary / 12
    return monthly_salary


@register_calculator(
    "employee", 
    "overhead_calc",
    "Calculate monthly overhead costs",
    dependencies=["salary_calc"]
)
def calculate_employee_overhead(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly overhead costs for an employee."""
    if not isinstance(entity, Employee):
        return 0.0
    
    as_of_date = context.get('as_of_date', context.get('period_start', date.today()))
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Calculate overhead based on salary
    monthly_salary = entity.salary / 12
    overhead_cost = monthly_salary * (entity.overhead_multiplier - 1.0)
    return overhead_cost


@register_calculator(
    "employee", 
    "total_cost_calc",
    "Calculate total monthly cost including all components",
    dependencies=["salary_calc", "overhead_calc"]
)
def calculate_employee_total_cost(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate total monthly cost for an employee."""
    if not isinstance(entity, Employee):
        return 0.0
    
    as_of_date = context.get('as_of_date', context.get('period_start', date.today()))
    return entity.calculate_total_cost(as_of_date)


@register_calculator(
    "employee", 
    "equity_calc",
    "Calculate vested equity value"
)
def calculate_employee_equity(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate vested equity value for an employee."""
    if not isinstance(entity, Employee):
        return 0.0
    
    as_of_date = context.get('as_of_date', context.get('period_start', date.today()))
    
    if not entity.is_active(as_of_date) or not entity.equity_eligible or not entity.equity_shares:
        return 0.0
    
    # Simple equity calculation - get share price from context
    share_price = context.get('share_price', 0.0)
    
    if share_price == 0.0:
        return 0.0
    
    # Calculate vested shares (simplified: assume 4 year vesting with 1 year cliff)
    equity_start = entity.equity_start_date or entity.start_date
    vesting_years = context.get('vesting_years', 4)
    cliff_years = context.get('cliff_years', 1)
    
    # Calculate time since equity start
    time_since_start = (as_of_date - equity_start).days / 365.25
    
    if time_since_start < cliff_years:
        return 0.0  # Before cliff
    
    # Calculate vested percentage
    vested_percentage = min(time_since_start / vesting_years, 1.0)
    vested_shares = entity.equity_shares * vested_percentage
    
    # Return monthly vesting value
    monthly_vesting = (entity.equity_shares / vesting_years / 12) * share_price
    return monthly_vesting


# Grant Calculators
@register_calculator(
    "grant", 
    "disbursement_calc",
    "Calculate monthly grant disbursement"
)
def calculate_grant_disbursement(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly disbursement for a grant."""
    if not isinstance(entity, Grant):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    return entity.calculate_monthly_disbursement(as_of_date)


@register_calculator(
    "grant", 
    "milestone_calc",
    "Calculate milestone-based payments"
)
def calculate_grant_milestone_payment(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate milestone-based payment for a grant."""
    if not isinstance(entity, Grant):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    
    # Check if there are any milestones due this month
    if not entity.payment_schedule:
        return 0.0
    
    current_month = as_of_date.replace(day=1)
    monthly_payment = 0.0
    
    for payment in entity.payment_schedule:
        if 'date' in payment and 'amount' in payment:
            payment_date = date.fromisoformat(payment['date']) if isinstance(payment['date'], str) else payment['date']
            payment_month = payment_date.replace(day=1)
            
            if payment_month == current_month:
                monthly_payment += payment['amount']
    
    return monthly_payment


# Investment Calculators
@register_calculator(
    "investment", 
    "disbursement_calc",
    "Calculate monthly investment disbursement"
)
def calculate_investment_disbursement(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly disbursement for an investment."""
    if not isinstance(entity, Investment):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    return entity.calculate_monthly_disbursement(as_of_date)


# Sale Calculators
@register_calculator(
    "sale", 
    "revenue_calc",
    "Calculate monthly revenue from sale"
)
def calculate_sale_revenue(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly revenue from a sale."""
    if not isinstance(entity, Sale):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    return entity.calculate_monthly_revenue(as_of_date)


# Service Calculators
@register_calculator(
    "service", 
    "recurring_calc",
    "Calculate monthly recurring service revenue"
)
def calculate_service_recurring(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly recurring revenue from a service."""
    if not isinstance(entity, Service):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    return entity.calculate_monthly_revenue(as_of_date)


# Facility Calculators
@register_calculator(
    "facility", 
    "recurring_calc",
    "Calculate monthly facility costs"
)
def calculate_facility_recurring(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly recurring costs for a facility."""
    if not isinstance(entity, Facility):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    return entity.calculate_monthly_cost(as_of_date)


@register_calculator(
    "facility", 
    "utilities_calc",
    "Calculate monthly utility costs"
)
def calculate_facility_utilities(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly utility costs for a facility."""
    if not isinstance(entity, Facility):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    return entity.utilities_monthly or 0.0


# Software Calculators
@register_calculator(
    "software", 
    "recurring_calc",
    "Calculate monthly software costs"
)
def calculate_software_recurring(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly recurring costs for software."""
    if not isinstance(entity, Software):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    return entity.calculate_monthly_cost(as_of_date)


# Equipment Calculators
@register_calculator(
    "equipment", 
    "depreciation_calc",
    "Calculate monthly depreciation expense"
)
def calculate_equipment_depreciation(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly depreciation for equipment."""
    if not isinstance(entity, Equipment):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    return entity.calculate_monthly_depreciation(as_of_date)


@register_calculator(
    "equipment", 
    "maintenance_calc",
    "Calculate monthly maintenance costs"
)
def calculate_equipment_maintenance(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly maintenance costs for equipment."""
    if not isinstance(entity, Equipment):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    return entity.calculate_monthly_maintenance(as_of_date)


@register_calculator(
    "equipment", 
    "one_time_calc",
    "Calculate one-time equipment purchase cost"
)
def calculate_equipment_one_time(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate one-time purchase cost for equipment."""
    if not isinstance(entity, Equipment):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    
    # Return cost only in the month of purchase
    purchase_month = entity.purchase_date.replace(day=1)
    current_month = as_of_date.replace(day=1)
    
    return entity.cost if purchase_month == current_month else 0.0


# Project Calculators
@register_calculator(
    "project", 
    "burn_calc",
    "Calculate monthly project burn rate"
)
def calculate_project_burn(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly burn rate for a project."""
    if not isinstance(entity, Project):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    return entity.calculate_monthly_burn_rate(as_of_date)


@register_calculator(
    "project", 
    "milestone_calc",
    "Calculate milestone-based project costs"
)
def calculate_project_milestone(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate milestone-based costs for a project."""
    if not isinstance(entity, Project):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    
    # Check if there are any milestones due this month
    if not entity.milestones:
        return 0.0
    
    current_month = as_of_date.replace(day=1)
    monthly_cost = 0.0
    
    for milestone in entity.milestones:
        if 'planned_date' in milestone and 'budget' in milestone:
            milestone_date = milestone['planned_date']
            if isinstance(milestone_date, str):
                milestone_date = date.fromisoformat(milestone_date)
            
            milestone_month = milestone_date.replace(day=1)
            
            if milestone_month == current_month:
                monthly_cost += milestone['budget']
    
    return monthly_cost


# Aggregate Calculators
@register_calculator(
    "employee", 
    "total_compensation_calc",
    "Calculate total annual compensation value",
    dependencies=["salary_calc", "equity_calc"]
)
def calculate_total_compensation(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate total annual compensation including equity."""
    if not isinstance(entity, Employee):
        return 0.0
    
    as_of_date = context.get('as_of_date', date.today())
    equity_value_per_share = context.get('equity_value_per_share', 0.0)
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Annual salary
    annual_comp = entity.salary
    
    # Add potential bonuses (with null checks)
    if entity.bonus_performance_max and entity.bonus_performance_max > 0:
        annual_comp += entity.salary * entity.bonus_performance_max
    
    if entity.bonus_milestones_max and entity.bonus_milestones_max > 0:
        annual_comp += entity.salary * entity.bonus_milestones_max
    
    # Add equity value (annual vesting) with null checks
    if (entity.equity_eligible and entity.equity_shares and equity_value_per_share and 
        entity.equity_vest_years and entity.equity_vest_years > 0):
        annual_equity_vest = entity.equity_shares / entity.equity_vest_years
        annual_comp += annual_equity_vest * equity_value_per_share
    
    return annual_comp


def register_builtin_calculators(registry: CalculatorRegistry) -> None:
    """Register all built-in calculators with the given registry."""
    # Calculators are automatically registered when this module is imported
    # This function exists for explicit registration if needed
    pass


def load_all_calculators() -> None:
    """Load all built-in calculators into the registry."""
    # Calculators are automatically registered when this module is imported
    pass


# Aliases for backwards compatibility with test files
salary_calculator = calculate_employee_salary
equity_calculator = calculate_employee_equity
overhead_calculator = calculate_employee_overhead
milestone_calculator = calculate_grant_milestone_payment
disbursement_calculator = calculate_investment_disbursement
recurring_calculator = calculate_facility_recurring
depreciation_calculator = calculate_equipment_depreciation
maintenance_calculator = calculate_equipment_maintenance