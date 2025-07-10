import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from cashcow.models.entities import Employee, Grant, Investment, Facility, Software, Equipment, Project
from cashcow.engine.calculators import CalculatorRegistry
from cashcow.engine.builtin_calculators import (
    salary_calculator, equity_calculator, overhead_calculator,
    milestone_calculator, disbursement_calculator, recurring_calculator,
    depreciation_calculator, maintenance_calculator
)


class TestCalculatorRegistry:
    def test_registry_creation(self):
        registry = CalculatorRegistry()
        assert registry._calculators == {}
    
    def test_register_calculator(self):
        registry = CalculatorRegistry()
        
        @registry.register('employee', 'test_calc')
        def test_calculator(entity, context):
            return 100.0
        
        assert 'employee' in registry._calculators
        assert 'test_calc' in registry._calculators['employee']
        assert registry._calculators['employee']['test_calc'] == test_calculator
    
    def test_get_calculator(self):
        registry = CalculatorRegistry()
        
        @registry.register('employee', 'test_calc')
        def test_calculator(entity, context):
            return 100.0
        
        calc = registry.get_calculator('employee', 'test_calc')
        assert calc == test_calculator
    
    def test_get_nonexistent_calculator(self):
        registry = CalculatorRegistry()
        calc = registry.get_calculator('employee', 'nonexistent')
        assert calc is None
    
    def test_get_calculators_for_entity(self):
        registry = CalculatorRegistry()
        
        @registry.register('employee', 'calc1')
        def calc1(entity, context):
            return 100.0
        
        @registry.register('employee', 'calc2')
        def calc2(entity, context):
            return 200.0
        
        calcs = registry.get_calculators('employee')
        assert len(calcs) == 2
        assert 'calc1' in calcs
        assert 'calc2' in calcs


class TestSalaryCalculator:
    def test_basic_salary_calculation(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly'
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = salary_calculator(employee, context)
        assert result == 5000.0  # 60000 / 12
    
    def test_hourly_salary_calculation(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=25 * 40 * 52,  # Annual salary equivalent
            pay_frequency='hourly',
            hours_per_week=40
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = salary_calculator(employee, context)
        # 25 * 40 * 52 / 12 = 4333.33
        assert abs(result - 4333.33) < 0.01
    
    def test_salary_with_bonus(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly',
            bonus_percentage=0.10
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = salary_calculator(employee, context)
        assert result == 5000.0  # Basic calculator doesn't handle bonuses
    
    def test_salary_with_allowances(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly',
            allowances={'transport': 500, 'food': 300}
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = salary_calculator(employee, context)
        assert result == 5000.0  # Basic calculator doesn't handle allowances
    
    def test_salary_outside_employment_period(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 2, 1),
            salary=60000,
            pay_frequency='monthly'
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = salary_calculator(employee, context)
        assert result == 0.0


class TestEquityCalculator:
    def test_equity_vesting_calculation(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            equity_eligible=True,
            equity_shares=10000,
            vesting_years=4,
            cliff_years=1
        )
        context = {
            'period_start': date(2025, 1, 1),
            'period_end': date(2025, 1, 31),
            'share_price': 10.0,
            'vesting_years': 4,
            'cliff_years': 1
        }
        
        result = equity_calculator(employee, context)
        # After 1 year (post-cliff), monthly vesting: 10000 / 4 / 12 * 10 = 2083.33
        assert abs(result - 2083.33) < 0.01
    
    def test_equity_before_cliff(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            equity_eligible=True,
            equity_shares=10000,
            vesting_years=4,
            cliff_years=1
        )
        context = {
            'period_start': date(2024, 6, 1),
            'period_end': date(2024, 6, 30),
            'share_price': 10.0,
            'vesting_years': 4,
            'cliff_years': 1
        }
        
        result = equity_calculator(employee, context)
        assert result == 0.0
    
    def test_equity_without_share_price(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            equity_eligible=True,
            equity_shares=10000,
            vesting_years=4,
            cliff_years=1
        )
        context = {'period_start': date(2025, 1, 1), 'period_end': date(2025, 1, 31)}
        
        result = equity_calculator(employee, context)
        assert result == 0.0


class TestOverheadCalculator:
    def test_overhead_calculation(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly',
            overhead_multiplier=1.3
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = overhead_calculator(employee, context)
        # Base salary: 5000, overhead: 5000 * 0.3 = 1500
        assert abs(result - 1500.0) < 0.01
    
    def test_overhead_with_benefits(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly',
            overhead_multiplier=1.3,
            benefits={'health': 400, 'retirement': 200}
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = overhead_calculator(employee, context)
        # Basic calculator doesn't handle benefits - just multiplier
        assert abs(result - 1500.0) < 0.01


class TestMilestoneCalculator:
    def test_milestone_payment(self):
        grant = Grant(
            type='grant',
            name='Test Grant',
            start_date=date(2024, 1, 1),
            amount=100000,
            payment_schedule=[
                {'date': '2024-06-01', 'amount': 50000},
                {'date': '2024-12-01', 'amount': 50000}
            ]
        )
        context = {'as_of_date': date(2024, 6, 1), 'period_start': date(2024, 6, 1), 'period_end': date(2024, 6, 30)}
        
        result = milestone_calculator(grant, context)
        assert result == 50000.0
    
    def test_no_milestone_in_period(self):
        grant = Grant(
            type='grant',
            name='Test Grant',
            start_date=date(2024, 1, 1),
            amount=100000,
            payment_schedule=[
                {'date': '2024-06-01', 'amount': 50000},
                {'date': '2024-12-01', 'amount': 50000}
            ]
        )
        context = {'period_start': date(2024, 7, 1), 'period_end': date(2024, 7, 31)}
        
        result = milestone_calculator(grant, context)
        assert result == 0.0


class TestDisbursementCalculator:
    def test_investment_disbursement(self):
        investment = Investment(
            type='investment',
            name='Test Investment',
            start_date=date(2024, 1, 1),
            amount=1000000,
            disbursement_schedule=[
                {'date': '2024-01-15', 'amount': 400000},
                {'date': '2024-06-15', 'amount': 600000}
            ]
        )
        context = {'as_of_date': date(2024, 1, 1), 'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = disbursement_calculator(investment, context)
        assert result == 400000.0
    
    def test_no_disbursement_in_period(self):
        investment = Investment(
            type='investment',
            name='Test Investment',
            start_date=date(2024, 1, 1),
            amount=1000000,
            disbursement_schedule=[
                {'date': '2024-01-15', 'amount': 400000},
                {'date': '2024-06-15', 'amount': 600000}
            ]
        )
        context = {'period_start': date(2024, 2, 1), 'period_end': date(2024, 2, 28)}
        
        result = disbursement_calculator(investment, context)
        assert result == 0.0


class TestRecurringCalculator:
    def test_monthly_recurring_cost(self):
        facility = Facility(
            type='facility',
            name='Test Facility',
            start_date=date(2024, 1, 1),
            monthly_cost=5000,
            payment_frequency='monthly'
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = recurring_calculator(facility, context)
        assert result == 5000.0
    
    def test_annual_recurring_cost(self):
        facility = Facility(
            type='facility',
            name='Test Facility',
            start_date=date(2024, 1, 1),
            monthly_cost=60000,
            payment_frequency='annual'
        )
        context = {'as_of_date': date(2024, 1, 1), 'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = recurring_calculator(facility, context)
        assert result == 60000.0  # Annual payment in January
    
    def test_recurring_cost_outside_period(self):
        facility = Facility(
            type='facility',
            name='Test Facility',
            start_date=date(2024, 2, 1),
            monthly_cost=5000,
            payment_frequency='monthly'
        )
        context = {'as_of_date': date(2024, 1, 1), 'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = recurring_calculator(facility, context)
        assert result == 0.0


class TestDepreciationCalculator:
    def test_equipment_depreciation(self):
        equipment = Equipment(
            type='equipment',
            name='Test Equipment',
            start_date=date(2024, 1, 1),
            cost=120000,
            purchase_date=date(2024, 1, 1),
            purchase_price=120000,
            useful_life_years=5,
            depreciation_method='straight-line'
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = depreciation_calculator(equipment, context)
        # 120000 / 5 / 12 = 2000 per month
        assert result == 2000.0
    
    def test_software_depreciation(self):
        software = Software(
            type='software',
            name='Test Software',
            start_date=date(2024, 1, 1),
            monthly_cost=333.33,
            purchase_price=12000,
            useful_life_years=3,
            depreciation_method='straight-line'
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        # Software depreciation is calculated through entity method
        result = software.calculate_monthly_depreciation(date(2024, 1, 1))
        # 12000 / 3 / 12 = 333.33 per month
        assert abs(result - 333.33) < 0.01
    
    def test_depreciation_after_useful_life(self):
        equipment = Equipment(
            type='equipment',
            name='Test Equipment',
            start_date=date(2019, 1, 1),
            cost=120000,
            purchase_date=date(2019, 1, 1),
            purchase_price=120000,
            useful_life_years=5,
            depreciation_method='straight-line'
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = depreciation_calculator(equipment, context)
        assert result == 0.0


class TestMaintenanceCalculator:
    def test_equipment_maintenance(self):
        equipment = Equipment(
            type='equipment',
            name='Test Equipment',
            start_date=date(2024, 1, 1),
            cost=120000,
            purchase_date=date(2024, 1, 1),
            purchase_price=120000,
            maintenance_percentage=0.05
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = maintenance_calculator(equipment, context)
        # 120000 * 0.05 / 12 = 500 per month
        assert result == 500.0
    
    def test_software_maintenance(self):
        software = Software(
            type='software',
            name='Test Software',
            start_date=date(2024, 1, 1),
            monthly_cost=200,
            purchase_price=12000,
            maintenance_percentage=0.20
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        # Software maintenance is calculated through entity method
        result = software.calculate_monthly_maintenance(date(2024, 1, 1))
        # 12000 * 0.20 / 12 = 200 per month
        assert result == 200.0
    
    def test_maintenance_with_fixed_cost(self):
        equipment = Equipment(
            type='equipment',
            name='Test Equipment',
            start_date=date(2024, 1, 1),
            cost=120000,
            purchase_date=date(2024, 1, 1),
            purchase_price=120000,
            maintenance_cost=1000
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        result = maintenance_calculator(equipment, context)
        assert result == 1000.0


class TestCalculatorIntegration:
    def test_multiple_calculators_for_employee(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly',
            overhead_multiplier=1.3,
            equity_eligible=True,
            equity_shares=10000,
            vesting_years=4,
            cliff_years=1
        )
        context = {
            'period_start': date(2025, 1, 1),
            'period_end': date(2025, 1, 31),
            'share_price': 10.0,
            'vesting_years': 4,
            'cliff_years': 1
        }
        
        salary_cost = salary_calculator(employee, context)
        overhead_cost = overhead_calculator(employee, context)
        equity_cost = equity_calculator(employee, context)
        
        total_cost = salary_cost + overhead_cost + equity_cost
        
        assert salary_cost == 5000.0
        assert abs(overhead_cost - 1500.0) < 0.01
        assert abs(equity_cost - 2083.33) < 0.01
        assert abs(total_cost - 8583.33) < 0.01
    
    def test_calculator_with_missing_context(self):
        employee = Employee(
            type='employee',
            name='Test Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly'
        )
        context = {}  # Missing period dates
        
        # Calculator uses today() as default, so no KeyError
        result = salary_calculator(employee, context)
        assert isinstance(result, float)
    
    def test_calculator_with_invalid_entity(self):
        # Test with wrong entity type
        facility = Facility(
            type='facility',
            name='Test Facility',
            start_date=date(2024, 1, 1),
            monthly_cost=5000
        )
        context = {'period_start': date(2024, 1, 1), 'period_end': date(2024, 1, 31)}
        
        # Should handle gracefully or return 0
        result = salary_calculator(facility, context)
        assert result == 0.0 or result is None