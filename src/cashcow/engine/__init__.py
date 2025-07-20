"""Engine package for CashCow."""

from .builtin_calculators import load_all_calculators
from .calculators import (
    CalculationContext,
    Calculator,
    CalculatorMixin,
    CalculatorRegistry,
    get_calculator_registry,
    register_calculator,
)
from .cashflow import CashFlowEngine
from .kpis import KPICalculator
from .scenarios import Scenario, ScenarioManager, create_scenario_summary

# Load all built-in calculators when package is imported
load_all_calculators()

__all__ = [
    'Calculator',
    'CalculatorRegistry',
    'CalculationContext',
    'CalculatorMixin',
    'get_calculator_registry',
    'register_calculator',
    'load_all_calculators',
    'CashFlowEngine',
    'KPICalculator',
    'Scenario',
    'ScenarioManager',
    'create_scenario_summary',
]
