import pytest
import tempfile
import shutil
import time
import psutil
import os
import asyncio
import threading
from pathlib import Path
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from cashcow.storage.database import EntityStore
from cashcow.storage.yaml_loader import YamlEntityLoader
from cashcow.engine.cashflow import CashFlowEngine
from cashcow.engine.calculators import CalculatorRegistry
from cashcow.engine.builtin_calculators import register_builtin_calculators
from cashcow.engine.kpis import KPICalculator
from cashcow.models.entities import Employee, Grant, Investment, Facility, Equipment, Software


class TestPerformanceScaling:
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'perf_test.db'
        self.entities_dir = Path(self.temp_dir) / 'entities'
        self.entities_dir.mkdir(parents=True)
        
        # Initialize components
        self.store = EntityStore(str(self.db_path))
        self.loader = YamlEntityLoader(self.entities_dir)
        self.registry = CalculatorRegistry()
        register_builtin_calculators(self.registry)
        self.engine = CashFlowEngine(self.store)
        self.kpi_calculator = KPICalculator()
        
        # Performance tracking
        self.process = psutil.Process(os.getpid())
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def create_entities_batch(self, count, entity_type='employee', start_offset_days=0):
        """Create a batch of entities for performance testing"""
        entities = []
        
        for i in range(count):
            start_date = date(2024, 1, 1) + timedelta(days=start_offset_days + (i % 365))
            
            if entity_type == 'employee':
                entity = Employee(
                    type='employee',
                    name=f'Employee {i}',
                    start_date=start_date,
                    salary=50000 + (i % 100000),
                    pay_frequency='monthly',
                    overhead_multiplier=1.1 + (i % 10) * 0.05,
                    equity_shares=1000 + (i % 50000),
                    vesting_years=4,
                    cliff_years=1,
                    tags=[f'batch_{i // 100}', f'level_{i % 5}']
                )
            elif entity_type == 'grant':
                entity = Grant(
                    type='grant',
                    name=f'Grant {i}',
                    start_date=start_date,
                    amount=100000 + (i % 1000000),
                    grantor=f'Agency {i % 10}',
                    milestones=[
                        {'name': f'Phase {j}', 'amount': 50000, 'due_date': (start_date + timedelta(days=j*180)).isoformat()}
                        for j in range(1, 3)
                    ],
                    tags=[f'batch_{i // 100}', f'agency_{i % 10}']
                )
            elif entity_type == 'investment':
                entity = Investment(
                    type='investment',
                    name=f'Investment {i}',
                    start_date=start_date,
                    amount=500000 + (i % 5000000),
                    investor=f'Investor {i % 20}',
                    disbursement_schedule=[
                        {'date': (start_date + timedelta(days=j*90)).isoformat(), 'amount': 250000}
                        for j in range(1, 3)
                    ],
                    tags=[f'batch_{i // 100}', f'investor_{i % 20}']
                )
            elif entity_type == 'facility':
                entity = Facility(
                    type='facility',
                    name=f'Facility {i}',
                    start_date=start_date,
                    monthly_cost=5000 + (i % 50000),
                    utilities={'electricity': 1000 + (i % 5000), 'water': 200 + (i % 1000)},
                    square_footage=1000 + (i % 20000),
                    tags=[f'batch_{i // 100}', f'size_{i % 3}']
                )
            elif entity_type == 'equipment':
                entity = Equipment(
                    type='equipment',
                    name=f'Equipment {i}',
                    start_date=start_date,
                    purchase_price=50000 + (i % 500000),
                    useful_life_years=5 + (i % 10),
                    maintenance_percentage=0.03 + (i % 10) * 0.01,
                    tags=[f'batch_{i // 100}', f'category_{i % 5}']
                )
            else:
                entity = Software(
                    type='software',
                    name=f'Software {i}',
                    start_date=start_date,
                    purchase_price=10000 + (i % 100000),
                    useful_life_years=3 + (i % 5),
                    maintenance_percentage=0.15 + (i % 5) * 0.05,
                    users=5 + (i % 100),
                    tags=[f'batch_{i // 100}', f'category_{i % 5}']
                )
            
            entities.append(entity)
        
        return entities
    
    def measure_performance(self, operation_func, *args, **kwargs):
        """Measure performance metrics for an operation"""
        # Get initial memory usage
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Measure execution time
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        
        # Get final memory usage
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'result': result,
            'execution_time': end_time - start_time,
            'memory_before': memory_before,
            'memory_after': memory_after,
            'memory_used': memory_after - memory_before
        }
    
    def test_entity_storage_scaling(self):
        """Test entity storage performance with increasing dataset sizes"""
        self.setUp()
        
        test_sizes = [100, 500, 1000, 2500, 5000]
        results = {}
        
        for size in test_sizes:
            print(f"Testing entity storage with {size} entities...")
            
            # Create entities
            entities = self.create_entities_batch(size, 'employee')
            
            # Measure bulk insert performance
            perf_metrics = self.measure_performance(
                lambda: [self.store.add_entity(entity) for entity in entities]
            )
            
            # Measure query performance
            query_perf = self.measure_performance(
                lambda: self.store.get_entities_by_type('employee')
            )
            
            # Measure filtered query performance
            filter_perf = self.measure_performance(
                lambda: self.store.get_entities_by_tags(['batch_0'])
            )
            
            results[size] = {
                'insert_time': perf_metrics['execution_time'],
                'insert_memory': perf_metrics['memory_used'],
                'query_time': query_perf['execution_time'],
                'query_memory': query_perf['memory_used'],
                'filter_time': filter_perf['execution_time'],
                'filter_memory': filter_perf['memory_used']
            }
            
            # Performance assertions
            assert perf_metrics['execution_time'] < size * 0.01  # Should be less than 10ms per entity
            assert query_perf['execution_time'] < 5.0  # Query should complete in <5 seconds
            assert filter_perf['execution_time'] < 2.0  # Filtered query should complete in <2 seconds
        
        # Test scaling characteristics
        for i in range(1, len(test_sizes)):
            size_ratio = test_sizes[i] / test_sizes[i-1]
            time_ratio = results[test_sizes[i]]['insert_time'] / results[test_sizes[i-1]]['insert_time']
            
            # Time should scale roughly linearly (within 2x of size ratio)
            assert time_ratio < size_ratio * 2, f"Performance degradation too severe: {time_ratio} vs {size_ratio}"
        
        print("Entity storage scaling test passed!")
        print(f"Results: {results}")
        
        self.tearDown()
    
    def test_forecast_calculation_scaling(self):
        """Test forecast calculation performance with increasing dataset sizes"""
        self.setUp()
        
        test_sizes = [50, 100, 250, 500, 1000]
        results = {}
        
        for size in test_sizes:
            print(f"Testing forecast calculation with {size} entities...")
            
            # Create mixed entity types
            employees = self.create_entities_batch(size // 2, 'employee')
            grants = self.create_entities_batch(size // 4, 'grant')
            facilities = self.create_entities_batch(size // 4, 'facility')
            
            all_entities = employees + grants + facilities
            
            # Add entities to store
            for entity in all_entities:
                self.store.add_entity(entity)
            
            # Measure forecast calculation performance
            start_date = date(2024, 1, 1)
            end_date = date(2024, 12, 31)
            
            perf_metrics = self.measure_performance(
                self.engine.calculate_period,
                start_date, end_date
            )
            
            # Measure KPI calculation performance
            forecast_df = perf_metrics['result']
            kpi_perf = self.measure_performance(
                self.kpi_calculator.calculate_all_kpis,
                forecast_df
            )
            
            results[size] = {
                'forecast_time': perf_metrics['execution_time'],
                'forecast_memory': perf_metrics['memory_used'],
                'kpi_time': kpi_perf['execution_time'],
                'kpi_memory': kpi_perf['memory_used'],
                'total_time': perf_metrics['execution_time'] + kpi_perf['execution_time']
            }
            
            # Performance assertions
            assert perf_metrics['execution_time'] < size * 0.1  # Should be less than 100ms per entity
            assert kpi_perf['execution_time'] < 10.0  # KPI calculation should complete in <10 seconds
            assert len(forecast_df) == 12  # Should have 12 months of data
            assert not forecast_df.isnull().any().any()  # No null values
        
        # Test scaling characteristics
        for i in range(1, len(test_sizes)):
            size_ratio = test_sizes[i] / test_sizes[i-1]
            time_ratio = results[test_sizes[i]]['total_time'] / results[test_sizes[i-1]]['total_time']
            
            # Time should scale sub-quadratically
            assert time_ratio < size_ratio ** 1.5, f"Performance degradation too severe: {time_ratio} vs {size_ratio}"
        
        print("Forecast calculation scaling test passed!")
        print(f"Results: {results}")
        
        self.tearDown()
    
    @pytest.mark.asyncio
    async def test_async_performance_scaling(self):
        """Test asynchronous operation performance"""
        self.setUp()
        
        # Create test entities
        entities = self.create_entities_batch(500, 'employee')
        for entity in entities:
            self.store.add_entity(entity)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Test sync vs async performance
        sync_perf = self.measure_performance(
            self.engine.calculate_period,
            start_date, end_date
        )
        
        async_perf = self.measure_performance(
            lambda: asyncio.run(self.engine.calculate_period_async(start_date, end_date))
        )
        
        # Verify results are equivalent
        sync_df = sync_perf['result']
        async_df = async_perf['result']
        pd.testing.assert_frame_equal(sync_df, async_df)
        
        # Async should be at least as fast as sync (within 20% tolerance)
        assert async_perf['execution_time'] <= sync_perf['execution_time'] * 1.2
        
        print(f"Sync time: {sync_perf['execution_time']:.2f}s")
        print(f"Async time: {async_perf['execution_time']:.2f}s")
        
        self.tearDown()
    
    def test_parallel_calculation_performance(self):
        """Test parallel calculation performance"""
        self.setUp()
        
        # Create test entities
        entities = self.create_entities_batch(500, 'employee')
        for entity in entities:
            self.store.add_entity(entity)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Test different execution modes
        sync_perf = self.measure_performance(
            self.engine.calculate_period,
            start_date, end_date
        )
        
        parallel_perf = self.measure_performance(
            self.engine.calculate_parallel,
            start_date, end_date
        )
        
        # Verify results are equivalent
        sync_df = sync_perf['result']
        parallel_df = parallel_perf['result']
        pd.testing.assert_frame_equal(sync_df, parallel_df)
        
        # Parallel should be faster for large datasets (or at least not much slower)
        speedup_ratio = sync_perf['execution_time'] / parallel_perf['execution_time']
        assert speedup_ratio >= 0.5, f"Parallel execution too slow: {speedup_ratio}x speedup"
        
        print(f"Sync time: {sync_perf['execution_time']:.2f}s")
        print(f"Parallel time: {parallel_perf['execution_time']:.2f}s")
        print(f"Speedup: {speedup_ratio:.2f}x")
        
        self.tearDown()
    
    def test_memory_usage_scaling(self):
        """Test memory usage scaling with dataset size"""
        self.setUp()
        
        test_sizes = [100, 500, 1000, 2000]
        memory_results = {}
        
        for size in test_sizes:
            print(f"Testing memory usage with {size} entities...")
            
            # Clear any cached data
            if hasattr(self.engine, '_cache'):
                self.engine._cache.clear()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Get baseline memory
            baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # Create and add entities
            entities = self.create_entities_batch(size, 'employee')
            for entity in entities:
                self.store.add_entity(entity)
            
            storage_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # Run forecast calculation
            start_date = date(2024, 1, 1)
            end_date = date(2024, 12, 31)
            forecast_df = self.engine.calculate_period(start_date, end_date)
            
            calculation_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            memory_results[size] = {
                'baseline': baseline_memory,
                'after_storage': storage_memory,
                'after_calculation': calculation_memory,
                'storage_overhead': storage_memory - baseline_memory,
                'calculation_overhead': calculation_memory - storage_memory,
                'total_overhead': calculation_memory - baseline_memory
            }
            
            # Memory usage should be reasonable
            assert memory_results[size]['total_overhead'] < size * 0.1  # Less than 100KB per entity
        
        # Test memory scaling linearity
        for i in range(1, len(test_sizes)):
            size_ratio = test_sizes[i] / test_sizes[i-1]
            memory_ratio = (memory_results[test_sizes[i]]['total_overhead'] / 
                          memory_results[test_sizes[i-1]]['total_overhead'])
            
            # Memory should scale roughly linearly (within 2x of size ratio)
            assert memory_ratio < size_ratio * 2, f"Memory scaling too poor: {memory_ratio} vs {size_ratio}"
        
        print("Memory scaling test passed!")
        print(f"Memory results: {memory_results}")
        
        self.tearDown()
    
    def test_concurrent_access_performance(self):
        """Test performance under concurrent access"""
        self.setUp()
        
        # Create test entities
        entities = self.create_entities_batch(200, 'employee')
        for entity in entities:
            self.store.add_entity(entity)
        
        # Test concurrent read operations
        def read_worker():
            start_date = date(2024, 1, 1)
            end_date = date(2024, 12, 31)
            return self.engine.calculate_period(start_date, end_date)
        
        # Measure single-threaded performance
        single_perf = self.measure_performance(read_worker)
        
        # Measure multi-threaded performance
        num_threads = 4
        results = []
        errors = []
        
        def worker_wrapper():
            try:
                result = read_worker()
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        start_time = time.time()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker_wrapper)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == num_threads
        
        # All results should be identical
        base_result = results[0]
        for result in results[1:]:
            pd.testing.assert_frame_equal(base_result, result)
        
        # Concurrent access should complete in reasonable time
        expected_max_time = single_perf['execution_time'] * 2  # Allow 2x overhead
        assert concurrent_time < expected_max_time
        
        print(f"Single-threaded time: {single_perf['execution_time']:.2f}s")
        print(f"Concurrent time ({num_threads} threads): {concurrent_time:.2f}s")
        
        self.tearDown()
    
    def test_database_query_performance(self):
        """Test database query performance optimization"""
        self.setUp()
        
        # Create large dataset with various entity types
        all_entities = []
        all_entities.extend(self.create_entities_batch(1000, 'employee'))
        all_entities.extend(self.create_entities_batch(200, 'grant'))
        all_entities.extend(self.create_entities_batch(100, 'investment'))
        all_entities.extend(self.create_entities_batch(100, 'facility'))
        
        # Add all entities
        for entity in all_entities:
            self.store.add_entity(entity)
        
        # Test different query patterns
        query_tests = [
            ('get_all_entities', lambda: self.store.get_all_entities()),
            ('get_by_type', lambda: self.store.get_entities_by_type('employee')),
            ('get_by_tags', lambda: self.store.get_entities_by_tags(['batch_0'])),
            ('get_active', lambda: self.store.get_active_entities(date(2024, 6, 1))),
            ('filtered_query', lambda: self.store.query({
                'type': 'employee',
                'tags': ['level_1'],
                'active_on': date(2024, 6, 1)
            }))
        ]
        
        query_results = {}
        
        for query_name, query_func in query_tests:
            perf = self.measure_performance(query_func)
            query_results[query_name] = {
                'time': perf['execution_time'],
                'memory': perf['memory_used'],
                'result_count': len(perf['result'])
            }
            
            # All queries should complete quickly
            assert perf['execution_time'] < 5.0, f"{query_name} too slow: {perf['execution_time']}s"
        
        print("Database query performance test passed!")
        print(f"Query results: {query_results}")
        
        self.tearDown()
    
    def test_cache_performance_impact(self):
        """Test caching performance impact"""
        self.setUp()
        
        # Create test entities
        entities = self.create_entities_batch(300, 'employee')
        for entity in entities:
            self.store.add_entity(entity)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Disable caching
        if hasattr(self.engine, '_enable_cache'):
            self.engine._enable_cache = False
        
        # Measure without cache
        no_cache_perf1 = self.measure_performance(
            self.engine.calculate_period,
            start_date, end_date
        )
        
        no_cache_perf2 = self.measure_performance(
            self.engine.calculate_period,
            start_date, end_date
        )
        
        # Enable caching
        if hasattr(self.engine, '_enable_cache'):
            self.engine._enable_cache = True
        
        # Measure with cache
        cache_perf1 = self.measure_performance(
            self.engine.calculate_period,
            start_date, end_date
        )
        
        cache_perf2 = self.measure_performance(
            self.engine.calculate_period,
            start_date, end_date
        )
        
        # Verify results are consistent
        pd.testing.assert_frame_equal(no_cache_perf1['result'], cache_perf1['result'])
        pd.testing.assert_frame_equal(cache_perf1['result'], cache_perf2['result'])
        
        # Second cached call should be significantly faster
        if hasattr(self.engine, '_cache'):
            cache_speedup = cache_perf1['execution_time'] / cache_perf2['execution_time']
            assert cache_speedup > 2, f"Cache not effective: {cache_speedup}x speedup"
        
        print(f"No cache (1st): {no_cache_perf1['execution_time']:.2f}s")
        print(f"No cache (2nd): {no_cache_perf2['execution_time']:.2f}s")
        print(f"With cache (1st): {cache_perf1['execution_time']:.2f}s")
        print(f"With cache (2nd): {cache_perf2['execution_time']:.2f}s")
        
        self.tearDown()
    
    def test_large_dataset_edge_cases(self):
        """Test performance with edge cases in large datasets"""
        self.setUp()
        
        # Create dataset with edge cases
        entities = []
        
        # Many entities with same start date
        entities.extend(self.create_entities_batch(100, 'employee', 0))
        
        # Entities with staggered start dates
        for i in range(100):
            entities.extend(self.create_entities_batch(1, 'employee', i * 7))
        
        # Entities with very high values
        high_value_entities = self.create_entities_batch(50, 'investment')
        for entity in high_value_entities:
            entity.amount *= 100  # Make investments very large
        entities.extend(high_value_entities)
        
        # Entities with very low values
        low_value_entities = self.create_entities_batch(50, 'employee')
        for entity in low_value_entities:
            entity.salary = 1  # Minimal salary
        entities.extend(low_value_entities)
        
        # Add all entities
        for entity in entities:
            self.store.add_entity(entity)
        
        # Test forecast calculation with edge cases
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        perf = self.measure_performance(
            self.engine.calculate_period,
            start_date, end_date
        )
        
        forecast_df = perf['result']
        
        # Verify data integrity
        assert len(forecast_df) == 12
        assert not forecast_df.isnull().any().any()
        assert (forecast_df['revenue'] >= 0).all()
        assert (forecast_df['expenses'] >= 0).all()
        
        # Performance should still be reasonable
        assert perf['execution_time'] < len(entities) * 0.05  # 50ms per entity max
        
        print(f"Edge case performance test passed!")
        print(f"Time: {perf['execution_time']:.2f}s for {len(entities)} entities")
        
        self.tearDown()
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations"""
        self.setUp()
        
        # Create base entities
        entities = self.create_entities_batch(100, 'employee')
        for entity in entities:
            self.store.add_entity(entity)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Measure memory usage over multiple iterations
        memory_samples = []
        num_iterations = 10
        
        for i in range(num_iterations):
            # Run forecast calculation
            forecast_df = self.engine.calculate_period(start_date, end_date)
            
            # Calculate KPIs
            kpis = self.kpi_calculator.calculate_all_kpis(forecast_df)
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Sample memory usage
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            memory_samples.append(memory_mb)
            
            # Small delay to allow cleanup
            time.sleep(0.1)
        
        # Analyze memory trend
        initial_memory = memory_samples[0]
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be minimal (less than 50MB over 10 iterations)
        assert memory_growth < 50, f"Potential memory leak: {memory_growth:.2f}MB growth"
        
        # Check for consistent memory usage in later iterations
        stable_samples = memory_samples[-5:]  # Last 5 samples
        memory_variance = np.var(stable_samples)
        
        # Variance should be low in stable state
        assert memory_variance < 25, f"Memory usage not stable: variance {memory_variance:.2f}"
        
        print(f"Memory leak test passed!")
        print(f"Initial memory: {initial_memory:.2f}MB")
        print(f"Final memory: {final_memory:.2f}MB")
        print(f"Growth: {memory_growth:.2f}MB")
        print(f"Variance: {memory_variance:.2f}")
        
        self.tearDown()
    
    def test_stress_test_extreme_load(self):
        """Stress test with extreme load conditions"""
        self.setUp()
        
        print("Running stress test with extreme load...")
        
        # Create very large dataset
        large_entities = []
        large_entities.extend(self.create_entities_batch(2000, 'employee'))
        large_entities.extend(self.create_entities_batch(500, 'grant'))
        large_entities.extend(self.create_entities_batch(200, 'investment'))
        large_entities.extend(self.create_entities_batch(300, 'facility'))
        
        # Add entities in batches to avoid memory issues
        batch_size = 500
        for i in range(0, len(large_entities), batch_size):
            batch = large_entities[i:i+batch_size]
            for entity in batch:
                self.store.add_entity(entity)
            
            # Force garbage collection after each batch
            import gc
            gc.collect()
        
        total_entities = len(large_entities)
        print(f"Created {total_entities} entities")
        
        # Stress test: multiple forecast calculations
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)  # 2-year forecast
        
        perf = self.measure_performance(
            self.engine.calculate_period,
            start_date, end_date
        )
        
        forecast_df = perf['result']
        
        # Verify results
        assert len(forecast_df) == 24  # 24 months
        assert not forecast_df.isnull().any().any()
        
        # Performance should complete within reasonable time (5 minutes max)
        assert perf['execution_time'] < 300, f"Stress test too slow: {perf['execution_time']}s"
        
        # Memory usage should be reasonable (less than 1GB)
        assert perf['memory_after'] < 1024, f"Memory usage too high: {perf['memory_after']:.2f}MB"
        
        print(f"Stress test passed!")
        print(f"Time: {perf['execution_time']:.2f}s")
        print(f"Memory: {perf['memory_after']:.2f}MB")
        print(f"Throughput: {total_entities / perf['execution_time']:.1f} entities/second")
        
        self.tearDown()


class TestPerformanceBenchmarks:
    def setUp(self):
        """Set up benchmarking environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'benchmark.db'
        
        # Initialize components
        self.store = EntityStore(str(self.db_path))
        self.registry = CalculatorRegistry()
        register_builtin_calculators(self.registry)
        self.engine = CashFlowEngine(self.store)
        
        # Benchmark data
        self.benchmark_results = {}
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def run_benchmark(self, name, operation, *args, **kwargs):
        """Run a benchmark and record results"""
        # Warm up
        for _ in range(3):
            operation(*args, **kwargs)
        
        # Benchmark runs
        times = []
        for _ in range(10):
            start_time = time.time()
            result = operation(*args, **kwargs)
            end_time = time.time()
            times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = np.std(times)
        
        self.benchmark_results[name] = {
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'std_dev': std_dev,
            'all_times': times
        }
        
        print(f"{name}: {avg_time:.3f}s ± {std_dev:.3f}s (min: {min_time:.3f}s, max: {max_time:.3f}s)")
        
        return result
    
    def test_comprehensive_benchmarks(self):
        """Run comprehensive performance benchmarks"""
        self.setUp()
        
        # Create standard test dataset
        employees = []
        for i in range(500):
            employee = Employee(
                type='employee',
                name=f'Benchmark Employee {i}',
                start_date=date(2024, 1, 1),
                salary=60000 + i * 100,
                pay_frequency='monthly',
                overhead_multiplier=1.2 + i * 0.001,
                tags=[f'benchmark', f'level_{i % 5}']
            )
            employees.append(employee)
        
        # Benchmark: Entity storage
        self.run_benchmark(
            'Entity Storage (500 employees)',
            lambda: [self.store.add_entity(emp) for emp in employees]
        )
        
        # Benchmark: Entity queries
        self.run_benchmark(
            'Query All Entities',
            self.store.get_all_entities
        )
        
        self.run_benchmark(
            'Query by Type',
            self.store.get_entities_by_type, 'employee'
        )
        
        self.run_benchmark(
            'Query by Tags',
            self.store.get_entities_by_tags, ['benchmark']
        )
        
        # Benchmark: Forecast calculations
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        self.run_benchmark(
            'Forecast Calculation (12 months)',
            self.engine.calculate_period,
            start_date, end_date
        )
        
        # Benchmark: Extended forecast
        end_date_extended = date(2026, 12, 31)
        
        self.run_benchmark(
            'Extended Forecast (36 months)',
            self.engine.calculate_period,
            start_date, end_date_extended
        )
        
        # Generate benchmark report
        self.generate_benchmark_report()
        
        self.tearDown()
    
    def generate_benchmark_report(self):
        """Generate benchmark performance report"""
        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK REPORT")
        print("="*60)
        
        for benchmark_name, results in self.benchmark_results.items():
            print(f"\n{benchmark_name}:")
            print(f"  Average Time: {results['avg_time']:.3f}s")
            print(f"  Min Time:     {results['min_time']:.3f}s")
            print(f"  Max Time:     {results['max_time']:.3f}s")
            print(f"  Std Dev:      {results['std_dev']:.3f}s")
            print(f"  Variation:    {(results['std_dev']/results['avg_time']*100):.1f}%")
        
        # Performance targets
        targets = {
            'Entity Storage (500 employees)': 5.0,
            'Query All Entities': 1.0,
            'Query by Type': 0.5,
            'Query by Tags': 0.5,
            'Forecast Calculation (12 months)': 2.0,
            'Extended Forecast (36 months)': 6.0
        }
        
        print(f"\n{'Benchmark':<35} {'Target':<10} {'Actual':<10} {'Status'}")
        print("-" * 65)
        
        all_passed = True
        for benchmark_name, target in targets.items():
            if benchmark_name in self.benchmark_results:
                actual = self.benchmark_results[benchmark_name]['avg_time']
                status = "PASS" if actual <= target else "FAIL"
                if status == "FAIL":
                    all_passed = False
                
                print(f"{benchmark_name:<35} {target:<10.2f} {actual:<10.3f} {status}")
        
        print(f"\nOverall Performance: {'PASS' if all_passed else 'FAIL'}")
        
        return all_passed
    
    def test_regression_benchmarks(self):
        """Test for performance regression against baseline"""
        self.setUp()
        
        # Load baseline benchmarks (would be from previous runs)
        baseline_benchmarks = {
            'Entity Storage (500 employees)': 3.0,
            'Query All Entities': 0.5,
            'Forecast Calculation (12 months)': 1.5
        }
        
        # Run current benchmarks
        employees = []
        for i in range(500):
            employee = Employee(
                type='employee',
                name=f'Regression Test Employee {i}',
                start_date=date(2024, 1, 1),
                salary=60000 + i * 100,
                pay_frequency='monthly',
                overhead_multiplier=1.2,
                tags=['regression_test']
            )
            employees.append(employee)
        
        # Storage benchmark
        self.run_benchmark(
            'Entity Storage (500 employees)',
            lambda: [self.store.add_entity(emp) for emp in employees]
        )
        
        # Query benchmark
        self.run_benchmark(
            'Query All Entities',
            self.store.get_all_entities
        )
        
        # Forecast benchmark
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        self.run_benchmark(
            'Forecast Calculation (12 months)',
            self.engine.calculate_period,
            start_date, end_date
        )
        
        # Check for regression
        regression_threshold = 1.2  # 20% regression tolerance
        
        for benchmark_name, baseline_time in baseline_benchmarks.items():
            if benchmark_name in self.benchmark_results:
                current_time = self.benchmark_results[benchmark_name]['avg_time']
                regression_ratio = current_time / baseline_time
                
                print(f"{benchmark_name}: {regression_ratio:.2f}x baseline")
                
                # Assert no significant regression
                assert regression_ratio <= regression_threshold, \
                    f"Performance regression in {benchmark_name}: {regression_ratio:.2f}x baseline"
        
        print("Regression benchmarks passed!")
        
        self.tearDown()