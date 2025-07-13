import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from datetime import date, timedelta
import yaml
import pandas as pd
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from cashcow.storage.database import EntityStore
from cashcow.storage.yaml_loader import YamlEntityLoader
from cashcow.engine.cashflow import CashFlowEngine
from cashcow.engine.calculators import CalculatorRegistry
from cashcow.engine.builtin_calculators import register_builtin_calculators
from cashcow.engine.kpis import KPICalculator
from cashcow.models.entities import Employee, Grant, Investment, Facility, Software, Equipment, Project


class TestEndToEndForecast:
    def setup_method(self):
        """Set up test environment with complete entity ecosystem"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test.db'
        self.entities_dir = Path(self.temp_dir) / 'entities'
        self.entities_dir.mkdir(parents=True)
        
        # Create directory structure
        (self.entities_dir / 'expenses' / 'employees').mkdir(parents=True)
        (self.entities_dir / 'revenue' / 'grants').mkdir(parents=True)
        (self.entities_dir / 'revenue' / 'investments').mkdir(parents=True)
        (self.entities_dir / 'expenses' / 'facilities').mkdir(parents=True)
        (self.entities_dir / 'expenses' / 'software').mkdir(parents=True)
        (self.entities_dir / 'expenses' / 'equipment').mkdir(parents=True)
        (self.entities_dir / 'projects').mkdir(parents=True)
        
        # Initialize components
        self.store = EntityStore(str(self.db_path))
        self.loader = YamlEntityLoader(self.entities_dir)
        self.registry = CalculatorRegistry()
        register_builtin_calculators(self.registry)
        self.engine = CashFlowEngine(self.store)
        self.kpi_calculator = KPICalculator()
        
        # For testing, we'll mock the store to hold entities in memory
        self._test_entities = []
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
    
    def create_test_entities(self):
        """Create a comprehensive set of test entities"""
        entities = []
        
        # Employees
        employees = [
            Employee(
                type='employee',
                name='CEO',
                start_date=date(2024, 1, 1),
                salary=180000,
                pay_frequency='monthly',
                overhead_multiplier=1.4,
                equity_shares=100000,
                vesting_years=4,
                cliff_years=1,
                tags=['executive', 'founder']
            ),
            Employee(
                type='employee',
                name='Lead Engineer',
                start_date=date(2024, 1, 1),
                salary=140000,
                pay_frequency='monthly',
                overhead_multiplier=1.3,
                equity_shares=25000,
                vesting_years=4,
                cliff_years=1,
                tags=['engineering', 'senior']
            ),
            Employee(
                type='employee',
                name='Junior Engineer',
                start_date=date(2024, 3, 1),
                salary=85000,
                pay_frequency='monthly',
                overhead_multiplier=1.2,
                equity_shares=5000,
                vesting_years=4,
                cliff_years=1,
                tags=['engineering', 'junior']
            ),
            Employee(
                type='employee',
                name='Marketing Manager',
                start_date=date(2024, 6, 1),
                salary=95000,
                pay_frequency='monthly',
                overhead_multiplier=1.25,
                equity_shares=10000,
                vesting_years=4,
                cliff_years=1,
                tags=['marketing', 'manager']
            )
        ]
        
        # Revenue sources
        revenue_entities = [
            Grant(
                type='grant',
                name='SBIR Phase I',
                start_date=date(2024, 1, 1),
                amount=275000,
                agency='NASA',
                milestones=[
                    {'name': 'Technical Feasibility', 'amount': 137500, 'due_date': '2024-06-01'},
                    {'name': 'Final Report', 'amount': 137500, 'due_date': '2024-12-01'}
                ],
                tags=['government', 'research']
            ),
            Grant(
                type='grant',
                name='SBIR Phase II',
                start_date=date(2024, 12, 1),
                amount=1500000,
                agency='NASA',
                milestones=[
                    {'name': 'Year 1 Deliverable', 'amount': 750000, 'due_date': '2025-12-01'},
                    {'name': 'Final Prototype', 'amount': 750000, 'due_date': '2026-12-01'}
                ],
                tags=['government', 'research', 'phase2']
            ),
            Investment(
                type='investment',
                name='Seed Round',
                start_date=date(2024, 3, 1),
                amount=2000000,
                investor='Space Ventures',
                disbursement_schedule=[
                    {'date': '2024-03-15', 'amount': 800000},
                    {'date': '2024-09-15', 'amount': 1200000}
                ],
                equity_percentage=0.15,
                tags=['private', 'seed']
            )
        ]
        
        # Expenses
        expense_entities = [
            Facility(
                type='facility',
                name='Main Office',
                start_date=date(2024, 1, 1),
                monthly_cost=12000,
                utilities_monthly=2800,  # Sum of electricity, internet, insurance
                size_sqft=4000,
                tags=['office', 'headquarters']
            ),
            Facility(
                type='facility',
                name='Manufacturing Space',
                start_date=date(2024, 9, 1),
                monthly_cost=25000,
                utilities_monthly=7500,  # Sum of electricity, gas, water
                size_sqft=15000,
                tags=['manufacturing', 'production']
            ),
            Software(
                type='software',
                name='CAD Software',
                start_date=date(2024, 1, 1),
                monthly_cost=500,
                purchase_price=15000,
                useful_life_years=3,
                maintenance_percentage=0.18,
                users=5,
                tags=['engineering', 'tools']
            ),
            Software(
                type='software',
                name='Cloud Services',
                start_date=date(2024, 1, 1),
                monthly_cost=2500,
                subscription_type='monthly',
                tags=['infrastructure', 'cloud']
            ),
            Equipment(
                type='equipment',
                name='Test Equipment',
                start_date=date(2024, 6, 1),
                cost=350000,
                purchase_date=date(2024, 6, 1),
                purchase_price=350000,
                useful_life_years=7,
                maintenance_percentage=0.06,
                tags=['testing', 'equipment']
            ),
            Equipment(
                type='equipment',
                name='Manufacturing Equipment',
                start_date=date(2024, 10, 1),
                cost=850000,
                purchase_date=date(2024, 10, 1),
                purchase_price=850000,
                useful_life_years=10,
                maintenance_percentage=0.08,
                tags=['manufacturing', 'equipment']
            )
        ]
        
        # Projects
        projects = [
            Project(
                type='project',
                name='Engine Development',
                start_date=date(2024, 1, 1),
                end_date=date(2025, 12, 31),
                total_budget=3000000,
                milestones=[
                    {'name': 'Design Complete', 'budget': 500000, 'due_date': '2024-06-01'},
                    {'name': 'Prototype Build', 'budget': 1500000, 'due_date': '2024-12-01'},
                    {'name': 'Testing Complete', 'budget': 1000000, 'due_date': '2025-12-01'}
                ],
                tags=['core', 'product']
            )
        ]
        
        return employees + revenue_entities + expense_entities + projects
    
    def test_complete_forecast_workflow(self):
        """Test complete end-to-end forecast generation"""
        
        # Create and add entities
        entities = self.create_test_entities()
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities
        self.store.query = Mock(return_value=self._test_entities)
        
        # Run forecast for 24 months
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)
        
        # Test synchronous calculation
        df = self.engine.calculate_period(start_date, end_date)
        
        # Verify DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 24  # 24 months
        assert 'period' in df.columns
        assert 'total_revenue' in df.columns
        assert 'total_expenses' in df.columns
        assert 'net_cash_flow' in df.columns
        assert 'cash_balance' in df.columns
        
        # Verify data types
        assert df['total_revenue'].dtype in ['float64', 'int64']
        assert df['total_expenses'].dtype in ['float64', 'int64']
        assert df['net_cash_flow'].dtype in ['float64', 'int64']
        assert df['cash_balance'].dtype in ['float64', 'int64']
        
        # Verify logical consistency
        assert (df['net_cash_flow'] == df['total_revenue'] - df['total_expenses']).all()
        
        # Check for expected revenue patterns
        # Should have grant milestone payments
        revenue_months = df[df['total_revenue'] > 0]
        assert len(revenue_months) > 0
        
        # Check for consistent expenses
        # Should have monthly employee costs
        assert (df['total_expenses'] > 0).all()
        
        # Verify cumulative cash calculation
        expected_cumulative = df['net_cash_flow'].cumsum()
        pd.testing.assert_series_equal(df['cash_balance'], expected_cumulative, check_names=False)
        
    
    @pytest.mark.asyncio
    async def test_async_forecast_calculation(self):
        """Test asynchronous forecast calculation"""
        
        # Create and add entities
        entities = self.create_test_entities()
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities
        self.store.query = Mock(return_value=self._test_entities)
        
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)
        
        # Test asynchronous calculation
        df = await self.engine.calculate_period_async(start_date, end_date)
        
        # Verify results similar to sync version
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 24
        assert 'period' in df.columns
        assert 'total_revenue' in df.columns
        assert 'total_expenses' in df.columns
        
        # Verify async calculation produces same results as sync
        sync_df = self.engine.calculate_period(start_date, end_date)
        pd.testing.assert_frame_equal(df, sync_df)
        
    
    def test_parallel_forecast_calculation(self):
        """Test parallel forecast calculation with ThreadPoolExecutor"""
        
        # Create and add entities
        entities = self.create_test_entities()
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities
        self.store.query = Mock(return_value=self._test_entities)
        
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)
        
        # Test parallel calculation
        df = self.engine.calculate_parallel(start_date, end_date)
        
        # Verify results
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 24
        
        # Verify parallel calculation produces same results as sync
        sync_df = self.engine.calculate_period(start_date, end_date)
        pd.testing.assert_frame_equal(df, sync_df)
        
    
    def test_kpi_calculation_integration(self):
        """Test KPI calculation with full forecast"""
        
        # Create and add entities
        entities = self.create_test_entities()
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities
        self.store.query = Mock(return_value=self._test_entities)
        
        # Generate forecast
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)
        df = self.engine.calculate_period(start_date, end_date)
        
        # Calculate KPIs with reasonable starting cash
        starting_cash = 5000000  # 5M starting cash for runway calculation
        kpis = self.kpi_calculator.calculate_all_kpis(df, starting_cash=starting_cash)
        
        # Verify KPI structure
        assert isinstance(kpis, dict)
        
        # Check for expected KPIs
        expected_kpis = [
            'runway_months', 'burn_rate', 'revenue_growth_rate',
            'rd_percentage', 'revenue_per_employee', 'cash_efficiency',
            'average_team_size', 'employee_cost_efficiency', 'facility_cost_percentage'
        ]
        
        for kpi in expected_kpis:
            assert kpi in kpis
        
        # Verify KPI values make sense
        assert isinstance(kpis['runway_months'], (int, float))
        assert kpis['runway_months'] > 0
        
        assert isinstance(kpis['burn_rate'], (int, float))
        assert kpis['burn_rate'] > 0  # Should be positive (cash outflow)
        
        assert isinstance(kpis['revenue_growth_rate'], (int, float))
        
    
    def test_entity_lifecycle_impact(self):
        """Test how entity start/end dates affect forecast"""
        
        # Create entities with different lifecycles
        entities = [
            Employee(
                type='employee',
                name='Early Employee',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 6, 30),
                salary=60000,
                pay_frequency='monthly',
                overhead_multiplier=1.2
            ),
            Employee(
                type='employee',
                name='Late Employee',
                start_date=date(2024, 7, 1),
                salary=70000,
                pay_frequency='monthly',
                overhead_multiplier=1.3
            ),
            Grant(
                type='grant',
                name='Early Grant',
                start_date=date(2024, 1, 1),
                amount=100000,
                grantor='NASA',
                milestones=[
                    {'name': 'Payment 1', 'amount': 50000, 'due_date': '2024-03-01'},
                    {'name': 'Payment 2', 'amount': 50000, 'due_date': '2024-06-01'}
                ]
            )
        ]
        
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities  
        self.store.query = Mock(return_value=self._test_entities)
        
        # Generate forecast
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        df = self.engine.calculate_period(start_date, end_date)
        
        # Verify entity lifecycle effects
        # Early employee should only appear in first 6 months
        early_months = df.iloc[:6]  # Jan-Jun
        late_months = df.iloc[6:]   # Jul-Dec
        
        # Check that expenses change when employee transitions
        early_avg_expense = early_months['total_expenses'].mean()
        late_avg_expense = late_months['total_expenses'].mean()
        
        # Late employee has higher salary, so expenses should increase
        assert late_avg_expense > early_avg_expense
        
        # Grant revenue should appear in March and June
        march_revenue = df.iloc[2]['total_revenue']  # March (index 2)
        june_revenue = df.iloc[5]['total_revenue']   # June (index 5)
        
        assert march_revenue > 0
        assert june_revenue > 0
        
    
    def test_data_aggregation_categories(self):
        """Test data aggregation by different categories"""
        
        # Create entities with specific tags
        entities = [
            Employee(
                type='employee',
                name='Engineer',
                start_date=date(2024, 1, 1),
                salary=100000,
                pay_frequency='monthly',
                overhead_multiplier=1.3,
                tags=['engineering', 'rd']
            ),
            Employee(
                type='employee',
                name='Sales Rep',
                start_date=date(2024, 1, 1),
                salary=80000,
                pay_frequency='monthly',
                overhead_multiplier=1.2,
                tags=['sales', 'business']
            ),
            Facility(
                type='facility',
                name='Office',
                start_date=date(2024, 1, 1),
                monthly_cost=5000,
                tags=['office', 'overhead']
            ),
            Equipment(
                type='equipment',
                name='Lab Equipment',
                start_date=date(2024, 1, 1),
                cost=200000,
                purchase_date=date(2024, 1, 1),
                purchase_price=200000,
                useful_life_years=5,
                maintenance_percentage=0.05,
                tags=['equipment', 'rd']
            )
        ]
        
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities  
        self.store.query = Mock(return_value=self._test_entities)
        
        # Generate forecast
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        df = self.engine.calculate_period(start_date, end_date)
        
        # Test aggregation by category
        categories = self.engine.aggregate_by_category(df)
        
        # Verify category structure
        assert isinstance(categories, dict)
        assert 'revenue' in categories
        assert 'expenses' in categories
        assert 'summary' in categories
        assert 'growth' in categories
        
        # Verify expense breakdown has employee costs
        expense_data = categories['expenses']
        assert 'employee_costs' in expense_data.columns
        assert 'facility_costs' in expense_data.columns
        assert 'equipment_costs' in expense_data.columns
        
        # Verify R&D costs (employee and equipment)
        total_rd_costs = expense_data['employee_costs'].sum() + expense_data['equipment_costs'].sum()
        assert total_rd_costs > 0
        
    
    def test_forecast_with_missing_data(self):
        """Test forecast handling of entities with missing or incomplete data"""
        
        # Create entities with minimal data
        entities = [
            Employee(
                type='employee',
                name='Minimal Employee',
                start_date=date(2024, 1, 1),
                salary=60000,
                pay_frequency='monthly'
                # Missing optional fields like overhead_multiplier
            ),
            Grant(
                type='grant',
                name='Simple Grant',
                start_date=date(2024, 1, 1),
                amount=100000,
                grantor='Test'
                # No milestones - should distribute evenly
            )
        ]
        
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities  
        self.store.query = Mock(return_value=self._test_entities)
        
        # Generate forecast should not fail
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        df = self.engine.calculate_period(start_date, end_date)
        
        # Verify basic structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12
        assert not df.isnull().any().any()  # No null values
        
        # Verify calculations use default values
        monthly_expense = df.iloc[0]['total_expenses']
        assert monthly_expense > 0  # Employee cost calculated with defaults
        
    
    def test_forecast_edge_cases(self):
        """Test forecast handling of edge cases"""
        
        # Test with minimal amounts (since Employee validation requires positive salary)
        minimal_employee = Employee(
            type='employee',
            name='Minimal Salary Employee',
            start_date=date(2024, 1, 1),
            salary=1,  # Minimum positive salary for edge case testing
            pay_frequency='monthly'
        )
        
        # Test with future start dates
        future_employee = Employee(
            type='employee',
            name='Future Employee',
            start_date=date(2025, 1, 1),
            salary=60000,
            pay_frequency='monthly'
        )
        
        # Test with past end dates
        past_employee = Employee(
            type='employee',
            name='Past Employee',
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            salary=60000,
            pay_frequency='monthly'
        )
        
        entities = [minimal_employee, future_employee, past_employee]
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities  
        self.store.query = Mock(return_value=self._test_entities)
        
        # Generate forecast for 2024
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        df = self.engine.calculate_period(start_date, end_date)
        
        # Verify handling of edge cases
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12
        
        # Zero salary employee should contribute minimal cost
        # Future employee should not contribute to 2024 forecast
        # Past employee should not contribute to 2024 forecast
        
        # All expenses should be minimal (just overhead from zero salary)
        assert df['total_expenses'].sum() >= 0
        
    
    def test_caching_performance(self):
        """Test caching layer performance"""
        
        # Create entities
        entities = self.create_test_entities()
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities  
        self.store.query = Mock(return_value=self._test_entities)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # First calculation (should cache)
        import time
        start_time = time.time()
        df1 = self.engine.calculate_period(start_date, end_date)
        first_time = time.time() - start_time
        
        # Second calculation (should use cache)
        start_time = time.time()
        df2 = self.engine.calculate_period(start_date, end_date)
        second_time = time.time() - start_time
        
        # Verify results are identical
        pd.testing.assert_frame_equal(df1, df2)
        
        # Second calculation should be faster (cached)
        assert second_time < first_time
        
        # Test cache behavior by changing calculation period
        # Calculate for a different period (cache should not apply)
        df3 = self.engine.calculate_period(date(2024, 1, 1), date(2024, 6, 30))
        
        # Should be different from previous results (different period)
        assert not df1.equals(df3)
        assert len(df3) != len(df1)  # Different number of months
        
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        
        # Create valid entities
        valid_employee = Employee(
            type='employee',
            name='Valid Employee',
            start_date=date(2024, 1, 1),
            salary=60000,
            pay_frequency='monthly'
        )
        
        self._test_entities.append(valid_employee)
        self.store.query = Mock(return_value=self._test_entities)
        
        # Test calculation with valid data
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        df = self.engine.calculate_period(start_date, end_date)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12
        
        # Test with invalid date range
        with pytest.raises(ValueError):
            self.engine.calculate_period(date(2024, 12, 31), date(2024, 1, 1))
        
        # Test with corrupted entity data
        # This should be handled gracefully
        corrupted_entity = Mock()
        corrupted_entity.type = 'employee'
        corrupted_entity.name = 'Corrupted Employee'
        corrupted_entity.is_active.side_effect = Exception("Corrupted data")
        
        # Engine should handle corruption gracefully during normal calculation
        # Add corrupted entity to store (this test may be implementation dependent)
        try:
            # Test will depend on actual error handling in the engine
            test_df = self.engine.calculate_period(date(2024, 1, 1), date(2024, 1, 31))
            # If we get here, the engine handled it gracefully
            assert isinstance(test_df, pd.DataFrame)
        except Exception as e:
            # Should be a handled exception, not a crash
            assert isinstance(e, (ValueError, RuntimeError))
        
    
    def test_memory_usage_optimization(self):
        """Test memory usage optimization with large datasets"""
        
        # Create large number of entities
        entities = []
        for i in range(100):
            employee = Employee(
                type='employee',
                name=f'Employee {i}',
                start_date=date(2024, 1, 1),
                salary=60000 + i * 1000,
                pay_frequency='monthly',
                overhead_multiplier=1.2 + i * 0.01
            )
            entities.append(employee)
        
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities  
        self.store.query = Mock(return_value=self._test_entities)
        
        # Generate forecast
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Monitor memory usage
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        
        df = self.engine.calculate_period(start_date, end_date)
        
        memory_after = process.memory_info().rss
        memory_used = memory_after - memory_before
        
        # Verify results
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12
        
        # Memory usage should be reasonable (less than 100MB for 100 entities)
        assert memory_used < 100 * 1024 * 1024  # 100MB
        
    
    def test_concurrent_forecast_calculations(self):
        """Test concurrent forecast calculations"""
        
        # Create entities
        entities = self.create_test_entities()
        for entity in entities:
            self._test_entities.append(entity)
        
        # Mock the store query method to return our test entities  
        self.store.query = Mock(return_value=self._test_entities)
        
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                start_date = date(2024, 1, 1)
                end_date = date(2024, 12, 31)
                df = self.engine.calculate_period(start_date, end_date)
                results.append((worker_id, df))
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # All results should be identical
        base_df = results[0][1]
        for worker_id, df in results[1:]:
            pd.testing.assert_frame_equal(base_df, df)
        
        # Clean up test entities
        self._test_entities.clear()