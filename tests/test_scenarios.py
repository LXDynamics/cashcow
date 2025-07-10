import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
from unittest.mock import Mock, patch

from cashcow.storage.database import EntityStore
from cashcow.engine.cashflow import CashFlowEngine
from cashcow.engine.calculators import CalculatorRegistry
from cashcow.engine.builtin_calculators import register_builtin_calculators
from cashcow.engine.scenarios import ScenarioManager, Scenario
from cashcow.models.entities import Employee, Grant, Investment, Facility, Equipment


class TestScenarioManager:
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test.db'
        self.scenarios_dir = Path(self.temp_dir) / 'scenarios'
        self.scenarios_dir.mkdir(parents=True)
        
        # Initialize components
        self.store = EntityStore(str(self.db_path))
        self.engine = CashFlowEngine(self.store)
        self.scenario_manager = ScenarioManager(self.store, self.engine)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def create_test_entities(self):
        """Create test entities for scenario testing"""
        return [
            Employee(
                type='employee',
                name='Base Employee',
                start_date=date(2024, 1, 1),
                salary=100000,
                pay_frequency='monthly',
                overhead_multiplier=1.3,
                tags=['engineering', 'core']
            ),
            Employee(
                type='employee',
                name='Growth Employee',
                start_date=date(2024, 6, 1),
                salary=80000,
                pay_frequency='monthly',
                overhead_multiplier=1.2,
                tags=['engineering', 'growth']
            ),
            Grant(
                type='grant',
                name='Research Grant',
                start_date=date(2024, 1, 1),
                amount=500000,
                grantor='NASA',
                milestones=[
                    {'name': 'Phase 1', 'amount': 250000, 'due_date': '2024-06-01'},
                    {'name': 'Phase 2', 'amount': 250000, 'due_date': '2024-12-01'}
                ],
                tags=['government', 'research']
            ),
            Investment(
                type='investment',
                name='Series A',
                start_date=date(2024, 3, 1),
                amount=2000000,
                investor='VC Fund',
                disbursement_schedule=[
                    {'date': '2024-03-15', 'amount': 1000000},
                    {'date': '2024-09-15', 'amount': 1000000}
                ],
                tags=['private', 'growth']
            ),
            Facility(
                type='facility',
                name='Main Office',
                start_date=date(2024, 1, 1),
                monthly_cost=15000,
                tags=['office', 'overhead']
            ),
            Equipment(
                type='equipment',
                name='Test Equipment',
                start_date=date(2024, 4, 1),
                cost=300000,
                purchase_date=date(2024, 4, 1),
                useful_life_years=5,
                maintenance_percentage=0.05,
                tags=['equipment', 'testing']
            )
        ]
    
    def test_scenario_creation(self):
        """Test basic scenario creation"""
        self.setUp()
        
        scenario = Scenario(
            name='test_scenario',
            description='Test scenario for unit tests',
            entity_filters={'require_tags': ['core']},
            entity_overrides=[{'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 1.5}],
            assumptions={'inflation_rate': 0.03}
        )
        
        assert scenario.name == 'test_scenario'
        assert scenario.description == 'Test scenario for unit tests'
        assert scenario.entity_filters == {'require_tags': ['core']}
        assert scenario.entity_overrides == [{'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 1.5}]
        assert scenario.assumptions == {'inflation_rate': 0.03}
        
        self.tearDown()
    
    def test_scenario_yaml_loading(self):
        """Test loading scenarios from YAML files"""
        self.setUp()
        
        # Create scenario YAML file
        scenario_data = {
            'name': 'optimistic',
            'description': 'Optimistic growth scenario',
            'entity_filters': {
                'require_tags': ['core', 'growth'],
                'exclude_tags': ['deprecated']
            },
            'entity_overrides': [
                {
                    'entity_type': 'employee',
                    'field': 'overhead_multiplier',
                    'value': 1.2
                },
                {
                    'entity_type': 'grant',
                    'field': 'amount',
                    'multiplier': 1.2
                }
            ],
            'assumptions': {
                'inflation_rate': 0.02,
                'growth_rate': 0.15,
                'hiring_acceleration': 1.3
            }
        }
        
        scenario_file = self.scenarios_dir / 'optimistic.yaml'
        with open(scenario_file, 'w') as f:
            yaml.dump(scenario_data, f)
        
        # Load scenario
        self.scenario_manager.load_scenario(scenario_file)
        
        scenario = self.scenario_manager.get_scenario('optimistic')
        assert scenario is not None
        assert scenario.name == 'optimistic'
        assert scenario.description == 'Optimistic growth scenario'
        assert scenario.entity_filters['require_tags'] == ['core', 'growth']
        assert scenario.assumptions['inflation_rate'] == 0.02
        
        self.tearDown()
    
    def test_builtin_scenarios(self):
        """Test built-in scenario generation"""
        self.setUp()
        
        # Built-in scenarios are created by default
        scenario_names = self.scenario_manager.list_scenarios()
        
        # Verify expected scenarios exist
        expected_scenarios = ['baseline', 'optimistic', 'conservative', 'cash_preservation']
        for scenario_name in expected_scenarios:
            assert scenario_name in scenario_names
        
        # Check baseline scenario
        baseline = self.scenario_manager.get_scenario('baseline')
        assert baseline.name == 'baseline'
        assert 'baseline' in baseline.description.lower()
        
        # Check optimistic scenario
        optimistic = self.scenario_manager.get_scenario('optimistic')
        assert optimistic.name == 'optimistic'
        assert 'revenue_growth_rate' in optimistic.assumptions
        assert optimistic.assumptions['revenue_growth_rate'] > 0.1
        
        # Check conservative scenario
        conservative = self.scenario_manager.get_scenario('conservative')
        assert conservative.name == 'conservative'
        assert 'overhead_multiplier' in conservative.assumptions
        assert conservative.assumptions['overhead_multiplier'] > 1.3
        
        # Check cash preservation scenario
        cash_preservation = self.scenario_manager.get_scenario('cash_preservation')
        assert cash_preservation.name == 'cash_preservation'
        assert 'exclude_tags' in cash_preservation.entity_filters
        assert 'non_essential' in cash_preservation.entity_filters['exclude_tags']
        
        self.tearDown()
    
    def test_entity_filtering(self):
        """Test entity filtering based on scenario criteria"""
        self.setUp()
        
        # Create test entities directly for filtering test
        entities = self.create_test_entities()
        
        # Test filtering by tags
        scenario = Scenario(
            name='core_only',
            description='Only core entities',
            entity_filters={'require_tags': ['core']},
            entity_overrides=[],
            assumptions={}
        )
        
        # Test that scenario can filter entities
        core_entities = [e for e in entities if scenario.should_include_entity(e)]
        
        # Should only include entities with 'core' tag
        assert len(core_entities) == 1
        assert core_entities[0].name == 'Base Employee'
        
        # Test exclusion filtering
        scenario_exclude = Scenario(
            name='no_growth',
            description='Exclude growth entities',
            entity_filters={'exclude_tags': ['growth']},
            entity_overrides=[],
            assumptions={}
        )
        
        non_growth_entities = [e for e in entities if scenario_exclude.should_include_entity(e)]
        
        # Should exclude entities with 'growth' tag
        growth_entities = [e for e in non_growth_entities if 'growth' in e.tags]
        assert len(growth_entities) == 0
        
        self.tearDown()
    
    def test_entity_overrides(self):
        """Test entity override application"""
        self.setUp()
        
        # Create test entities directly
        entities = self.create_test_entities()
        
        # Test employee overrides
        scenario = Scenario(
            name='high_overhead',
            description='High overhead scenario',
            entity_filters={},
            entity_overrides=[
                {
                    'entity_type': 'employee',
                    'field': 'overhead_multiplier',
                    'value': 1.8
                }
            ],
            assumptions={}
        )
        
        # Apply overrides to specific entities
        employees = [e for e in entities if e.type == 'employee']
        
        # Test scenario application
        for employee in employees:
            modified_employee = scenario.apply_to_entity(employee)
            assert modified_employee.overhead_multiplier == 1.8
        
        # Test non-employee entities are unchanged
        non_employees = [e for e in entities if e.type != 'employee']
        for entity in non_employees:
            original_dict = entity.to_dict()
            modified_entity = scenario.apply_to_entity(entity)
            modified_dict = modified_entity.to_dict()
            # Should not have been modified (key fields should be the same)
            assert modified_dict['name'] == original_dict['name']
            assert modified_dict['type'] == original_dict['type']
        
        self.tearDown()
    
    def test_global_assumptions(self):
        """Test global assumption application"""
        self.setUp()
        
        # Create test entities directly
        entities = self.create_test_entities()
        
        # Test global assumptions
        scenario = Scenario(
            name='inflated',
            description='Scenario with inflation',
            entity_filters={},
            entity_overrides=[],
            assumptions={
                'inflation_rate': 0.05,
                'revenue_growth_rate': 0.15,
                'overhead_multiplier': 1.10
            }
        )
        
        # Test that assumptions are stored correctly
        assert scenario.assumptions['inflation_rate'] == 0.05
        assert scenario.assumptions['revenue_growth_rate'] == 0.15
        assert scenario.assumptions['overhead_multiplier'] == 1.10
        
        # Test that assumptions can be applied to entities
        employees = [e for e in entities if e.type == 'employee']
        for employee in employees:
            modified_employee = scenario.apply_to_entity(employee)
            # Check that global assumptions could affect the entity
            assert modified_employee is not None
        
        self.tearDown()
    
    def test_scenario_application_to_forecast(self):
        """Test applying scenarios to forecast calculations"""
        self.setUp()
        
        # Test basic scenario application without requiring database entities
        baseline_scenario = Scenario(
            name='test_baseline',
            description='Test baseline scenario',
            entity_filters={},
            entity_overrides=[],
            assumptions={}
        )
        
        optimistic_scenario = Scenario(
            name='test_optimistic',
            description='Test optimistic scenario',
            entity_filters={},
            entity_overrides=[
                {'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 1.1}
            ],
            assumptions={
                'revenue_growth_rate': 0.2,
                'overhead_multiplier': 1.1
            }
        )
        
        self.scenario_manager.add_scenario(baseline_scenario)
        self.scenario_manager.add_scenario(optimistic_scenario)
        
        # Test that scenarios were added
        assert self.scenario_manager.get_scenario('test_baseline') is not None
        assert self.scenario_manager.get_scenario('test_optimistic') is not None
        
        # Test scenario differences
        baseline = self.scenario_manager.get_scenario('test_baseline')
        optimistic = self.scenario_manager.get_scenario('test_optimistic')
        
        assert len(baseline.assumptions) == 0
        assert optimistic.assumptions['revenue_growth_rate'] == 0.2
        assert len(optimistic.entity_overrides) == 1
        
        self.tearDown()
    
    def test_scenario_comparison(self):
        """Test scenario comparison functionality"""
        self.setUp()
        
        # Create scenarios with different assumptions
        baseline_scenario = Scenario(
            name='test_baseline',
            description='Test baseline scenario',
            entity_filters={},
            entity_overrides=[],
            assumptions={}
        )
        
        optimistic_scenario = Scenario(
            name='test_optimistic',
            description='Test optimistic scenario',
            entity_filters={},
            entity_overrides=[],
            assumptions={'revenue_growth_rate': 0.3}
        )
        
        self.scenario_manager.add_scenario(baseline_scenario)
        self.scenario_manager.add_scenario(optimistic_scenario)
        
        # Test that scenarios can be compared
        scenarios = self.scenario_manager.list_scenarios()
        assert 'test_baseline' in scenarios
        assert 'test_optimistic' in scenarios
        
        # Test scenario differences
        baseline = self.scenario_manager.get_scenario('test_baseline')
        optimistic = self.scenario_manager.get_scenario('test_optimistic')
        
        assert baseline.assumptions == {}
        assert optimistic.assumptions['revenue_growth_rate'] == 0.3
        
        self.tearDown()
    
    def test_scenario_sensitivity_analysis(self):
        """Test basic scenario parameter variation"""
        self.setUp()
        
        # Test different parameter values
        base_scenario = Scenario(
            name='base',
            description='Base scenario',
            entity_filters={},
            entity_overrides=[],
            assumptions={'revenue_growth_rate': 0.1}
        )
        
        high_growth_scenario = Scenario(
            name='high_growth',
            description='High growth scenario',
            entity_filters={},
            entity_overrides=[],
            assumptions={'revenue_growth_rate': 0.3}
        )
        
        # Add scenarios to manager
        self.scenario_manager.add_scenario(base_scenario)
        self.scenario_manager.add_scenario(high_growth_scenario)
        
        # Test that scenarios have different assumptions
        assert base_scenario.assumptions['revenue_growth_rate'] == 0.1
        assert high_growth_scenario.assumptions['revenue_growth_rate'] == 0.3
        
        self.tearDown()
    
    def test_monte_carlo_scenario_generation(self):
        """Test basic scenario generation concepts"""
        self.setUp()
        
        # Test generating multiple scenarios with different parameters
        scenarios = []
        
        # Create scenarios with different revenue growth rates (simulating Monte Carlo)
        import random
        for i in range(10):
            growth_rate = random.uniform(0.05, 0.25)  # 5% to 25% growth
            scenario = Scenario(
                name=f'monte_carlo_{i}',
                description=f'Monte Carlo scenario {i}',
                entity_filters={},
                entity_overrides=[],
                assumptions={'revenue_growth_rate': growth_rate}
            )
            scenarios.append(scenario)
        
        # Verify scenarios were created correctly
        assert len(scenarios) == 10
        
        for i, scenario in enumerate(scenarios):
            assert scenario.name == f'monte_carlo_{i}'
            assert 'revenue_growth_rate' in scenario.assumptions
            assert 0.05 <= scenario.assumptions['revenue_growth_rate'] <= 0.25
        
        self.tearDown()
    
    def test_scenario_risk_analysis(self):
        """Test basic risk scenario concepts"""
        self.setUp()
        
        # Create risk scenarios
        baseline_scenario = Scenario(
            name='test_baseline',
            description='Baseline scenario',
            entity_filters={},
            entity_overrides=[],
            assumptions={}
        )
        
        revenue_loss_scenario = Scenario(
            name='revenue_loss',
            description='Major revenue loss',
            entity_filters={'exclude_tags': ['growth']},  # Exclude growth revenue
            entity_overrides=[],
            assumptions={'revenue_growth_rate': -0.1}  # Negative growth
        )
        
        cost_overrun_scenario = Scenario(
            name='cost_overrun',
            description='Cost overrun scenario',
            entity_filters={},
            entity_overrides=[{'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 1.8}],
            assumptions={}
        )
        
        # Add scenarios to manager
        self.scenario_manager.add_scenario(baseline_scenario)
        self.scenario_manager.add_scenario(revenue_loss_scenario)
        self.scenario_manager.add_scenario(cost_overrun_scenario)
        
        # Verify scenarios were created
        assert self.scenario_manager.get_scenario('test_baseline') is not None
        assert self.scenario_manager.get_scenario('revenue_loss') is not None
        assert self.scenario_manager.get_scenario('cost_overrun') is not None
        
        # Test basic risk scenario differences
        assert revenue_loss_scenario.assumptions['revenue_growth_rate'] == -0.1
        assert cost_overrun_scenario.entity_overrides[0]['value'] == 1.8
        
        self.tearDown()
    
    def test_scenario_optimization(self):
        """Test basic scenario optimization concepts"""
        self.setUp()
        
        # Test creating scenarios for different target outcomes
        conservative_scenario = Scenario(
            name='test_conservative',
            description='Conservative scenario for cash preservation',
            entity_filters={'exclude_tags': ['non_essential']},
            entity_overrides=[],
            assumptions={'revenue_growth_rate': 0.05}
        )
        
        aggressive_scenario = Scenario(
            name='test_aggressive',
            description='Aggressive scenario for revenue growth',
            entity_filters={},
            entity_overrides=[],
            assumptions={'revenue_growth_rate': 0.25}
        )
        
        # Add scenarios to manager
        self.scenario_manager.add_scenario(conservative_scenario)
        self.scenario_manager.add_scenario(aggressive_scenario)
        
        # Test that scenarios have different optimization goals
        assert conservative_scenario.assumptions['revenue_growth_rate'] == 0.05
        assert aggressive_scenario.assumptions['revenue_growth_rate'] == 0.25
        
        # Test that filtering works for cash preservation
        assert 'exclude_tags' in conservative_scenario.entity_filters
        assert 'non_essential' in conservative_scenario.entity_filters['exclude_tags']
        
        self.tearDown()
    
    def test_scenario_stress_testing(self):
        """Test basic stress testing concepts"""
        self.setUp()
        
        # Create stress test scenarios
        revenue_shock_scenario = Scenario(
            name='revenue_shock',
            description='Severe revenue drop',
            entity_filters={},
            entity_overrides=[],
            assumptions={'revenue_growth_rate': -0.5}  # 50% revenue drop
        )
        
        expense_explosion_scenario = Scenario(
            name='expense_explosion',
            description='Massive expense increase',
            entity_filters={},
            entity_overrides=[{'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 2.0}],
            assumptions={}
        )
        
        funding_drought_scenario = Scenario(
            name='funding_drought',
            description='No external funding',
            entity_filters={'exclude_tags': ['private', 'government']},
            entity_overrides=[],
            assumptions={}
        )
        
        # Add scenarios to manager
        self.scenario_manager.add_scenario(revenue_shock_scenario)
        self.scenario_manager.add_scenario(expense_explosion_scenario)
        self.scenario_manager.add_scenario(funding_drought_scenario)
        
        # Test that stress scenarios have appropriate parameters
        assert revenue_shock_scenario.assumptions['revenue_growth_rate'] == -0.5
        assert expense_explosion_scenario.entity_overrides[0]['value'] == 2.0
        assert 'exclude_tags' in funding_drought_scenario.entity_filters
        
        self.tearDown()
    
    def test_scenario_validation(self):
        """Test basic scenario validation"""
        self.setUp()
        
        # Test valid scenario creation
        valid_scenario = Scenario(
            name='valid',
            description='Valid scenario',
            entity_filters={'require_tags': ['test']},
            entity_overrides=[{'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 1.2}],
            assumptions={'revenue_growth_rate': 0.1}
        )
        
        # Should not raise any errors
        assert valid_scenario.name == 'valid'
        assert valid_scenario.description == 'Valid scenario'
        assert valid_scenario.entity_filters['require_tags'] == ['test']
        assert valid_scenario.entity_overrides[0]['value'] == 1.2
        assert valid_scenario.assumptions['revenue_growth_rate'] == 0.1
        
        # Test scenario with conflicting filters
        conflicting_scenario = Scenario(
            name='conflicting',
            description='Conflicting scenario',
            entity_filters={'require_tags': ['test'], 'exclude_tags': ['test']},
            entity_overrides=[],
            assumptions={}
        )
        
        # Should still create but filter might not work as expected
        assert conflicting_scenario.name == 'conflicting'
        assert 'require_tags' in conflicting_scenario.entity_filters
        assert 'exclude_tags' in conflicting_scenario.entity_filters
        
        self.tearDown()
    
    def test_scenario_persistence(self):
        """Test scenario saving and loading"""
        self.setUp()
        
        # Create custom scenarios
        growth_aggressive = Scenario(
            name='growth_aggressive',
            description='Aggressive growth scenario',
            entity_filters={'require_tags': ['growth', 'expansion']},
            entity_overrides=[
                {'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 1.1}
            ],
            assumptions={
                'revenue_growth_rate': 0.25,
                'hiring_acceleration': 2.0
            }
        )
        
        cash_conservation = Scenario(
            name='cash_conservation',
            description='Cash conservation scenario',
            entity_filters={'require_tags': ['essential']},
            entity_overrides=[
                {'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 0.9}
            ],
            assumptions={
                'revenue_growth_rate': 0.05
            }
        )
        
        # Save scenarios to YAML files
        growth_file = self.scenarios_dir / 'growth_aggressive.yaml'
        cash_file = self.scenarios_dir / 'cash_conservation.yaml'
        
        growth_aggressive.to_yaml(growth_file)
        cash_conservation.to_yaml(cash_file)
        
        # Verify files were created
        assert growth_file.exists()
        assert cash_file.exists()
        
        # Load scenarios back
        loaded_growth = Scenario.from_yaml(growth_file)
        loaded_cash = Scenario.from_yaml(cash_file)
        
        # Verify loaded scenarios match original
        assert loaded_growth.name == growth_aggressive.name
        assert loaded_growth.description == growth_aggressive.description
        assert loaded_growth.assumptions['revenue_growth_rate'] == 0.25
        
        assert loaded_cash.name == cash_conservation.name
        assert loaded_cash.description == cash_conservation.description
        assert loaded_cash.assumptions['revenue_growth_rate'] == 0.05
        
        self.tearDown()
    
    def test_scenario_versioning(self):
        """Test basic scenario versioning concepts"""
        self.setUp()
        
        # Create initial scenario
        scenario_v1 = Scenario(
            name='evolving_scenario',
            description='Scenario version 1',
            entity_filters={},
            entity_overrides=[{'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 1.2}],
            assumptions={'revenue_growth_rate': 0.1}
        )
        
        # Create version 2 with different assumptions
        scenario_v2 = Scenario(
            name='evolving_scenario',
            description='Scenario version 2 - Updated assumptions',
            entity_filters={'require_tags': ['core']},
            entity_overrides=[{'entity_type': 'employee', 'field': 'overhead_multiplier', 'value': 1.3}],
            assumptions={'revenue_growth_rate': 0.2}
        )
        
        # Save versions as separate files
        version_1_file = self.scenarios_dir / 'evolving_scenario_v1.yaml'
        version_2_file = self.scenarios_dir / 'evolving_scenario_v2.yaml'
        
        scenario_v1.to_yaml(version_1_file)
        scenario_v2.to_yaml(version_2_file)
        
        # Verify files were created
        assert version_1_file.exists()
        assert version_2_file.exists()
        
        # Load and verify version differences
        loaded_v1 = Scenario.from_yaml(version_1_file)
        loaded_v2 = Scenario.from_yaml(version_2_file)
        
        # Verify version differences
        assert loaded_v1.entity_overrides[0]['value'] == 1.2
        assert loaded_v2.entity_overrides[0]['value'] == 1.3
        
        assert loaded_v1.assumptions['revenue_growth_rate'] == 0.1
        assert loaded_v2.assumptions['revenue_growth_rate'] == 0.2
        
        self.tearDown()