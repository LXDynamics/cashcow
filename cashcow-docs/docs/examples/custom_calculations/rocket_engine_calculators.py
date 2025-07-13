"""
Custom Calculator Examples for Rocket Engine Financial Modeling

This module demonstrates how to create domain-specific calculators
for rocket engine companies using the CashCow calculation engine.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import math

from cashcow.engine import register_calculator, get_calculator_registry
from cashcow.models.base import BaseEntity


# =============================================================================
# Rocket Engine Test Calculators
# =============================================================================

@register_calculator(
    entity_type="rocket_engine",
    name="fuel_consumption_calc",
    description="Calculate monthly fuel consumption costs for testing",
    dependencies=[]
)
def calculate_fuel_consumption(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly fuel consumption costs for rocket engine testing.
    
    Args:
        entity: Rocket engine entity with test schedule
        context: Calculation context with fuel pricing
        
    Returns:
        Monthly fuel cost in dollars
    """
    as_of_date = context.get('as_of_date', date.today())
    
    # Check if entity is active
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Get fuel pricing from context or entity
    fuel_price_per_gallon = context.get('fuel_price_per_gallon', 
                                       getattr(entity, 'fuel_price_per_gallon', 4.50))
    
    # Get test schedule parameters
    monthly_tests = getattr(entity, 'monthly_test_count', 0)
    fuel_per_test = getattr(entity, 'fuel_gallons_per_test', 1000)
    
    # Calculate base fuel cost
    base_fuel_cost = monthly_tests * fuel_per_test * fuel_price_per_gallon
    
    # Apply test intensity multiplier for development phase
    test_phase = getattr(entity, 'development_phase', 'testing')
    intensity_multipliers = {
        'development': 1.5,  # More intensive testing
        'testing': 1.0,      # Standard testing
        'production': 0.3,   # Minimal testing
        'maintenance': 0.1   # Just maintenance runs
    }
    
    multiplier = intensity_multipliers.get(test_phase, 1.0)
    adjusted_fuel_cost = base_fuel_cost * multiplier
    
    return adjusted_fuel_cost


@register_calculator(
    entity_type="rocket_engine",
    name="test_infrastructure_calc",
    description="Calculate monthly test infrastructure and facility costs",
    dependencies=[]
)
def calculate_test_infrastructure(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly test infrastructure costs.
    
    Includes test stand rental, instrumentation, safety systems, etc.
    """
    as_of_date = context.get('as_of_date', date.today())
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Base infrastructure costs
    test_stand_rental = getattr(entity, 'test_stand_monthly_cost', 50000)
    instrumentation_cost = getattr(entity, 'instrumentation_monthly_cost', 15000)
    safety_systems_cost = getattr(entity, 'safety_systems_monthly_cost', 8000)
    
    # Test frequency modifier
    monthly_tests = getattr(entity, 'monthly_test_count', 0)
    if monthly_tests > 10:
        utilization_multiplier = 1.2  # High utilization premium
    elif monthly_tests > 5:
        utilization_multiplier = 1.0  # Standard utilization
    else:
        utilization_multiplier = 0.8  # Low utilization discount
    
    total_infrastructure = (test_stand_rental + instrumentation_cost + 
                           safety_systems_cost) * utilization_multiplier
    
    return total_infrastructure


@register_calculator(
    entity_type="rocket_engine",
    name="total_testing_cost",
    description="Calculate total monthly testing costs including all components",
    dependencies=["fuel_consumption_calc", "test_infrastructure_calc"]
)
def calculate_total_testing_cost(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate total monthly testing costs."""
    registry = get_calculator_registry()
    
    # Get component costs
    fuel_cost = registry.calculate(entity, "fuel_consumption_calc", context) or 0.0
    infrastructure_cost = registry.calculate(entity, "test_infrastructure_calc", context) or 0.0
    
    # Add labor costs for test operations
    test_crew_size = getattr(entity, 'test_crew_size', 8)
    avg_hourly_rate = getattr(entity, 'test_crew_hourly_rate', 75)
    monthly_test_hours = getattr(entity, 'monthly_test_hours', 160)
    
    labor_cost = test_crew_size * avg_hourly_rate * monthly_test_hours
    
    # Add consumables and maintenance
    consumables_cost = getattr(entity, 'monthly_consumables_cost', 5000)
    maintenance_cost = getattr(entity, 'monthly_maintenance_cost', 12000)
    
    total_cost = (fuel_cost + infrastructure_cost + labor_cost + 
                  consumables_cost + maintenance_cost)
    
    return total_cost


# =============================================================================
# Manufacturing and Production Calculators
# =============================================================================

@register_calculator(
    entity_type="manufacturing_line",
    name="production_capacity_calc",
    description="Calculate monthly production capacity and associated costs",
    dependencies=[]
)
def calculate_production_capacity(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly production capacity costs."""
    as_of_date = context.get('as_of_date', date.today())
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Production parameters
    engines_per_month = getattr(entity, 'engines_per_month_capacity', 10)
    cost_per_engine = getattr(entity, 'cost_per_engine_base', 250000)
    
    # Capacity utilization from context or entity
    capacity_utilization = context.get('capacity_utilization', 
                                      getattr(entity, 'capacity_utilization', 0.75))
    
    # Calculate actual production costs
    actual_engines = engines_per_month * capacity_utilization
    production_cost = actual_engines * cost_per_engine
    
    # Add fixed manufacturing overhead
    fixed_overhead = getattr(entity, 'monthly_fixed_overhead', 150000)
    
    # Variable overhead based on utilization
    variable_overhead_rate = getattr(entity, 'variable_overhead_rate', 0.15)
    variable_overhead = production_cost * variable_overhead_rate
    
    total_manufacturing_cost = production_cost + fixed_overhead + variable_overhead
    
    return total_manufacturing_cost


@register_calculator(
    entity_type="manufacturing_line",
    name="quality_assurance_calc",
    description="Calculate monthly quality assurance and testing costs",
    dependencies=["production_capacity_calc"]
)
def calculate_quality_assurance(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly QA costs based on production volume."""
    registry = get_calculator_registry()
    
    # Get production volume (derived from production capacity)
    production_cost = registry.calculate(entity, "production_capacity_calc", context) or 0.0
    
    # QA costs as percentage of production
    qa_percentage = getattr(entity, 'qa_cost_percentage', 0.08)  # 8% of production cost
    
    # Additional QA overhead
    qa_overhead = getattr(entity, 'qa_monthly_overhead', 25000)
    
    total_qa_cost = (production_cost * qa_percentage) + qa_overhead
    
    return total_qa_cost


# =============================================================================
# Research and Development Calculators
# =============================================================================

@register_calculator(
    entity_type="rd_project",
    name="research_milestone_calc",
    description="Calculate milestone-based R&D costs with risk adjustments",
    dependencies=[]
)
def calculate_research_milestone(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate R&D milestone costs with technical risk adjustments."""
    as_of_date = context.get('as_of_date', date.today())
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Check for milestones in current month
    milestones = getattr(entity, 'milestones', [])
    current_month = as_of_date.replace(day=1)
    
    monthly_milestone_cost = 0.0
    
    for milestone in milestones:
        milestone_date = milestone.get('planned_date')
        if isinstance(milestone_date, str):
            milestone_date = date.fromisoformat(milestone_date)
        
        milestone_month = milestone_date.replace(day=1)
        
        if milestone_month == current_month:
            base_cost = milestone.get('budget', 0)
            
            # Apply technical risk multiplier
            risk_level = milestone.get('risk_level', 'medium')
            risk_multipliers = {
                'low': 1.0,
                'medium': 1.2,
                'high': 1.5,
                'extreme': 2.0
            }
            
            risk_multiplier = risk_multipliers.get(risk_level, 1.2)
            adjusted_cost = base_cost * risk_multiplier
            
            monthly_milestone_cost += adjusted_cost
    
    return monthly_milestone_cost


@register_calculator(
    entity_type="rd_project",
    name="prototype_development_calc",
    description="Calculate monthly prototype development costs",
    dependencies=[]
)
def calculate_prototype_development(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly prototype development costs."""
    as_of_date = context.get('as_of_date', date.today())
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Material costs for prototypes
    monthly_material_budget = getattr(entity, 'monthly_material_budget', 100000)
    
    # Prototype complexity modifier
    complexity_level = getattr(entity, 'complexity_level', 'medium')
    complexity_multipliers = {
        'simple': 0.7,
        'medium': 1.0,
        'complex': 1.4,
        'cutting_edge': 2.0
    }
    
    complexity_multiplier = complexity_multipliers.get(complexity_level, 1.0)
    
    # Specialized equipment and tooling
    equipment_rental = getattr(entity, 'monthly_equipment_rental', 20000)
    tooling_amortization = getattr(entity, 'monthly_tooling_cost', 15000)
    
    # External contractor costs
    contractor_budget = getattr(entity, 'monthly_contractor_budget', 50000)
    
    total_prototype_cost = ((monthly_material_budget * complexity_multiplier) + 
                           equipment_rental + tooling_amortization + contractor_budget)
    
    return total_prototype_cost


# =============================================================================
# Regulatory and Compliance Calculators
# =============================================================================

@register_calculator(
    entity_type="compliance_program",
    name="regulatory_compliance_calc",
    description="Calculate monthly regulatory compliance costs",
    dependencies=[]
)
def calculate_regulatory_compliance(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly regulatory compliance costs."""
    as_of_date = context.get('as_of_date', date.today())
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Base compliance costs
    faa_compliance = getattr(entity, 'faa_monthly_cost', 15000)
    itar_compliance = getattr(entity, 'itar_monthly_cost', 8000)
    iso_compliance = getattr(entity, 'iso_monthly_cost', 5000)
    
    # Audit and inspection costs (periodic)
    audit_frequency_months = getattr(entity, 'audit_frequency_months', 6)
    audit_cost = getattr(entity, 'audit_cost', 50000)
    
    # Calculate monthly audit cost amortization
    monthly_audit_cost = audit_cost / audit_frequency_months
    
    # Legal and consulting fees
    legal_retainer = getattr(entity, 'legal_monthly_retainer', 12000)
    compliance_consulting = getattr(entity, 'compliance_consulting_monthly', 8000)
    
    total_compliance_cost = (faa_compliance + itar_compliance + iso_compliance + 
                            monthly_audit_cost + legal_retainer + compliance_consulting)
    
    return total_compliance_cost


# =============================================================================
# Insurance and Risk Management Calculators
# =============================================================================

@register_calculator(
    entity_type="insurance_policy",
    name="insurance_premium_calc",
    description="Calculate monthly insurance premiums with risk adjustments",
    dependencies=[]
)
def calculate_insurance_premium(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """Calculate monthly insurance premiums with risk-based adjustments."""
    as_of_date = context.get('as_of_date', date.today())
    
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Base premium costs
    general_liability = getattr(entity, 'general_liability_monthly', 8000)
    product_liability = getattr(entity, 'product_liability_monthly', 25000)
    professional_liability = getattr(entity, 'professional_liability_monthly', 6000)
    cyber_liability = getattr(entity, 'cyber_liability_monthly', 4000)
    
    # Risk factors that affect premiums
    test_frequency = context.get('monthly_tests', getattr(entity, 'monthly_test_count', 0))
    safety_incidents = context.get('safety_incidents_12m', 0)
    
    # Risk adjustment multiplier
    risk_multiplier = 1.0
    
    # High test frequency increases risk
    if test_frequency > 15:
        risk_multiplier += 0.3
    elif test_frequency > 10:
        risk_multiplier += 0.15
    
    # Safety incidents increase premiums
    if safety_incidents > 0:
        risk_multiplier += safety_incidents * 0.1
    
    # Industry experience modifier
    years_in_operation = getattr(entity, 'years_in_operation', 1)
    if years_in_operation > 5:
        risk_multiplier *= 0.9  # Experience discount
    elif years_in_operation < 2:
        risk_multiplier *= 1.2  # New company premium
    
    base_premium = general_liability + product_liability + professional_liability + cyber_liability
    adjusted_premium = base_premium * risk_multiplier
    
    return adjusted_premium


# =============================================================================
# Utility Functions for Calculator Development
# =============================================================================

def validate_entity_attributes(entity: BaseEntity, required_attrs: List[str]) -> bool:
    """Validate that entity has required attributes for calculation."""
    for attr in required_attrs:
        if not hasattr(entity, attr):
            return False
    return True


def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Perform safe division with default value for zero denominator."""
    return numerator / denominator if denominator != 0 else default


def interpolate_monthly_value(annual_value: float, start_date: date, 
                             calculation_date: date) -> float:
    """Interpolate monthly value from annual value based on timing."""
    months_since_start = ((calculation_date.year - start_date.year) * 12 + 
                         calculation_date.month - start_date.month)
    
    # Return proportional monthly value
    return annual_value / 12 if months_since_start >= 0 else 0.0


def apply_scenario_multipliers(base_value: float, context: Dict[str, Any], 
                              entity_type: str) -> float:
    """Apply scenario-specific multipliers to calculated values."""
    scenario = context.get('scenario', 'baseline')
    
    # Scenario multipliers by entity type
    multipliers = {
        'optimistic': {
            'rocket_engine': 1.2,
            'manufacturing_line': 1.3,
            'rd_project': 1.4,
        },
        'conservative': {
            'rocket_engine': 0.9,
            'manufacturing_line': 0.8,
            'rd_project': 0.7,
        },
        'baseline': {
            'rocket_engine': 1.0,
            'manufacturing_line': 1.0,
            'rd_project': 1.0,
        }
    }
    
    multiplier = multipliers.get(scenario, {}).get(entity_type, 1.0)
    return base_value * multiplier


# =============================================================================
# Example Usage and Testing
# =============================================================================

if __name__ == "__main__":
    """
    Example usage of custom calculators.
    
    This section demonstrates how to use the custom calculators
    in a real-world scenario.
    """
    
    from cashcow.models.entities import create_entity
    from cashcow.engine import get_calculator_registry, CalculationContext
    
    # Create a sample rocket engine entity
    engine_data = {
        'name': 'Raptor_Engine_Development',
        'type': 'rocket_engine',
        'start_date': date(2024, 1, 1),
        'end_date': date(2025, 12, 31),
        'monthly_test_count': 12,
        'fuel_gallons_per_test': 1500,
        'fuel_price_per_gallon': 5.25,
        'development_phase': 'testing',
        'test_stand_monthly_cost': 75000,
        'test_crew_size': 10,
        'test_crew_hourly_rate': 85,
        'monthly_test_hours': 200,
    }
    
    # Create entity
    engine = create_entity(engine_data)
    
    # Create calculation context
    context = CalculationContext(
        as_of_date=date(2024, 6, 1),
        scenario="baseline",
        additional_params={
            'capacity_utilization': 0.8,
            'safety_incidents_12m': 0,
            'monthly_tests': 12,
        }
    )
    
    # Get registry and calculate values
    registry = get_calculator_registry()
    
    # Calculate individual components
    fuel_cost = registry.calculate(engine, "fuel_consumption_calc", context.to_dict())
    infrastructure_cost = registry.calculate(engine, "test_infrastructure_calc", context.to_dict())
    total_cost = registry.calculate(engine, "total_testing_cost", context.to_dict())
    
    print(f"Rocket Engine Monthly Costs:")
    print(f"  Fuel Consumption: ${fuel_cost:,.2f}")
    print(f"  Test Infrastructure: ${infrastructure_cost:,.2f}")
    print(f"  Total Testing Cost: ${total_cost:,.2f}")
    
    # Calculate all available values
    all_calculations = registry.calculate_all(engine, context.to_dict())
    print(f"\nAll Calculations: {all_calculations}")