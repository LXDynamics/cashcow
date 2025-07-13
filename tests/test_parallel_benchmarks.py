import pytest
import tempfile
import shutil
import time
import asyncio
import threading
from pathlib import Path
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from cashcow.storage.database import EntityStore
from cashcow.engine.cashflow import CashFlowEngine
from cashcow.engine.calculators import CalculatorRegistry
from cashcow.engine.builtin_calculators import register_builtin_calculators
from cashcow.engine.kpis import KPICalculator
from cashcow.models.entities import Employee, Grant, Investment, Facility


class TestParallelCalculationBenchmarks:
    def setUp(self):
        """Set up test environment for parallel benchmarks"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'parallel_test.db'
        
        # Initialize components
        self.store = EntityStore(str(self.db_path))
        self.registry = CalculatorRegistry()
        register_builtin_calculators(self.registry)
        self.engine = CashFlowEngine(self.store)
        self.kpi_calculator = KPICalculator(self.store, self.registry)
        
        # System info
        self.cpu_count = mp.cpu_count()
        print(f"System has {self.cpu_count} CPU cores")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def create_test_dataset(self, size=1000):
        """Create test dataset for parallel benchmarks"""
        entities = []
        
        # Create diverse entity types
        for i in range(size // 4):
            # Employees
            employee = Employee(
                type='employee',
                name=f'Employee {i}',
                start_date=date(2024, 1, 1) + timedelta(days=i % 365),
                salary=50000 + (i % 100000),
                pay_frequency='monthly',
                overhead_multiplier=1.1 + (i % 20) * 0.05,
                equity_shares=1000 + (i % 50000),
                vesting_years=4,
                cliff_years=1,
                tags=[f'parallel_test', f'batch_{i // 50}', f'level_{i % 5}']
            )
            entities.append(employee)
        
        for i in range(size // 8):
            # Grants
            grant = Grant(
                type='grant',
                name=f'Grant {i}',
                start_date=date(2024, 1, 1) + timedelta(days=(i * 30) % 365),
                amount=100000 + (i % 2000000),
                grantor=f'Agency {i % 20}',
                milestones=[
                    {'name': f'Phase {j}', 'amount': 50000, 
                     'due_date': (date(2024, 1, 1) + timedelta(days=(i * 30 + j * 90))).isoformat()}
                    for j in range(1, 4)
                ],
                tags=[f'parallel_test', f'batch_{i // 20}']
            )
            entities.append(grant)
        
        for i in range(size // 8):
            # Investments
            investment = Investment(
                type='investment',
                name=f'Investment {i}',
                start_date=date(2024, 1, 1) + timedelta(days=(i * 60) % 365),
                amount=500000 + (i % 10000000),
                investor=f'Investor {i % 30}',
                disbursement_schedule=[
                    {'date': (date(2024, 1, 1) + timedelta(days=(i * 60 + j * 120))).isoformat(), 
                     'amount': 250000}
                    for j in range(1, 3)
                ],
                tags=[f'parallel_test', f'batch_{i // 15}']
            )
            entities.append(investment)
        
        for i in range(size // 8):
            # Facilities
            facility = Facility(
                type='facility',
                name=f'Facility {i}',
                start_date=date(2024, 1, 1) + timedelta(days=(i * 90) % 365),
                monthly_cost=5000 + (i % 50000),
                utilities={'electricity': 1000 + (i % 5000), 'water': 200 + (i % 1000)},
                square_footage=1000 + (i % 20000),
                tags=[f'parallel_test', f'batch_{i // 25}']
            )
            entities.append(facility)
        
        return entities
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time with high precision"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time
    
    def test_serial_vs_parallel_performance(self):
        """Compare serial vs parallel execution performance"""
        self.setUp()
        
        # Create test dataset
        entities = self.create_test_dataset(800)
        for entity in entities:
            self.store.add_entity(entity)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Test serial execution
        print("Testing serial execution...")
        serial_result, serial_time = self.measure_execution_time(
            self.engine.calculate_period,
            start_date, end_date
        )
        
        # Test parallel execution (if available)
        print("Testing parallel execution...")
        if hasattr(self.engine, 'calculate_period_parallel'):
            parallel_result, parallel_time = self.measure_execution_time(
                self.engine.calculate_period_parallel,
                start_date, end_date
            )
            
            # Verify results are equivalent
            pd.testing.assert_frame_equal(serial_result, parallel_result)
            
            # Calculate speedup
            speedup = serial_time / parallel_time
            efficiency = speedup / self.cpu_count
            
            print(f"Serial time:     {serial_time:.3f}s")
            print(f"Parallel time:   {parallel_time:.3f}s")
            print(f"Speedup:         {speedup:.2f}x")
            print(f"Efficiency:      {efficiency:.2f} ({efficiency*100:.1f}%)")
            
            # Assertions
            assert speedup > 1.0, f"Parallel execution should be faster: {speedup}x"
            assert efficiency > 0.3, f"Parallel efficiency too low: {efficiency:.2f}"
            
        else:
            print("Parallel execution not available, testing async execution...")
            
            # Test async execution
            async def async_test():
                return await self.engine.calculate_period_async(start_date, end_date)
            
            async_result, async_time = self.measure_execution_time(
                lambda: asyncio.run(async_test())
            )
            
            # Verify results are equivalent
            pd.testing.assert_frame_equal(serial_result, async_result)
            
            speedup = serial_time / async_time
            print(f"Serial time:     {serial_time:.3f}s")
            print(f"Async time:      {async_time:.3f}s")
            print(f"Speedup:         {speedup:.2f}x")
            
            # Async should be at least as fast as serial
            assert speedup >= 0.8, f"Async execution too slow: {speedup}x"
        
        self.tearDown()
    
    def test_thread_pool_scaling(self):
        """Test performance scaling with different thread pool sizes"""
        self.setUp()
        
        # Create test dataset
        entities = self.create_test_dataset(600)
        for entity in entities:
            self.store.add_entity(entity)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Test different thread pool sizes
        thread_counts = [1, 2, 4, 8, min(16, self.cpu_count * 2)]
        results = {}
        
        for thread_count in thread_counts:
            print(f"Testing with {thread_count} threads...")
            
            # Run multiple times for stability
            times = []
            for run in range(3):
                # Create thread pool-based parallel calculation
                with ThreadPoolExecutor(max_workers=thread_count) as executor:
                    # Split entities into chunks
                    entity_chunks = []
                    chunk_size = len(entities) // thread_count
                    for i in range(0, len(entities), chunk_size):
                        entity_chunks.append(entities[i:i + chunk_size])
                    
                    # Submit parallel tasks
                    start_time = time.perf_counter()
                    
                    # For this test, we'll simulate parallel entity processing
                    # In real implementation, this would be entity-level parallelization
                    futures = []
                    for chunk in entity_chunks:
                        future = executor.submit(
                            self._process_entity_chunk, chunk, start_date, end_date
                        )
                        futures.append(future)
                    
                    # Collect results
                    chunk_results = []
                    for future in as_completed(futures):
                        chunk_results.append(future.result())
                    
                    end_time = time.perf_counter()
                    times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            results[thread_count] = avg_time
            
            print(f"  Average time: {avg_time:.3f}s")
        
        # Analyze scaling characteristics
        baseline_time = results[1]  # Single thread baseline
        
        for thread_count, avg_time in results.items():
            speedup = baseline_time / avg_time
            efficiency = speedup / thread_count
            
            print(f"{thread_count} threads: {speedup:.2f}x speedup, {efficiency:.2f} efficiency")
            
            if thread_count <= self.cpu_count:
                # Should see some speedup up to CPU count
                assert speedup > thread_count * 0.3, f"Poor scaling at {thread_count} threads"
        
        self.tearDown()
    
    def _process_entity_chunk(self, entities, start_date, end_date):
        """Helper method to process a chunk of entities"""
        # Simulate entity processing workload
        total_cost = 0
        for entity in entities:
            # Simulate calculation work
            if hasattr(entity, 'salary'):
                total_cost += entity.salary * 12
            elif hasattr(entity, 'amount'):
                total_cost += entity.amount
            elif hasattr(entity, 'monthly_cost'):
                total_cost += entity.monthly_cost * 12
        
        return total_cost
    
    @pytest.mark.asyncio
    async def test_async_concurrency_performance(self):
        """Test async concurrency performance"""
        self.setUp()
        
        # Create test dataset
        entities = self.create_test_dataset(400)
        for entity in entities:
            self.store.add_entity(entity)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        results = {}
        
        for concurrency in concurrency_levels:
            print(f"Testing async concurrency level: {concurrency}")
            
            # Create multiple concurrent tasks
            async def concurrent_calculation():
                tasks = []
                for i in range(concurrency):
                    if hasattr(self.engine, 'calculate_period_async'):
                        task = self.engine.calculate_period_async(start_date, end_date)
                    else:
                        # Simulate async operation
                        task = asyncio.create_task(
                            self._async_mock_calculation(start_date, end_date)
                        )
                    tasks.append(task)
                
                start_time = time.perf_counter()
                results_list = await asyncio.gather(*tasks)
                end_time = time.perf_counter()
                
                return results_list, end_time - start_time
            
            async_results, async_time = await concurrent_calculation()
            results[concurrency] = async_time
            
            # Verify all results are consistent
            if len(async_results) > 1:
                for result in async_results[1:]:
                    if isinstance(async_results[0], pd.DataFrame) and isinstance(result, pd.DataFrame):
                        pd.testing.assert_frame_equal(async_results[0], result)
            
            print(f"  Time for {concurrency} concurrent operations: {async_time:.3f}s")
        
        # Analyze concurrency scaling
        baseline_time = results[1]
        
        for concurrency, time_taken in results.items():
            if concurrency > 1:
                # With proper async implementation, time shouldn't increase linearly
                time_ratio = time_taken / baseline_time
                print(f"Concurrency {concurrency}: {time_ratio:.2f}x baseline time")
                
                # Should not scale linearly with concurrency (async benefit)
                assert time_ratio < concurrency, f"Poor async scaling at concurrency {concurrency}"
        
        self.tearDown()
    
    async def _async_mock_calculation(self, start_date, end_date):
        """Mock async calculation for testing"""
        # Simulate async work
        await asyncio.sleep(0.1)
        
        # Return mock forecast data
        months = pd.date_range(start_date, end_date, freq='M')
        return pd.DataFrame({
            'period': months,
            'revenue': np.random.uniform(10000, 50000, len(months)),
            'expenses': np.random.uniform(20000, 40000, len(months)),
            'net_cashflow': np.random.uniform(-10000, 10000, len(months)),
            'cumulative_cash': np.cumsum(np.random.uniform(-10000, 10000, len(months)))
        })
    
    def test_process_pool_performance(self):
        """Test process pool performance for CPU-intensive tasks"""
        self.setUp()
        
        # Create test dataset
        entities = self.create_test_dataset(400)
        for entity in entities:
            self.store.add_entity(entity)
        
        # Test serial vs process pool execution
        def cpu_intensive_task(entity_data):
            """Simulate CPU-intensive calculation"""
            result = 0
            for i in range(10000):  # Computational work
                result += i * len(entity_data['name'])
            return result
        
        # Prepare entity data for serialization
        entity_data_list = []
        for entity in entities:
            entity_data_list.append({
                'name': entity.name,
                'type': entity.type,
                'value': getattr(entity, 'salary', getattr(entity, 'amount', getattr(entity, 'monthly_cost', 1000)))
            })
        
        # Serial execution
        start_time = time.perf_counter()
        serial_results = [cpu_intensive_task(data) for data in entity_data_list]
        serial_time = time.perf_counter() - start_time
        
        # Process pool execution
        process_count = min(self.cpu_count, 4)  # Limit for testing
        
        start_time = time.perf_counter()
        with ProcessPoolExecutor(max_workers=process_count) as executor:
            process_results = list(executor.map(cpu_intensive_task, entity_data_list))
        process_time = time.perf_counter() - start_time
        
        # Verify results are identical
        assert serial_results == process_results
        
        # Calculate performance metrics
        speedup = serial_time / process_time
        efficiency = speedup / process_count
        
        print(f"Serial time:       {serial_time:.3f}s")
        print(f"Process pool time: {process_time:.3f}s")
        print(f"Speedup:           {speedup:.2f}x")
        print(f"Efficiency:        {efficiency:.2f} ({efficiency*100:.1f}%)")
        
        # Process pool should provide speedup for CPU-intensive tasks
        assert speedup > 1.5, f"Process pool speedup too low: {speedup}x"
        assert efficiency > 0.4, f"Process pool efficiency too low: {efficiency:.2f}"
        
        self.tearDown()
    
    def test_memory_efficient_parallel_processing(self):
        """Test memory-efficient parallel processing of large datasets"""
        self.setUp()
        
        # Create larger dataset
        large_entities = self.create_test_dataset(2000)
        
        # Process in batches to test memory efficiency
        batch_size = 200
        batch_count = len(large_entities) // batch_size
        
        print(f"Processing {len(large_entities)} entities in {batch_count} batches")
        
        # Serial batch processing
        start_time = time.perf_counter()
        serial_results = []
        
        for i in range(0, len(large_entities), batch_size):
            batch = large_entities[i:i + batch_size]
            
            # Add batch to store
            temp_store = EntityStore(':memory:')  # In-memory for speed
            for entity in batch:
                temp_store.add_entity(entity)
            
            # Process batch
            batch_result = len(batch)  # Simplified processing
            serial_results.append(batch_result)
        
        serial_time = time.perf_counter() - start_time
        
        # Parallel batch processing
        def process_batch(batch_entities):
            temp_store = EntityStore(':memory:')
            for entity in batch_entities:
                temp_store.add_entity(entity)
            return len(batch_entities)
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            batches = [large_entities[i:i + batch_size] 
                      for i in range(0, len(large_entities), batch_size)]
            parallel_results = list(executor.map(process_batch, batches))
        
        parallel_time = time.perf_counter() - start_time
        
        # Verify results
        assert sum(serial_results) == sum(parallel_results)
        assert len(serial_results) == len(parallel_results)
        
        speedup = serial_time / parallel_time
        
        print(f"Serial batch time:   {serial_time:.3f}s")
        print(f"Parallel batch time: {parallel_time:.3f}s")
        print(f"Speedup:             {speedup:.2f}x")
        
        # Should see speedup from parallel batch processing
        assert speedup > 1.2, f"Parallel batch processing speedup too low: {speedup}x"
        
        self.tearDown()
    
    def test_load_balancing_performance(self):
        """Test load balancing in parallel execution"""
        self.setUp()
        
        # Create entities with varying computational complexity
        entities = []
        
        # Simple entities (low complexity)
        for i in range(100):
            entity = Employee(
                type='employee',
                name=f'Simple Employee {i}',
                start_date=date(2024, 1, 1),
                salary=50000,
                pay_frequency='monthly',
                overhead_multiplier=1.2,
                tags=['simple', 'low_complexity']
            )
            entities.append(entity)
        
        # Complex entities (high complexity)
        for i in range(50):
            entity = Grant(
                type='grant',
                name=f'Complex Grant {i}',
                start_date=date(2024, 1, 1),
                amount=1000000,
                grantor='Complex Agency',
                milestones=[
                    {'name': f'Phase {j}', 'amount': 100000, 
                     'due_date': (date(2024, 1, 1) + timedelta(days=j*30)).isoformat()}
                    for j in range(10)  # Many milestones = more complexity
                ],
                tags=['complex', 'high_complexity']
            )
            entities.append(entity)
        
        # Test work distribution
        def simulate_processing_time(entity):
            """Simulate processing time based on entity complexity"""
            if 'simple' in entity.tags:
                time.sleep(0.001)  # 1ms for simple entities
                return 1
            else:
                time.sleep(0.01)   # 10ms for complex entities
                return 10
        
        # Serial execution (baseline)
        start_time = time.perf_counter()
        serial_total = sum(simulate_processing_time(entity) for entity in entities)
        serial_time = time.perf_counter() - start_time
        
        # Parallel execution with load balancing
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks and let executor handle load balancing
            futures = [executor.submit(simulate_processing_time, entity) 
                      for entity in entities]
            
            parallel_total = sum(future.result() for future in as_completed(futures))
        
        parallel_time = time.perf_counter() - start_time
        
        # Verify results
        assert serial_total == parallel_total
        
        speedup = serial_time / parallel_time
        
        print(f"Serial time (mixed complexity):   {serial_time:.3f}s")
        print(f"Parallel time (load balanced):    {parallel_time:.3f}s")
        print(f"Speedup:                          {speedup:.2f}x")
        
        # Should achieve good speedup even with mixed complexity
        assert speedup > 2.0, f"Load balancing speedup too low: {speedup}x"
        
        self.tearDown()
    
    def test_parallel_kpi_calculation_performance(self):
        """Test parallel KPI calculation performance"""
        self.setUp()
        
        # Create test dataset
        entities = self.create_test_dataset(600)
        for entity in entities:
            self.store.add_entity(entity)
        
        # Generate forecast data
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        forecast_df = self.engine.calculate_period(start_date, end_date)
        
        # Test serial KPI calculation
        start_time = time.perf_counter()
        serial_kpis = self.kpi_calculator.calculate_all_kpis(forecast_df, start_date, end_date)
        serial_time = time.perf_counter() - start_time
        
        # Test parallel KPI calculation (if available)
        if hasattr(self.kpi_calculator, 'calculate_all_kpis_parallel'):
            start_time = time.perf_counter()
            parallel_kpis = self.kpi_calculator.calculate_all_kpis_parallel(
                forecast_df, start_date, end_date
            )
            parallel_time = time.perf_counter() - start_time
            
            # Verify results are equivalent
            for kpi_name in serial_kpis:
                if kpi_name in parallel_kpis:
                    serial_val = serial_kpis[kpi_name]
                    parallel_val = parallel_kpis[kpi_name]
                    
                    if isinstance(serial_val, (int, float)) and isinstance(parallel_val, (int, float)):
                        assert abs(serial_val - parallel_val) < 0.01, f"KPI mismatch: {kpi_name}"
            
            speedup = serial_time / parallel_time
            
            print(f"Serial KPI time:   {serial_time:.3f}s")
            print(f"Parallel KPI time: {parallel_time:.3f}s")
            print(f"KPI Speedup:       {speedup:.2f}x")
            
            # Should see speedup in KPI calculation
            assert speedup > 1.0, f"Parallel KPI calculation not faster: {speedup}x"
        
        else:
            print("Parallel KPI calculation not available")
            # Test manual parallel KPI calculation
            kpi_functions = [
                ('runway_months', lambda: self.kpi_calculator._calculate_runway_months(forecast_df)),
                ('burn_rate', lambda: self.kpi_calculator._calculate_burn_rate(forecast_df)),
                ('revenue_growth', lambda: self.kpi_calculator._calculate_revenue_growth_rate(forecast_df)),
                ('cash_efficiency', lambda: self.kpi_calculator._calculate_cash_conversion_efficiency(forecast_df))
            ]
            
            # Serial calculation
            start_time = time.perf_counter()
            serial_kpi_results = {}
            for kpi_name, kpi_func in kpi_functions:
                try:
                    serial_kpi_results[kpi_name] = kpi_func()
                except:
                    serial_kpi_results[kpi_name] = 0.0  # Fallback
            serial_manual_time = time.perf_counter() - start_time
            
            # Parallel calculation
            start_time = time.perf_counter()
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_kpi = {executor.submit(kpi_func): kpi_name 
                               for kpi_name, kpi_func in kpi_functions}
                
                parallel_kpi_results = {}
                for future in as_completed(future_to_kpi):
                    kpi_name = future_to_kpi[future]
                    try:
                        parallel_kpi_results[kpi_name] = future.result()
                    except:
                        parallel_kpi_results[kpi_name] = 0.0  # Fallback
            
            parallel_manual_time = time.perf_counter() - start_time
            
            speedup = serial_manual_time / parallel_manual_time
            
            print(f"Serial manual KPI time:   {serial_manual_time:.3f}s")
            print(f"Parallel manual KPI time: {parallel_manual_time:.3f}s")
            print(f"Manual KPI Speedup:       {speedup:.2f}x")
        
        self.tearDown()
    
    def test_scalability_stress_test(self):
        """Stress test parallel execution scalability"""
        self.setUp()
        
        dataset_sizes = [200, 400, 800, 1200]
        performance_data = {}
        
        for size in dataset_sizes:
            print(f"Stress testing with {size} entities...")
            
            # Create dataset
            entities = self.create_test_dataset(size)
            
            # Clear store and add entities
            self.store = EntityStore(':memory:')  # Fresh store for each test
            for entity in entities:
                self.store.add_entity(entity)
            
            start_date = date(2024, 1, 1)
            end_date = date(2024, 12, 31)
            
            # Measure performance
            start_time = time.perf_counter()
            forecast_df = self.engine.calculate_period(start_date, end_date)
            calc_time = time.perf_counter() - start_time
            
            # Measure KPI calculation
            start_time = time.perf_counter()
            kpis = self.kpi_calculator.calculate_all_kpis(forecast_df, start_date, end_date)
            kpi_time = time.perf_counter() - start_time
            
            total_time = calc_time + kpi_time
            
            performance_data[size] = {
                'calc_time': calc_time,
                'kpi_time': kpi_time,
                'total_time': total_time,
                'entities_per_second': size / total_time
            }
            
            print(f"  Calculation time: {calc_time:.3f}s")
            print(f"  KPI time:         {kpi_time:.3f}s")
            print(f"  Total time:       {total_time:.3f}s")
            print(f"  Throughput:       {size / total_time:.1f} entities/second")
            
            # Performance should not degrade exponentially
            if size > dataset_sizes[0]:
                base_size = dataset_sizes[0]
                base_time = performance_data[base_size]['total_time']
                
                size_ratio = size / base_size
                time_ratio = total_time / base_time
                
                # Time should not grow faster than O(n^1.5)
                max_expected_ratio = size_ratio ** 1.5
                
                assert time_ratio <= max_expected_ratio * 1.2, \
                    f"Performance degradation too severe: {time_ratio:.2f}x vs expected {max_expected_ratio:.2f}x"
        
        # Print performance summary
        print("\nScalability Summary:")
        print(f"{'Size':<6} {'Time':<8} {'Throughput':<12}")
        print("-" * 30)
        for size, data in performance_data.items():
            print(f"{size:<6} {data['total_time']:<8.2f} {data['entities_per_second']:<12.1f}")
        
        self.tearDown()


class TestParallelCalculationOptimizations:
    def setUp(self):
        """Set up test environment for optimization testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'optimization_test.db'
        
        # Initialize components
        self.store = EntityStore(str(self.db_path))
        self.registry = CalculatorRegistry()
        register_builtin_calculators(self.registry)
        self.engine = CashFlowEngine(self.store)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_batch_processing_optimization(self):
        """Test batch processing optimization"""
        self.setUp()
        
        # Create test entities
        entities = []
        for i in range(500):
            employee = Employee(
                type='employee',
                name=f'Batch Employee {i}',
                start_date=date(2024, 1, 1),
                salary=50000 + i * 100,
                pay_frequency='monthly',
                overhead_multiplier=1.2,
                tags=['batch_test']
            )
            entities.append(employee)
        
        for entity in entities:
            self.store.add_entity(entity)
        
        # Test different batch sizes
        batch_sizes = [50, 100, 200, 500]
        results = {}
        
        for batch_size in batch_sizes:
            print(f"Testing batch size: {batch_size}")
            
            # Simulate batch processing
            start_time = time.perf_counter()
            
            total_cost = 0
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                
                # Process batch
                batch_cost = sum(entity.salary for entity in batch)
                total_cost += batch_cost
                
                # Simulate batch overhead
                time.sleep(0.001)  # 1ms overhead per batch
            
            end_time = time.perf_counter()
            
            results[batch_size] = {
                'time': end_time - start_time,
                'batches': len(entities) // batch_size + (1 if len(entities) % batch_size else 0),
                'total_cost': total_cost
            }
            
            print(f"  Time: {results[batch_size]['time']:.3f}s")
            print(f"  Batches: {results[batch_size]['batches']}")
        
        # Find optimal batch size (fastest execution)
        optimal_batch_size = min(results.keys(), key=lambda x: results[x]['time'])
        optimal_time = results[optimal_batch_size]['time']
        
        print(f"\nOptimal batch size: {optimal_batch_size}")
        print(f"Optimal time: {optimal_time:.3f}s")
        
        # Verify all results are consistent
        expected_total = sum(entity.salary for entity in entities)
        for batch_size, result in results.items():
            assert result['total_cost'] == expected_total
        
        # Optimal batch size should be neither too small nor too large
        assert 50 <= optimal_batch_size <= 200, f"Optimal batch size unusual: {optimal_batch_size}"
        
        self.tearDown()
    
    def test_cache_locality_optimization(self):
        """Test cache locality optimization in parallel processing"""
        self.setUp()
        
        # Create entities with related data
        related_entities = []
        for group in range(10):
            for i in range(50):
                employee = Employee(
                    type='employee',
                    name=f'Group {group} Employee {i}',
                    start_date=date(2024, 1, 1),
                    salary=50000 + group * 10000 + i * 100,
                    pay_frequency='monthly',
                    overhead_multiplier=1.2 + group * 0.1,
                    tags=[f'group_{group}', 'cache_test']
                )
                related_entities.append(employee)
        
        # Test sequential access (good cache locality)
        def sequential_processing(entities):
            total = 0
            for entity in entities:
                # Simulate computation that benefits from cache locality
                total += entity.salary * entity.overhead_multiplier
            return total
        
        # Test random access (poor cache locality)
        def random_processing(entities):
            import random
            shuffled_entities = entities.copy()
            random.shuffle(shuffled_entities)
            
            total = 0
            for entity in shuffled_entities:
                total += entity.salary * entity.overhead_multiplier
            return total
        
        # Measure sequential access performance
        start_time = time.perf_counter()
        sequential_result = sequential_processing(related_entities)
        sequential_time = time.perf_counter() - start_time
        
        # Measure random access performance
        start_time = time.perf_counter()
        random_result = random_processing(related_entities)
        random_time = time.perf_counter() - start_time
        
        # Results should be the same
        assert sequential_result == random_result
        
        # Sequential should be faster due to cache locality
        cache_efficiency = random_time / sequential_time
        
        print(f"Sequential time: {sequential_time:.3f}s")
        print(f"Random time:     {random_time:.3f}s")
        print(f"Cache efficiency: {cache_efficiency:.2f}x")
        
        # Should see some benefit from cache locality
        assert cache_efficiency > 1.1, f"Cache locality benefit too small: {cache_efficiency}x"
        
        self.tearDown()
    
    def test_memory_access_pattern_optimization(self):
        """Test memory access pattern optimization"""
        self.setUp()
        
        # Create entities with different access patterns
        entities = []
        for i in range(1000):
            employee = Employee(
                type='employee',
                name=f'Memory Test Employee {i}',
                start_date=date(2024, 1, 1),
                salary=50000 + i,
                pay_frequency='monthly',
                overhead_multiplier=1.2,
                tags=['memory_test']
            )
            entities.append(employee)
        
        # Test column-wise access (accessing same field across entities)
        def column_wise_access(entities):
            # Access salaries first
            total_salary = sum(entity.salary for entity in entities)
            
            # Then access overhead multipliers
            total_overhead = sum(entity.overhead_multiplier for entity in entities)
            
            return total_salary, total_overhead
        
        # Test row-wise access (accessing all fields of one entity at a time)
        def row_wise_access(entities):
            total_salary = 0
            total_overhead = 0
            
            for entity in entities:
                total_salary += entity.salary
                total_overhead += entity.overhead_multiplier
            
            return total_salary, total_overhead
        
        # Measure column-wise access
        start_time = time.perf_counter()
        column_result = column_wise_access(entities)
        column_time = time.perf_counter() - start_time
        
        # Measure row-wise access
        start_time = time.perf_counter()
        row_result = row_wise_access(entities)
        row_time = time.perf_counter() - start_time
        
        # Results should be identical
        assert column_result == row_result
        
        print(f"Column-wise access: {column_time:.3f}s")
        print(f"Row-wise access:    {row_time:.3f}s")
        
        # Both should complete quickly
        assert column_time < 1.0, f"Column-wise access too slow: {column_time}s"
        assert row_time < 1.0, f"Row-wise access too slow: {row_time}s"
        
        self.tearDown()