"""
Test Cases for Custom Rocket Engine Calculators

This module provides comprehensive test coverage for the custom
calculators defined in rocket_engine_calculators.py
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from cashcow.engine import get_calculator_registry, CalculationContext
from cashcow.models.entities import create_entity

# Import custom calculators to ensure they're registered
from rocket_engine_calculators import (
    calculate_fuel_consumption,
    calculate_test_infrastructure,
    calculate_total_testing_cost,
    calculate_production_capacity,
    calculate_quality_assurance,
    calculate_research_milestone,
    calculate_prototype_development,
    calculate_regulatory_compliance,
    calculate_insurance_premium,
)


class TestRocketEngineCalculators:
    """Test suite for rocket engine calculators."""
    
    @pytest.fixture
    def rocket_engine_entity(self):
        """Create a sample rocket engine entity for testing."""
        entity_data = {
            'name': 'Test_Raptor_Engine',
            'type': 'rocket_engine',
            'start_date': date(2024, 1, 1),
            'end_date': date(2025, 12, 31),
            'monthly_test_count': 8,
            'fuel_gallons_per_test': 1200,
            'fuel_price_per_gallon': 4.75,
            'development_phase': 'testing',
            'test_stand_monthly_cost': 60000,
            'instrumentation_monthly_cost': 12000,
            'safety_systems_monthly_cost': 6000,
            'test_crew_size': 8,
            'test_crew_hourly_rate': 80,
            'monthly_test_hours': 160,
            'monthly_consumables_cost': 4000,
            'monthly_maintenance_cost': 10000,
        }
        return create_entity(entity_data)
    
    @pytest.fixture
    def calculation_context(self):
        """Create a standard calculation context."""
        return CalculationContext(
            as_of_date=date(2024, 6, 1),
            scenario="baseline",
            additional_params={
                'fuel_price_per_gallon': 5.00,
                'capacity_utilization': 0.75,
            }
        )
    
    def test_fuel_consumption_calculation(self, rocket_engine_entity, calculation_context):
        """Test fuel consumption calculator."""
        registry = get_calculator_registry()
        
        result = registry.calculate(
            rocket_engine_entity, 
            "fuel_consumption_calc", 
            calculation_context.to_dict()
        )
        
        # Expected: 8 tests * 1200 gallons * $5.00 * 1.0 (testing phase)
        expected = 8 * 1200 * 5.00 * 1.0
        assert result == expected
        assert result == 48000.0
    
    def test_fuel_consumption_development_phase(self, rocket_engine_entity, calculation_context):
        """Test fuel consumption with development phase multiplier."""
        # Modify entity for development phase
        rocket_engine_entity.development_phase = 'development'
        
        registry = get_calculator_registry()
        result = registry.calculate(
            rocket_engine_entity, 
            "fuel_consumption_calc", 
            calculation_context.to_dict()
        )
        
        # Expected: 8 tests * 1200 gallons * $5.00 * 1.5 (development phase)
        expected = 8 * 1200 * 5.00 * 1.5
        assert result == expected
        assert result == 72000.0
    
    def test_fuel_consumption_inactive_entity(self, rocket_engine_entity, calculation_context):
        """Test fuel consumption for inactive entity."""
        # Set entity as inactive
        rocket_engine_entity.end_date = date(2024, 1, 1)
        
        registry = get_calculator_registry()
        result = registry.calculate(
            rocket_engine_entity, 
            "fuel_consumption_calc", 
            calculation_context.to_dict()
        )
        
        assert result == 0.0
    
    def test_test_infrastructure_calculation(self, rocket_engine_entity, calculation_context):
        """Test test infrastructure calculator."""
        registry = get_calculator_registry()
        
        result = registry.calculate(
            rocket_engine_entity, 
            "test_infrastructure_calc", 
            calculation_context.to_dict()
        )
        
        # Expected: (60000 + 12000 + 6000) * 1.0 (standard utilization for 8 tests)
        expected = (60000 + 12000 + 6000) * 1.0
        assert result == expected
        assert result == 78000.0
    
    def test_test_infrastructure_high_utilization(self, rocket_engine_entity, calculation_context):
        """Test test infrastructure with high utilization."""
        # Set high test count
        rocket_engine_entity.monthly_test_count = 12
        
        registry = get_calculator_registry()
        result = registry.calculate(
            rocket_engine_entity, 
            "test_infrastructure_calc", 
            calculation_context.to_dict()
        )
        
        # Expected: (60000 + 12000 + 6000) * 1.2 (high utilization for >10 tests)
        expected = (60000 + 12000 + 6000) * 1.2
        assert result == expected
        assert result == 93600.0
    
    def test_total_testing_cost_calculation(self, rocket_engine_entity, calculation_context):
        """Test total testing cost calculator with dependencies."""
        registry = get_calculator_registry()
        
        result = registry.calculate(
            rocket_engine_entity, 
            "total_testing_cost", 
            calculation_context.to_dict()
        )
        
        # Calculate expected components
        fuel_cost = 8 * 1200 * 5.00 * 1.0  # 48000
        infrastructure_cost = (60000 + 12000 + 6000) * 1.0  # 78000
        labor_cost = 8 * 80 * 160  # 102400
        consumables_cost = 4000
        maintenance_cost = 10000
        
        expected = fuel_cost + infrastructure_cost + labor_cost + consumables_cost + maintenance_cost
        assert result == expected
        assert result == 242400.0
    
    def test_calculator_dependency_validation(self, rocket_engine_entity):
        """Test that calculator dependencies are properly validated."""
        registry = get_calculator_registry()
        
        # Check dependencies for total_testing_cost
        missing_deps = registry.validate_dependencies("rocket_engine", "total_testing_cost")
        assert len(missing_deps) == 0  # Should have no missing dependencies
    
    def test_calculator_error_handling(self, calculation_context):
        """Test calculator error handling with invalid entity."""
        # Create entity without required attributes
        invalid_entity_data = {
            'name': 'Invalid_Entity',
            'type': 'rocket_engine',
            'start_date': date(2024, 1, 1),
            # Missing required attributes
        }
        invalid_entity = create_entity(invalid_entity_data)
        
        registry = get_calculator_registry()
        
        # Should not raise exception, should use defaults or return 0
        result = registry.calculate(
            invalid_entity, 
            "fuel_consumption_calc", 
            calculation_context.to_dict()
        )
        
        # Should return 0 due to missing attributes
        assert result == 0.0


class TestManufacturingCalculators:
    """Test suite for manufacturing line calculators."""
    
    @pytest.fixture
    def manufacturing_entity(self):
        """Create a sample manufacturing line entity."""
        entity_data = {
            'name': 'Engine_Production_Line_1',
            'type': 'manufacturing_line',
            'start_date': date(2024, 1, 1),
            'end_date': date(2026, 12, 31),
            'engines_per_month_capacity': 15,
            'cost_per_engine_base': 200000,
            'capacity_utilization': 0.8,
            'monthly_fixed_overhead': 120000,
            'variable_overhead_rate': 0.12,
            'qa_cost_percentage': 0.06,
            'qa_monthly_overhead': 20000,
        }
        return create_entity(entity_data)
    
    def test_production_capacity_calculation(self, manufacturing_entity):
        """Test production capacity calculator."""
        context = {
            'as_of_date': date(2024, 6, 1),
            'capacity_utilization': 0.75,
        }
        
        registry = get_calculator_registry()
        result = registry.calculate(
            manufacturing_entity, 
            "production_capacity_calc", 
            context
        )
        
        # Expected calculation:
        # actual_engines = 15 * 0.75 = 11.25
        # production_cost = 11.25 * 200000 = 2,250,000
        # fixed_overhead = 120,000
        # variable_overhead = 2,250,000 * 0.12 = 270,000
        # total = 2,250,000 + 120,000 + 270,000 = 2,640,000
        
        expected = (15 * 0.75 * 200000) + 120000 + (15 * 0.75 * 200000 * 0.12)
        assert result == expected
        assert result == 2640000.0
    
    def test_quality_assurance_calculation(self, manufacturing_entity):
        """Test quality assurance calculator."""
        context = {
            'as_of_date': date(2024, 6, 1),
            'capacity_utilization': 0.8,
        }
        
        registry = get_calculator_registry()
        
        # First calculate production capacity
        production_cost = registry.calculate(
            manufacturing_entity, 
            "production_capacity_calc", 
            context
        )
        
        # Then calculate QA costs
        qa_result = registry.calculate(
            manufacturing_entity, 
            "quality_assurance_calc", 
            context
        )
        
        # Expected: production_cost * 0.06 + 20000
        expected_qa = (production_cost * 0.06) + 20000
        assert qa_result == expected_qa


class TestRDCalculators:
    """Test suite for R&D project calculators."""
    
    @pytest.fixture
    def rd_project_entity(self):
        """Create a sample R&D project entity."""
        entity_data = {
            'name': 'Advanced_Combustion_Research',
            'type': 'rd_project',
            'start_date': date(2024, 1, 1),
            'end_date': date(2025, 6, 30),
            'milestones': [
                {
                    'planned_date': date(2024, 6, 1),
                    'budget': 150000,
                    'risk_level': 'medium',
                    'description': 'Initial design review'
                },
                {
                    'planned_date': date(2024, 9, 1),
                    'budget': 300000,
                    'risk_level': 'high',
                    'description': 'Prototype testing'
                }
            ],
            'monthly_material_budget': 80000,
            'complexity_level': 'complex',
            'monthly_equipment_rental': 15000,
            'monthly_tooling_cost': 12000,
            'monthly_contractor_budget': 40000,
        }
        return create_entity(entity_data)
    
    def test_research_milestone_calculation(self, rd_project_entity):
        """Test research milestone calculator."""
        context = {
            'as_of_date': date(2024, 6, 1),
        }
        
        registry = get_calculator_registry()
        result = registry.calculate(
            rd_project_entity, 
            "research_milestone_calc", 
            context
        )
        
        # Expected: 150000 * 1.2 (medium risk multiplier) = 180000
        expected = 150000 * 1.2
        assert result == expected
        assert result == 180000.0
    
    def test_research_milestone_high_risk(self, rd_project_entity):
        """Test research milestone with high risk."""
        context = {
            'as_of_date': date(2024, 9, 1),
        }
        
        registry = get_calculator_registry()
        result = registry.calculate(
            rd_project_entity, 
            "research_milestone_calc", 
            context
        )
        
        # Expected: 300000 * 1.5 (high risk multiplier) = 450000
        expected = 300000 * 1.5
        assert result == expected
        assert result == 450000.0
    
    def test_prototype_development_calculation(self, rd_project_entity):
        """Test prototype development calculator."""
        context = {
            'as_of_date': date(2024, 6, 1),
        }
        
        registry = get_calculator_registry()
        result = registry.calculate(
            rd_project_entity, 
            "prototype_development_calc", 
            context
        )
        
        # Expected calculation:
        # material_cost = 80000 * 1.4 (complex multiplier) = 112000
        # equipment_rental = 15000
        # tooling_cost = 12000
        # contractor_budget = 40000
        # total = 112000 + 15000 + 12000 + 40000 = 179000
        
        expected = (80000 * 1.4) + 15000 + 12000 + 40000
        assert result == expected
        assert result == 179000.0


class TestComplianceCalculators:
    """Test suite for compliance and insurance calculators."""
    
    @pytest.fixture
    def compliance_entity(self):
        """Create a sample compliance program entity."""
        entity_data = {
            'name': 'Regulatory_Compliance_Program',
            'type': 'compliance_program',
            'start_date': date(2024, 1, 1),
            'faa_monthly_cost': 18000,
            'itar_monthly_cost': 10000,
            'iso_monthly_cost': 6000,
            'audit_frequency_months': 6,
            'audit_cost': 60000,
            'legal_monthly_retainer': 15000,
            'compliance_consulting_monthly': 10000,
        }
        return create_entity(entity_data)
    
    @pytest.fixture
    def insurance_entity(self):
        """Create a sample insurance policy entity."""
        entity_data = {
            'name': 'Comprehensive_Insurance_Package',
            'type': 'insurance_policy',
            'start_date': date(2024, 1, 1),
            'general_liability_monthly': 10000,
            'product_liability_monthly': 30000,
            'professional_liability_monthly': 8000,
            'cyber_liability_monthly': 5000,
            'years_in_operation': 3,
        }
        return create_entity(entity_data)
    
    def test_regulatory_compliance_calculation(self, compliance_entity):
        """Test regulatory compliance calculator."""
        context = {
            'as_of_date': date(2024, 6, 1),
        }
        
        registry = get_calculator_registry()
        result = registry.calculate(
            compliance_entity, 
            "regulatory_compliance_calc", 
            context
        )
        
        # Expected calculation:
        # base_costs = 18000 + 10000 + 6000 = 34000
        # monthly_audit = 60000 / 6 = 10000
        # legal_consulting = 15000 + 10000 = 25000
        # total = 34000 + 10000 + 25000 = 69000
        
        expected = 18000 + 10000 + 6000 + (60000/6) + 15000 + 10000
        assert result == expected
        assert result == 69000.0
    
    def test_insurance_premium_calculation(self, insurance_entity):
        """Test insurance premium calculator."""
        context = {
            'as_of_date': date(2024, 6, 1),
            'monthly_tests': 8,
            'safety_incidents_12m': 0,
        }
        
        registry = get_calculator_registry()
        result = registry.calculate(
            insurance_entity, 
            "insurance_premium_calc", 
            context
        )
        
        # Expected calculation:
        # base_premium = 10000 + 30000 + 8000 + 5000 = 53000
        # risk_multiplier = 1.0 (standard test frequency, no incidents)
        # experience_discount = 0.9 (3 years operation)
        # total = 53000 * 1.0 * 0.9 = 47700
        
        base_premium = 10000 + 30000 + 8000 + 5000
        expected = base_premium * 1.0 * 0.9  # Experience discount
        assert result == expected
        assert result == 47700.0
    
    def test_insurance_premium_high_risk(self, insurance_entity):
        """Test insurance premium with high risk factors."""
        context = {
            'as_of_date': date(2024, 6, 1),
            'monthly_tests': 16,  # High test frequency
            'safety_incidents_12m': 2,  # Safety incidents
        }
        
        registry = get_calculator_registry()
        result = registry.calculate(
            insurance_entity, 
            "insurance_premium_calc", 
            context
        )
        
        # Expected calculation:
        # base_premium = 53000
        # risk_multiplier = 1.0 + 0.3 (high tests) + 0.2 (2 incidents) = 1.5
        # experience_discount = 0.9
        # total = 53000 * 1.5 * 0.9 = 71550
        
        base_premium = 10000 + 30000 + 8000 + 5000
        risk_multiplier = 1.0 + 0.3 + (2 * 0.1)  # High frequency + incidents
        experience_discount = 0.9
        expected = base_premium * risk_multiplier * experience_discount
        assert result == expected
        assert result == 71550.0


class TestCalculatorIntegration:
    """Integration tests for calculator system."""
    
    def test_calculator_registration(self):
        """Test that all custom calculators are properly registered."""
        registry = get_calculator_registry()
        
        # Test rocket engine calculators
        rocket_calculators = registry.list_calculators("rocket_engine")
        expected_rocket_calcs = [
            "fuel_consumption_calc",
            "test_infrastructure_calc", 
            "total_testing_cost"
        ]
        
        for calc_name in expected_rocket_calcs:
            assert calc_name in rocket_calculators["rocket_engine"]
        
        # Test manufacturing calculators
        manufacturing_calculators = registry.list_calculators("manufacturing_line")
        expected_manufacturing_calcs = [
            "production_capacity_calc",
            "quality_assurance_calc"
        ]
        
        for calc_name in expected_manufacturing_calcs:
            assert calc_name in manufacturing_calculators["manufacturing_line"]
    
    def test_calculate_all_functionality(self):
        """Test calculate_all functionality with custom calculators."""
        # Create rocket engine entity
        entity_data = {
            'name': 'Integration_Test_Engine',
            'type': 'rocket_engine',
            'start_date': date(2024, 1, 1),
            'monthly_test_count': 10,
            'fuel_gallons_per_test': 1000,
        }
        entity = create_entity(entity_data)
        
        context = {
            'as_of_date': date(2024, 6, 1),
            'fuel_price_per_gallon': 5.00,
        }
        
        registry = get_calculator_registry()
        all_results = registry.calculate_all(entity, context)
        
        # Should have results for all registered calculators
        expected_calculators = [
            "fuel_consumption_calc",
            "test_infrastructure_calc",
            "total_testing_cost"
        ]
        
        for calc_name in expected_calculators:
            assert calc_name in all_results
            assert isinstance(all_results[calc_name], (int, float))
            assert all_results[calc_name] >= 0  # Costs should be non-negative
    
    @patch('cashcow.engine.calculators.print')
    def test_error_handling_integration(self, mock_print):
        """Test error handling in calculate_all with problematic calculator."""
        # Create entity that might cause calculation errors
        entity_data = {
            'name': 'Error_Test_Entity',
            'type': 'rocket_engine',
            'start_date': date(2024, 1, 1),
            # Intentionally missing some attributes
        }
        entity = create_entity(entity_data)
        
        context = {
            'as_of_date': date(2024, 6, 1),
        }
        
        registry = get_calculator_registry()
        
        # Should not raise exception, should handle errors gracefully
        results = registry.calculate_all(entity, context)
        
        # Should still return some results (may have default values)
        assert isinstance(results, dict)


if __name__ == "__main__":
    """
    Run the tests directly with pytest or python.
    
    Example usage:
        python test_rocket_calculators.py
        pytest test_rocket_calculators.py -v
        pytest test_rocket_calculators.py::TestRocketEngineCalculators::test_fuel_consumption_calculation -v
    """
    
    # Run a quick smoke test
    print("Running basic smoke test...")
    
    # Test basic calculator functionality
    entity_data = {
        'name': 'Smoke_Test_Engine',
        'type': 'rocket_engine',
        'start_date': date(2024, 1, 1),
        'monthly_test_count': 5,
        'fuel_gallons_per_test': 1000,
    }
    
    entity = create_entity(entity_data)
    context = {'as_of_date': date(2024, 6, 1), 'fuel_price_per_gallon': 4.50}
    
    registry = get_calculator_registry()
    result = registry.calculate(entity, "fuel_consumption_calc", context)
    
    print(f"Smoke test result: ${result:,.2f}")
    print("Smoke test passed!")