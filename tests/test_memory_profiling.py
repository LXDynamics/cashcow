import pytest
import tempfile
import shutil
import time
import psutil
import os
import gc
import sys
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import threading
import weakref
from memory_profiler import profile
import tracemalloc

from cashcow.storage.database import EntityStore
from cashcow.storage.yaml_loader import YamlEntityLoader
from cashcow.engine.cashflow import CashFlowEngine
from cashcow.engine.calculators import CalculatorRegistry
from cashcow.engine.builtin_calculators import register_builtin_calculators
from cashcow.engine.kpis import KPICalculator
from cashcow.models.entities import Employee, Grant, Investment, Facility, Equipment, Software


class TestMemoryProfiler:
    def setUp(self):
        """Set up test environment for memory profiling"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'memory_test.db'
        self.entities_dir = Path(self.temp_dir) / 'entities'
        self.entities_dir.mkdir(parents=True)
        
        # Initialize components
        self.store = EntityStore(str(self.db_path))
        self.loader = YamlEntityLoader(self.entities_dir)
        self.registry = CalculatorRegistry()
        register_builtin_calculators(self.registry)
        self.engine = CashFlowEngine(self.store)
        self.kpi_calculator = KPICalculator(self.store, self.registry)
        
        # Memory tracking
        self.process = psutil.Process(os.getpid())
        self.memory_snapshots = []
        
        # Start memory tracking
        tracemalloc.start()
    
    def tearDown(self):
        # Stop memory tracking
        tracemalloc.stop()
        shutil.rmtree(self.temp_dir)
    
    def get_memory_usage(self):
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def take_memory_snapshot(self, label):
        """Take a memory snapshot with label"""
        memory_mb = self.get_memory_usage()
        current, peak = tracemalloc.get_traced_memory()
        
        snapshot = {
            'label': label,
            'timestamp': time.time(),
            'rss_mb': memory_mb,
            'traced_current_mb': current / 1024 / 1024,
            'traced_peak_mb': peak / 1024 / 1024
        }
        
        self.memory_snapshots.append(snapshot)
        print(f"Memory snapshot '{label}': {memory_mb:.2f}MB RSS, {current/1024/1024:.2f}MB traced")
        
        return snapshot
    
    def create_test_entities(self, count, entity_type='mixed'):
        """Create test entities for memory profiling"""
        entities = []
        
        if entity_type == 'mixed':
            # Mix of different entity types
            for i in range(count // 6):
                # Employees
                employee = Employee(
                    type='employee',
                    name=f'Memory Test Employee {i}',
                    start_date=date(2024, 1, 1) + timedelta(days=i % 365),
                    salary=50000 + (i % 100000),
                    pay_frequency='monthly',
                    overhead_multiplier=1.1 + (i % 20) * 0.05,
                    equity_shares=1000 + (i % 50000),
                    vesting_years=4,
                    cliff_years=1,
                    benefits={'health': 400 + i % 600, 'dental': 100 + i % 200},
                    allowances={'transport': 300 + i % 500, 'food': 200 + i % 300},
                    tags=[f'memory_test', f'batch_{i // 50}', f'level_{i % 5}']
                )
                entities.append(employee)
            
            for i in range(count // 6):
                # Grants with complex milestones
                grant = Grant(
                    type='grant',
                    name=f'Memory Test Grant {i}',
                    start_date=date(2024, 1, 1) + timedelta(days=(i * 30) % 365),
                    amount=100000 + (i % 2000000),
                    grantor=f'Agency {i % 20}',
                    milestones=[
                        {'name': f'Phase {j}', 'amount': 25000, 
                         'due_date': (date(2024, 1, 1) + timedelta(days=(i * 30 + j * 60))).isoformat(),
                         'description': f'Detailed description for phase {j} of grant {i}'}
                        for j in range(1, 5)
                    ],
                    reporting_requirements=['quarterly_report', 'financial_audit', 'technical_review'],
                    tags=[f'memory_test', f'batch_{i // 30}', f'agency_{i % 10}']
                )
                entities.append(grant)
            
            for i in range(count // 6):
                # Investments with detailed schedules
                investment = Investment(
                    type='investment',
                    name=f'Memory Test Investment {i}',
                    start_date=date(2024, 1, 1) + timedelta(days=(i * 60) % 365),
                    amount=500000 + (i % 10000000),
                    investor=f'Investor {i % 30}',
                    disbursement_schedule=[
                        {'date': (date(2024, 1, 1) + timedelta(days=(i * 60 + j * 90))).isoformat(), 
                         'amount': 100000,
                         'conditions': f'Milestone {j} completion',
                         'documentation': f'Legal docs for disbursement {j}'}
                        for j in range(1, 6)
                    ],
                    equity_percentage=0.05 + (i % 20) * 0.01,
                    valuation=5000000 + (i % 50000000),
                    board_seats=i % 3,
                    tags=[f'memory_test', f'batch_{i // 20}', f'investor_{i % 15}']
                )
                entities.append(investment)
            
            for i in range(count // 6):
                # Facilities with detailed utilities
                facility = Facility(
                    type='facility',
                    name=f'Memory Test Facility {i}',
                    start_date=date(2024, 1, 1) + timedelta(days=(i * 90) % 365),
                    monthly_cost=5000 + (i % 50000),
                    utilities={
                        'electricity': 1000 + (i % 5000),
                        'water': 200 + (i % 1000),
                        'gas': 300 + (i % 1500),
                        'internet': 100 + (i % 500),
                        'security': 500 + (i % 1000),
                        'cleaning': 300 + (i % 800)
                    },
                    square_footage=1000 + (i % 20000),
                    address=f'{100 + i} Memory Test Street, Test City, TC {10000 + i}',
                    lease_terms={'duration_months': 12 + (i % 36), 'escalation_rate': 0.03 + (i % 5) * 0.01},
                    tags=[f'memory_test', f'batch_{i // 40}', f'size_{i % 4}']
                )
                entities.append(facility)
            
            for i in range(count // 6):
                # Equipment with maintenance schedules
                equipment = Equipment(
                    type='equipment',
                    name=f'Memory Test Equipment {i}',
                    start_date=date(2024, 1, 1) + timedelta(days=(i * 45) % 365),
                    purchase_price=50000 + (i % 500000),
                    useful_life_years=5 + (i % 10),
                    maintenance_percentage=0.03 + (i % 10) * 0.01,
                    maintenance_schedule={
                        'daily': ['visual_inspection', 'operational_check'],
                        'weekly': ['detailed_inspection', 'calibration_check'],
                        'monthly': ['preventive_maintenance', 'performance_test'],
                        'annual': ['major_overhaul', 'certification_renewal']
                    },
                    vendor=f'Equipment Vendor {i % 25}',
                    model=f'Model-{i % 100}',
                    serial_number=f'SN{i:06d}',
                    tags=[f'memory_test', f'batch_{i // 35}', f'category_{i % 6}']
                )
                entities.append(equipment)
            
            for i in range(count // 6):
                # Software with user details
                software = Software(
                    type='software',
                    name=f'Memory Test Software {i}',
                    start_date=date(2024, 1, 1) + timedelta(days=(i * 15) % 365),
                    purchase_price=10000 + (i % 100000),
                    useful_life_years=3 + (i % 5),
                    maintenance_percentage=0.15 + (i % 5) * 0.05,
                    users=5 + (i % 100),
                    license_details={
                        'type': 'perpetual' if i % 2 else 'subscription',
                        'concurrent_users': 5 + (i % 100),
                        'features': [f'feature_{j}' for j in range(i % 10)],
                        'support_level': ['basic', 'standard', 'premium'][i % 3]
                    },
                    vendor=f'Software Vendor {i % 30}',
                    version=f'{(i % 10) + 1}.{(i % 5)}.{i % 10}',
                    tags=[f'memory_test', f'batch_{i // 45}', f'category_{i % 7}']
                )
                entities.append(software)
        
        elif entity_type == 'employee':
            for i in range(count):
                employee = Employee(
                    type='employee',
                    name=f'Memory Employee {i}',
                    start_date=date(2024, 1, 1),
                    salary=50000 + i * 100,
                    pay_frequency='monthly',
                    overhead_multiplier=1.2,
                    tags=['memory_test', 'employee_only']
                )
                entities.append(employee)
        
        return entities
    
    def test_entity_creation_memory_usage(self):
        """Test memory usage during entity creation"""
        self.setUp()
        
        # Take baseline snapshot
        self.take_memory_snapshot('baseline')
        
        # Create entities in batches and measure memory growth
        batch_sizes = [100, 200, 500, 1000]
        
        for batch_size in batch_sizes:
            print(f"\nCreating {batch_size} entities...")
            
            # Force garbage collection before creating entities
            gc.collect()
            
            # Create entities
            entities = self.create_test_entities(batch_size, 'mixed')
            
            # Take snapshot after creation
            self.take_memory_snapshot(f'after_creating_{batch_size}_entities')
            
            # Calculate memory per entity
            if len(self.memory_snapshots) >= 2:
                current_memory = self.memory_snapshots[-1]['rss_mb']
                previous_memory = self.memory_snapshots[-2]['rss_mb']
                memory_per_entity = (current_memory - previous_memory) / batch_size * 1024  # KB per entity
                
                print(f"Memory per entity: {memory_per_entity:.2f} KB")
                
                # Memory per entity should be reasonable (less than 10KB per entity)
                assert memory_per_entity < 10, f"Memory per entity too high: {memory_per_entity:.2f} KB"
            
            # Clear entities to test cleanup
            del entities
            gc.collect()
            
            self.take_memory_snapshot(f'after_cleanup_{batch_size}')
        
        # Analyze memory growth pattern
        print(f"\nMemory growth analysis:")
        baseline_memory = self.memory_snapshots[0]['rss_mb']
        
        for snapshot in self.memory_snapshots[1:]:
            if 'after_creating' in snapshot['label']:
                growth = snapshot['rss_mb'] - baseline_memory
                print(f"{snapshot['label']}: +{growth:.2f}MB from baseline")
        
        self.tearDown()
    
    def test_entity_storage_memory_efficiency(self):
        """Test memory efficiency of entity storage operations"""
        self.setUp()
        
        # Take baseline
        self.take_memory_snapshot('storage_baseline')
        
        # Create entities and add to store
        entities = self.create_test_entities(1000, 'mixed')
        
        self.take_memory_snapshot('entities_created')
        
        # Add entities to store one by one (simulating real usage)
        for i, entity in enumerate(entities):
            self.store.add_entity(entity)
            
            # Take periodic snapshots
            if (i + 1) % 200 == 0:
                self.take_memory_snapshot(f'stored_{i + 1}_entities')
        
        # Force database commit
        if hasattr(self.store, '_connection'):
            self.store._connection.commit()
        
        self.take_memory_snapshot('all_entities_stored')
        
        # Test querying memory usage
        all_entities = self.store.get_all_entities()
        self.take_memory_snapshot('after_query_all')
        
        # Test filtered queries
        employees = self.store.get_entities_by_type('employee')
        self.take_memory_snapshot('after_query_employees')
        
        # Test tag-based queries
        memory_test_entities = self.store.get_entities_by_tags(['memory_test'])
        self.take_memory_snapshot('after_query_by_tags')
        
        # Verify data integrity
        assert len(all_entities) == len(entities)
        assert len(employees) > 0
        assert len(memory_test_entities) == len(entities)
        
        # Analyze storage efficiency
        baseline_memory = self.memory_snapshots[0]['rss_mb']
        storage_memory = self.memory_snapshots[-4]['rss_mb']  # all_entities_stored
        
        storage_overhead = storage_memory - baseline_memory
        print(f"Storage overhead: {storage_overhead:.2f}MB for {len(entities)} entities")
        print(f"Storage efficiency: {storage_overhead / len(entities) * 1024:.2f} KB per entity")
        
        # Storage should be efficient (less than 5KB per entity overhead)
        storage_per_entity = storage_overhead / len(entities) * 1024
        assert storage_per_entity < 5, f"Storage overhead too high: {storage_per_entity:.2f} KB per entity"
        
        self.tearDown()
    
    def test_forecast_calculation_memory_profile(self):
        """Test memory usage during forecast calculations"""
        self.setUp()
        
        # Create test entities
        entities = self.create_test_entities(800, 'mixed')
        for entity in entities:
            self.store.add_entity(entity)
        
        self.take_memory_snapshot('forecast_baseline')
        
        # Test different forecast periods
        periods = [
            (date(2024, 1, 1), date(2024, 12, 31), '12_months'),
            (date(2024, 1, 1), date(2025, 12, 31), '24_months'),
            (date(2024, 1, 1), date(2026, 12, 31), '36_months')
        ]
        
        for start_date, end_date, label in periods:
            print(f"\nTesting forecast calculation: {label}")
            
            # Force garbage collection before calculation
            gc.collect()
            self.take_memory_snapshot(f'before_{label}_calculation')
            
            # Perform forecast calculation
            forecast_df = self.engine.calculate_period(start_date, end_date)
            
            self.take_memory_snapshot(f'after_{label}_calculation')
            
            # Calculate KPIs
            kpis = self.kpi_calculator.calculate_all_kpis(forecast_df, start_date, end_date)
            
            self.take_memory_snapshot(f'after_{label}_kpis')
            
            # Verify results
            expected_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
            assert len(forecast_df) == expected_months
            assert isinstance(kpis, dict)
            assert len(kpis) > 0
            
            # Clear results
            del forecast_df, kpis
            gc.collect()
            
            self.take_memory_snapshot(f'after_{label}_cleanup')
        
        # Analyze memory usage patterns
        print(f"\nForecast memory analysis:")
        baseline_memory = None
        
        for snapshot in self.memory_snapshots:
            if 'forecast_baseline' in snapshot['label']:
                baseline_memory = snapshot['rss_mb']
                break
        
        if baseline_memory:
            for snapshot in self.memory_snapshots:
                if 'after_' in snapshot['label'] and '_calculation' in snapshot['label']:
                    growth = snapshot['rss_mb'] - baseline_memory
                    print(f"{snapshot['label']}: +{growth:.2f}MB from baseline")
                    
                    # Memory growth should be reasonable
                    assert growth < 100, f"Memory growth too high for {snapshot['label']}: {growth:.2f}MB"
        
        self.tearDown()
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations"""
        self.setUp()
        
        # Create base entities
        entities = self.create_test_entities(200, 'employee')
        for entity in entities:
            self.store.add_entity(entity)
        
        # Take baseline
        self.take_memory_snapshot('leak_test_baseline')
        
        # Perform repeated operations
        num_iterations = 20
        memory_samples = []
        
        for i in range(num_iterations):
            # Force garbage collection
            gc.collect()
            
            # Perform forecast calculation
            start_date = date(2024, 1, 1)
            end_date = date(2024, 12, 31)
            
            forecast_df = self.engine.calculate_period(start_date, end_date)
            kpis = self.kpi_calculator.calculate_all_kpis(forecast_df, start_date, end_date)
            
            # Clear results
            del forecast_df, kpis
            
            # Sample memory usage
            memory_mb = self.get_memory_usage()
            memory_samples.append(memory_mb)
            
            if i % 5 == 0:
                self.take_memory_snapshot(f'iteration_{i}')
            
            # Small delay
            time.sleep(0.01)
        
        # Analyze memory trend
        initial_memory = memory_samples[0]
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        
        # Calculate trend using linear regression
        x = np.arange(len(memory_samples))
        y = np.array(memory_samples)
        slope, intercept = np.polyfit(x, y, 1)
        
        print(f"\nMemory leak analysis:")
        print(f"Initial memory: {initial_memory:.2f}MB")
        print(f"Final memory: {final_memory:.2f}MB")
        print(f"Total growth: {memory_growth:.2f}MB over {num_iterations} iterations")
        print(f"Growth trend: {slope:.4f}MB per iteration")
        
        # Check for memory leaks
        # Total growth should be minimal (less than 20MB over 20 iterations)
        assert memory_growth < 20, f"Potential memory leak: {memory_growth:.2f}MB growth"
        
        # Trend should be minimal (less than 0.5MB per iteration)
        assert abs(slope) < 0.5, f"Memory leak trend detected: {slope:.4f}MB per iteration"
        
        # Check memory stability in later iterations
        stable_samples = memory_samples[-10:]  # Last 10 samples
        memory_variance = np.var(stable_samples)
        
        print(f"Memory variance (last 10 samples): {memory_variance:.2f}")
        assert memory_variance < 4, f"Memory usage not stable: variance {memory_variance:.2f}"
        
        self.tearDown()
    
    def test_large_dataset_memory_scaling(self):
        """Test memory scaling with large datasets"""
        self.setUp()
        
        # Test memory usage with increasing dataset sizes
        dataset_sizes = [500, 1000, 2000, 3000]
        memory_results = {}
        
        for size in dataset_sizes:
            print(f"\nTesting memory scaling with {size} entities...")
            
            # Clear previous data
            if hasattr(self, 'store'):
                del self.store
            
            # Create fresh store
            self.store = EntityStore(':memory:')  # Use in-memory for speed
            
            # Force garbage collection
            gc.collect()
            baseline_memory = self.get_memory_usage()
            
            # Create and add entities
            entities = self.create_test_entities(size, 'mixed')
            
            creation_memory = self.get_memory_usage()
            
            for entity in entities:
                self.store.add_entity(entity)
            
            storage_memory = self.get_memory_usage()
            
            # Perform calculation
            start_date = date(2024, 1, 1)
            end_date = date(2024, 12, 31)
            forecast_df = self.engine.calculate_period(start_date, end_date)
            
            calculation_memory = self.get_memory_usage()
            
            # Record results
            memory_results[size] = {
                'baseline': baseline_memory,
                'after_creation': creation_memory,
                'after_storage': storage_memory,
                'after_calculation': calculation_memory,
                'creation_overhead': creation_memory - baseline_memory,
                'storage_overhead': storage_memory - creation_memory,
                'calculation_overhead': calculation_memory - storage_memory,
                'total_overhead': calculation_memory - baseline_memory
            }
            
            print(f"  Creation overhead: {memory_results[size]['creation_overhead']:.2f}MB")
            print(f"  Storage overhead: {memory_results[size]['storage_overhead']:.2f}MB")
            print(f"  Calculation overhead: {memory_results[size]['calculation_overhead']:.2f}MB")
            print(f"  Total overhead: {memory_results[size]['total_overhead']:.2f}MB")
            print(f"  Memory per entity: {memory_results[size]['total_overhead'] / size * 1024:.2f}KB")
            
            # Clean up
            del entities, forecast_df
            gc.collect()
        
        # Analyze scaling characteristics
        print(f"\nMemory scaling analysis:")
        print(f"{'Size':<6} {'Total MB':<10} {'MB/Entity':<12} {'Scaling':<10}")
        print("-" * 45)
        
        base_size = dataset_sizes[0]
        base_memory = memory_results[base_size]['total_overhead']
        
        for size in dataset_sizes:
            total_memory = memory_results[size]['total_overhead']
            memory_per_entity = total_memory / size
            
            if size == base_size:
                scaling_factor = 1.0
            else:
                expected_memory = (size / base_size) * base_memory
                scaling_factor = total_memory / expected_memory
            
            print(f"{size:<6} {total_memory:<10.2f} {memory_per_entity * 1024:<12.2f} {scaling_factor:<10.2f}")
            
            # Memory per entity should be consistent (within 50% variance)
            if size > base_size:
                base_per_entity = base_memory / base_size
                variance = abs(memory_per_entity - base_per_entity) / base_per_entity
                assert variance < 0.5, f"Memory scaling variance too high: {variance:.2f}"
            
            # Scaling should be roughly linear (within 1.5x of expected)
            if size > base_size:
                assert scaling_factor < 1.5, f"Memory scaling too poor: {scaling_factor:.2f}x"
        
        self.tearDown()
    
    def test_concurrent_memory_usage(self):
        """Test memory usage under concurrent access"""
        self.setUp()
        
        # Create test entities
        entities = self.create_test_entities(300, 'mixed')
        for entity in entities:
            self.store.add_entity(entity)
        
        self.take_memory_snapshot('concurrent_baseline')
        
        # Test concurrent operations
        def worker_function(worker_id):
            """Worker function for concurrent testing"""
            try:
                start_date = date(2024, 1, 1)
                end_date = date(2024, 12, 31)
                
                # Perform calculations
                forecast_df = self.engine.calculate_period(start_date, end_date)
                kpis = self.kpi_calculator.calculate_all_kpis(forecast_df, start_date, end_date)
                
                # Simulate some processing time
                time.sleep(0.1)
                
                return len(forecast_df), len(kpis)
                
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                return None, None
        
        # Test different concurrency levels
        concurrency_levels = [1, 2, 4, 8]
        
        for concurrency in concurrency_levels:
            print(f"\nTesting concurrent memory usage: {concurrency} threads")
            
            # Take snapshot before concurrent operations
            gc.collect()
            before_memory = self.get_memory_usage()
            
            # Start concurrent workers
            threads = []
            results = []
            
            def worker_wrapper(worker_id):
                result = worker_function(worker_id)
                results.append(result)
            
            # Start threads
            start_time = time.time()
            for i in range(concurrency):
                thread = threading.Thread(target=worker_wrapper, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            
            # Measure memory after concurrent operations
            after_memory = self.get_memory_usage()
            memory_increase = after_memory - before_memory
            
            print(f"  Time: {end_time - start_time:.2f}s")
            print(f"  Memory increase: {memory_increase:.2f}MB")
            print(f"  Memory per thread: {memory_increase / concurrency:.2f}MB")
            
            # Verify all workers completed successfully
            successful_results = [r for r in results if r[0] is not None]
            assert len(successful_results) == concurrency
            
            # Memory increase should be reasonable
            memory_per_thread = memory_increase / concurrency
            assert memory_per_thread < 10, f"Memory per thread too high: {memory_per_thread:.2f}MB"
            
            # Clear results
            results.clear()
            gc.collect()
        
        self.tearDown()
    
    def test_garbage_collection_effectiveness(self):
        """Test garbage collection effectiveness"""
        self.setUp()
        
        # Test object creation and cleanup cycles
        self.take_memory_snapshot('gc_test_baseline')
        
        # Create many objects in cycles
        num_cycles = 10
        objects_per_cycle = 100
        
        for cycle in range(num_cycles):
            print(f"Cycle {cycle + 1}/{num_cycles}")
            
            # Create objects
            entities = self.create_test_entities(objects_per_cycle, 'employee')
            
            # Add to store
            for entity in entities:
                self.store.add_entity(entity)
            
            # Create some complex data structures
            forecast_data = []
            for i in range(50):
                df = pd.DataFrame({
                    'period': pd.date_range('2024-01-01', periods=12, freq='M'),
                    'revenue': np.random.uniform(1000, 5000, 12),
                    'expenses': np.random.uniform(2000, 4000, 12)
                })
                forecast_data.append(df)
            
            self.take_memory_snapshot(f'cycle_{cycle + 1}_created')
            
            # Clear objects explicitly
            del entities
            del forecast_data
            
            # Force garbage collection
            collected = gc.collect()
            
            self.take_memory_snapshot(f'cycle_{cycle + 1}_collected')
            
            print(f"  Garbage collected: {collected} objects")
        
        # Analyze garbage collection effectiveness
        print(f"\nGarbage collection analysis:")
        
        creation_memories = []
        collection_memories = []
        
        for snapshot in self.memory_snapshots:
            if '_created' in snapshot['label']:
                creation_memories.append(snapshot['rss_mb'])
            elif '_collected' in snapshot['label']:
                collection_memories.append(snapshot['rss_mb'])
        
        # Calculate average memory reduction from garbage collection
        memory_reductions = []
        for i in range(len(creation_memories)):
            if i < len(collection_memories):
                reduction = creation_memories[i] - collection_memories[i]
                memory_reductions.append(reduction)
                print(f"Cycle {i + 1}: {reduction:.2f}MB reduction after GC")
        
        if memory_reductions:
            avg_reduction = sum(memory_reductions) / len(memory_reductions)
            print(f"Average GC reduction: {avg_reduction:.2f}MB per cycle")
            
            # Garbage collection should be effective (average reduction > 1MB)
            assert avg_reduction > 1, f"Garbage collection not effective: {avg_reduction:.2f}MB average reduction"
        
        # Final memory should be close to baseline
        baseline_memory = self.memory_snapshots[0]['rss_mb']
        final_memory = self.memory_snapshots[-1]['rss_mb']
        final_growth = final_memory - baseline_memory
        
        print(f"Final memory growth: {final_growth:.2f}MB")
        assert final_growth < 30, f"Too much memory growth after GC cycles: {final_growth:.2f}MB"
        
        self.tearDown()
    
    def test_memory_optimization_techniques(self):
        """Test various memory optimization techniques"""
        self.setUp()
        
        # Test 1: Object pooling simulation
        print("Testing object pooling simulation...")
        
        # Without pooling - create new objects each time
        start_time = time.time()
        baseline_memory = self.get_memory_usage()
        
        objects_without_pooling = []
        for i in range(1000):
            # Create new employee each time
            employee = Employee(
                type='employee',
                name=f'No Pool Employee {i}',
                start_date=date(2024, 1, 1),
                salary=50000,
                pay_frequency='monthly',
                overhead_multiplier=1.2,
                tags=['no_pool']
            )
            objects_without_pooling.append(employee)
        
        no_pool_memory = self.get_memory_usage()
        no_pool_time = time.time() - start_time
        
        # With pooling - reuse template objects
        start_time = time.time()
        pooled_memory_start = self.get_memory_usage()
        
        # Create template
        template = {
            'type': 'employee',
            'start_date': date(2024, 1, 1),
            'salary': 50000,
            'pay_frequency': 'monthly',
            'overhead_multiplier': 1.2,
            'tags': ['pooled']
        }
        
        objects_with_pooling = []
        for i in range(1000):
            # Create from template (simulating pooling)
            employee_data = template.copy()
            employee_data['name'] = f'Pooled Employee {i}'
            employee = Employee(**employee_data)
            objects_with_pooling.append(employee)
        
        pool_memory = self.get_memory_usage()
        pool_time = time.time() - start_time
        
        print(f"Without pooling: {no_pool_memory - baseline_memory:.2f}MB, {no_pool_time:.3f}s")
        print(f"With pooling: {pool_memory - pooled_memory_start:.2f}MB, {pool_time:.3f}s")
        
        # Test 2: Lazy loading simulation
        print("\nTesting lazy loading simulation...")
        
        class LazyEntity:
            def __init__(self, entity_id):
                self.entity_id = entity_id
                self._data = None
            
            @property
            def data(self):
                if self._data is None:
                    # Simulate loading data on demand
                    self._data = {
                        'name': f'Lazy Entity {self.entity_id}',
                        'type': 'employee',
                        'salary': 50000,
                        'complex_data': list(range(100))  # Some complex data
                    }
                return self._data
        
        # Create lazy entities
        lazy_baseline = self.get_memory_usage()
        lazy_entities = [LazyEntity(i) for i in range(1000)]
        lazy_created_memory = self.get_memory_usage()
        
        # Access some data (triggering lazy loading)
        for i in range(0, 1000, 10):  # Access every 10th entity
            _ = lazy_entities[i].data
        
        lazy_accessed_memory = self.get_memory_usage()
        
        print(f"Lazy entities created: {lazy_created_memory - lazy_baseline:.2f}MB")
        print(f"After accessing 10%: {lazy_accessed_memory - lazy_created_memory:.2f}MB")
        
        # Test 3: Data structure optimization
        print("\nTesting data structure optimization...")
        
        # Using regular lists
        list_baseline = self.get_memory_usage()
        regular_data = []
        for i in range(10000):
            regular_data.append([i, f'item_{i}', i * 2.5, i % 100])
        list_memory = self.get_memory_usage()
        
        # Using numpy arrays (more memory efficient for numerical data)
        numpy_baseline = self.get_memory_usage()
        numpy_ids = np.arange(10000)
        numpy_values = np.arange(10000) * 2.5
        numpy_categories = np.arange(10000) % 100
        numpy_memory = self.get_memory_usage()
        
        print(f"Regular lists: {list_memory - list_baseline:.2f}MB")
        print(f"Numpy arrays: {numpy_memory - numpy_baseline:.2f}MB")
        
        # Numpy should be more memory efficient
        list_overhead = list_memory - list_baseline
        numpy_overhead = numpy_memory - numpy_baseline
        efficiency_ratio = list_overhead / numpy_overhead
        
        print(f"Memory efficiency ratio: {efficiency_ratio:.2f}x")
        assert efficiency_ratio > 1.5, f"Numpy not significantly more efficient: {efficiency_ratio:.2f}x"
        
        # Cleanup
        del objects_without_pooling, objects_with_pooling
        del lazy_entities, regular_data, numpy_ids, numpy_values, numpy_categories
        gc.collect()
        
        self.tearDown()
    
    def test_memory_profiler_integration(self):
        """Test integration with memory profiler tools"""
        self.setUp()
        
        # Create a function to profile
        @profile
        def memory_intensive_function():
            # Create entities
            entities = self.create_test_entities(500, 'mixed')
            
            # Add to store
            for entity in entities:
                self.store.add_entity(entity)
            
            # Perform calculations
            start_date = date(2024, 1, 1)
            end_date = date(2024, 12, 31)
            forecast_df = self.engine.calculate_period(start_date, end_date)
            kpis = self.kpi_calculator.calculate_all_kpis(forecast_df, start_date, end_date)
            
            return len(entities), len(forecast_df), len(kpis)
        
        # Test tracemalloc integration
        tracemalloc.start()
        
        # Take snapshot before
        snapshot1 = tracemalloc.take_snapshot()
        
        # Run memory-intensive function
        result = memory_intensive_function()
        
        # Take snapshot after
        snapshot2 = tracemalloc.take_snapshot()
        
        # Analyze differences
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        print(f"\nMemory profiler results:")
        print(f"Function result: {result}")
        print(f"Top memory differences:")
        
        for index, stat in enumerate(top_stats[:5]):
            print(f"  {index + 1}. {stat}")
        
        # Get current memory usage
        current, peak = tracemalloc.get_traced_memory()
        print(f"Current memory usage: {current / 1024 / 1024:.2f}MB")
        print(f"Peak memory usage: {peak / 1024 / 1024:.2f}MB")
        
        # Verify memory tracking is working
        assert current > 0, "Memory tracking not working"
        assert peak >= current, "Peak memory should be >= current memory"
        
        tracemalloc.stop()
        
        self.tearDown()
    
    def generate_memory_report(self):
        """Generate comprehensive memory usage report"""
        print("\n" + "="*60)
        print("MEMORY PROFILING REPORT")
        print("="*60)
        
        if not self.memory_snapshots:
            print("No memory snapshots available")
            return
        
        # Summary statistics
        baseline_memory = self.memory_snapshots[0]['rss_mb']
        peak_memory = max(snapshot['rss_mb'] for snapshot in self.memory_snapshots)
        final_memory = self.memory_snapshots[-1]['rss_mb']
        
        print(f"\nMemory Usage Summary:")
        print(f"  Baseline:     {baseline_memory:.2f}MB")
        print(f"  Peak:         {peak_memory:.2f}MB")
        print(f"  Final:        {final_memory:.2f}MB")
        print(f"  Peak Growth:  {peak_memory - baseline_memory:.2f}MB")
        print(f"  Net Growth:   {final_memory - baseline_memory:.2f}MB")
        
        # Detailed snapshots
        print(f"\nDetailed Memory Snapshots:")
        print(f"{'Timestamp':<12} {'Label':<30} {'RSS MB':<10} {'Growth':<10}")
        print("-" * 65)
        
        for snapshot in self.memory_snapshots:
            growth = snapshot['rss_mb'] - baseline_memory
            timestamp = snapshot['timestamp'] - self.memory_snapshots[0]['timestamp']
            print(f"{timestamp:<12.1f} {snapshot['label']:<30} {snapshot['rss_mb']:<10.2f} {growth:<10.2f}")
        
        # Memory efficiency analysis
        print(f"\nMemory Efficiency Analysis:")
        
        # Find entity creation snapshots
        entity_snapshots = [s for s in self.memory_snapshots if 'entities' in s['label']]
        if len(entity_snapshots) >= 2:
            memory_per_entity = (entity_snapshots[-1]['rss_mb'] - entity_snapshots[0]['rss_mb']) * 1024 / 1000
            print(f"  Estimated memory per entity: {memory_per_entity:.2f}KB")
        
        # Find calculation snapshots
        calc_snapshots = [s for s in self.memory_snapshots if 'calculation' in s['label']]
        if calc_snapshots:
            calc_overhead = calc_snapshots[-1]['rss_mb'] - baseline_memory
            print(f"  Calculation overhead: {calc_overhead:.2f}MB")
        
        # Memory stability analysis
        if len(self.memory_snapshots) > 5:
            recent_snapshots = self.memory_snapshots[-5:]
            recent_memories = [s['rss_mb'] for s in recent_snapshots]
            memory_variance = np.var(recent_memories)
            print(f"  Memory variance (recent): {memory_variance:.2f}")
            
            if memory_variance < 1:
                print("  Memory usage: STABLE")
            elif memory_variance < 5:
                print("  Memory usage: MODERATE")
            else:
                print("  Memory usage: UNSTABLE")
        
        print("\n" + "="*60)