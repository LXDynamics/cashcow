"""
Database monitoring and analysis script for CashCow.

This script provides detailed monitoring and analysis of database performance,
including real-time metrics, query analysis, and optimization recommendations.
"""

import os
import sqlite3
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import tempfile
import shutil
import psutil

from cashcow.models.entities import Employee, Grant, Investment
from cashcow.storage.database import EntityStore


class DatabaseMonitor:
    """Monitor database performance and provide analytics."""
    
    def __init__(self, store: EntityStore):
        self.store = store
        self.db_path = store.db_path
        self.metrics = {
            'query_times': [],
            'insert_times': [],
            'update_times': [],
            'delete_times': [],
            'memory_usage': [],
            'db_size': [],
            'entity_counts': []
        }
    
    def get_database_info(self) -> Dict:
        """Get comprehensive database information."""
        info = {}
        
        # File system info
        if os.path.exists(self.db_path):
            stat = os.stat(self.db_path)
            info['file_size_bytes'] = stat.st_size
            info['file_size_kb'] = stat.st_size / 1024
            info['file_size_mb'] = stat.st_size / (1024 * 1024)
        
        # SQLite info
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Database schema info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                info['tables'] = [row[0] for row in cursor.fetchall()]
                
                # Entity count
                cursor.execute("SELECT COUNT(*) FROM entities")
                info['entity_count'] = cursor.fetchone()[0]
                
                # Entity types distribution
                cursor.execute("SELECT type, COUNT(*) FROM entities GROUP BY type")
                info['entity_types'] = dict(cursor.fetchall())
                
                # Database page info
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                info['page_count'] = page_count
                info['page_size'] = page_size
                info['total_pages_size'] = page_count * page_size
                
                # Index info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                info['indexes'] = [row[0] for row in cursor.fetchall()]
                
                # Vacuum info
                cursor.execute("PRAGMA freelist_count")
                info['freelist_count'] = cursor.fetchone()[0]
                
        except Exception as e:
            info['database_error'] = str(e)
        
        return info
    
    def analyze_query_performance(self, query_func, description: str, iterations: int = 100) -> Dict:
        """Analyze performance of a specific query function."""
        times = []
        memory_before = psutil.Process().memory_info().rss
        
        for i in range(iterations):
            start_time = time.time()
            try:
                result = query_func()
                execution_time = time.time() - start_time
                times.append(execution_time)
            except Exception as e:
                times.append(float('inf'))  # Mark failed queries
        
        memory_after = psutil.Process().memory_info().rss
        memory_delta = memory_after - memory_before
        
        valid_times = [t for t in times if t != float('inf')]
        
        if valid_times:
            return {
                'description': description,
                'iterations': iterations,
                'successful': len(valid_times),
                'failed': len(times) - len(valid_times),
                'avg_time': sum(valid_times) / len(valid_times),
                'min_time': min(valid_times),
                'max_time': max(valid_times),
                'median_time': sorted(valid_times)[len(valid_times) // 2],
                'memory_delta_mb': memory_delta / (1024 * 1024),
                'queries_per_second': len(valid_times) / sum(valid_times) if sum(valid_times) > 0 else 0
            }
        else:
            return {
                'description': description,
                'iterations': iterations,
                'successful': 0,
                'failed': len(times),
                'error': 'All queries failed'
            }
    
    def benchmark_operations(self, entity_count: int = 1000) -> Dict:
        """Comprehensive benchmark of database operations."""
        results = {}
        
        # Create test entities
        entities = []
        for i in range(entity_count):
            if i % 3 == 0:
                entity = Employee(
                    type='employee',
                    name=f'Employee {i}',
                    start_date=date(2024, 1, 1),
                    salary=50000 + i
                )
            elif i % 3 == 1:
                entity = Grant(
                    type='grant',
                    name=f'Grant {i}',
                    start_date=date(2024, 1, 1),
                    amount=100000 + i
                )
            else:
                entity = Investment(
                    type='investment',
                    name=f'Investment {i}',
                    start_date=date(2024, 1, 1),
                    amount=500000 + i
                )
            entities.append(entity)
        
        # Benchmark insert operations
        print(f"Benchmarking {entity_count} insert operations...")
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss
        
        for entity in entities:
            self.store.add_entity(entity)
        
        insert_time = time.time() - start_time
        memory_after = psutil.Process().memory_info().rss
        
        results['insert_benchmark'] = {
            'total_time': insert_time,
            'entities_per_second': entity_count / insert_time if insert_time > 0 else 0,
            'avg_time_per_entity': insert_time / entity_count if entity_count > 0 else 0,
            'memory_used_mb': (memory_after - memory_before) / (1024 * 1024)
        }
        
        # Benchmark query operations
        query_tests = {
            'get_all_entities': lambda: self.store.get_all_entities(),
            'get_employees': lambda: self.store.get_entities_by_type('employee'),
            'get_grants': lambda: self.store.get_entities_by_type('grant'),
            'get_active_entities': lambda: self.store.get_active_entities(date(2024, 6, 1)),
        }
        
        for test_name, query_func in query_tests.items():
            print(f"Benchmarking {test_name}...")
            results[test_name] = self.analyze_query_performance(query_func, test_name, 50)
        
        # Benchmark update operations
        print("Benchmarking update operations...")
        update_entities = entities[:100]  # Update first 100 entities
        start_time = time.time()
        
        for entity in update_entities:
            if hasattr(entity, 'salary'):
                entity.salary += 1000
            elif hasattr(entity, 'amount'):
                entity.amount += 1000
            self.store.update_entity(entity)
        
        update_time = time.time() - start_time
        results['update_benchmark'] = {
            'total_time': update_time,
            'entities_per_second': len(update_entities) / update_time if update_time > 0 else 0,
            'avg_time_per_entity': update_time / len(update_entities)
        }
        
        # Benchmark delete operations
        print("Benchmarking delete operations...")
        delete_entities = entities[-50:]  # Delete last 50 entities
        start_time = time.time()
        
        for entity in delete_entities:
            self.store.delete_entity(entity.name, entity.type)
        
        delete_time = time.time() - start_time
        results['delete_benchmark'] = {
            'total_time': delete_time,
            'entities_per_second': len(delete_entities) / delete_time if delete_time > 0 else 0,
            'avg_time_per_entity': delete_time / len(delete_entities)
        }
        
        return results
    
    def analyze_database_growth(self, increments: List[int] = [100, 500, 1000, 2000]) -> Dict:
        """Analyze how database grows with entity count."""
        growth_data = []
        
        for increment in increments:
            print(f"Adding {increment} entities...")
            
            # Record before state
            before_info = self.get_database_info()
            
            # Add entities
            entities = []
            for i in range(increment):
                entity = Employee(
                    type='employee',
                    name=f'Growth_Test_Employee_{increment}_{i}',
                    start_date=date(2024, 1, 1),
                    salary=50000 + i
                )
                entities.append(entity)
                self.store.add_entity(entity)
            
            # Record after state
            after_info = self.get_database_info()
            
            growth_data.append({
                'increment': increment,
                'before_size_kb': before_info.get('file_size_kb', 0),
                'after_size_kb': after_info.get('file_size_kb', 0),
                'size_increase_kb': after_info.get('file_size_kb', 0) - before_info.get('file_size_kb', 0),
                'before_count': before_info.get('entity_count', 0),
                'after_count': after_info.get('entity_count', 0),
                'bytes_per_entity': (after_info.get('file_size_bytes', 0) - before_info.get('file_size_bytes', 0)) / increment if increment > 0 else 0
            })
        
        return {
            'growth_data': growth_data,
            'average_bytes_per_entity': sum(d['bytes_per_entity'] for d in growth_data) / len(growth_data),
            'total_entities': sum(d['increment'] for d in growth_data),
            'total_size_increase_kb': sum(d['size_increase_kb'] for d in growth_data)
        }
    
    def check_database_health(self) -> Dict:
        """Comprehensive database health check."""
        health = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check for corruption
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                health['integrity'] = integrity_result == 'ok'
                health['integrity_message'] = integrity_result
                
                # Check foreign key constraints
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                health['foreign_key_violations'] = len(fk_violations)
                
                # Analyze database statistics
                cursor.execute("ANALYZE")
                
                # Check for unused space
                cursor.execute("PRAGMA freelist_count")
                freelist_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                health['unused_pages'] = freelist_count
                health['total_pages'] = page_count
                health['fragmentation_ratio'] = freelist_count / page_count if page_count > 0 else 0
                
                # Performance recommendations
                recommendations = []
                
                if health['fragmentation_ratio'] > 0.1:
                    recommendations.append("Consider running VACUUM to reduce fragmentation")
                
                if health['foreign_key_violations'] > 0:
                    recommendations.append("Fix foreign key constraint violations")
                
                health['recommendations'] = recommendations
                
        except Exception as e:
            health['error'] = str(e)
            health['healthy'] = False
        
        return health


def run_comprehensive_database_analysis():
    """Run a comprehensive analysis of database performance."""
    print("=== CashCow Database Stress Test and Analysis ===\n")
    
    # Create temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
    try:
        db_path = temp_dir / "stress_test.db"
        store = EntityStore(str(db_path))
        monitor = DatabaseMonitor(store)
        
        print("1. Initial Database Information")
        print("-" * 40)
        initial_info = monitor.get_database_info()
        for key, value in initial_info.items():
            print(f"{key}: {value}")
        print()
        
        print("2. Database Health Check")
        print("-" * 40)
        health = monitor.check_database_health()
        for key, value in health.items():
            print(f"{key}: {value}")
        print()
        
        print("3. Performance Benchmarks")
        print("-" * 40)
        benchmarks = monitor.benchmark_operations(500)
        for test_name, results in benchmarks.items():
            print(f"\n{test_name}:")
            for metric, value in results.items():
                if isinstance(value, float):
                    print(f"  {metric}: {value:.4f}")
                else:
                    print(f"  {metric}: {value}")
        print()
        
        print("4. Database Growth Analysis")
        print("-" * 40)
        growth_analysis = monitor.analyze_database_growth([200, 500, 1000])
        print("Growth data:")
        for data in growth_analysis['growth_data']:
            print(f"  +{data['increment']} entities: {data['size_increase_kb']:.1f} KB increase "
                  f"({data['bytes_per_entity']:.1f} bytes/entity)")
        
        print(f"\nOverall growth metrics:")
        print(f"  Average bytes per entity: {growth_analysis['average_bytes_per_entity']:.1f}")
        print(f"  Total entities added: {growth_analysis['total_entities']}")
        print(f"  Total size increase: {growth_analysis['total_size_increase_kb']:.1f} KB")
        print()
        
        print("5. Final Database Information")
        print("-" * 40)
        final_info = monitor.get_database_info()
        for key, value in final_info.items():
            print(f"{key}: {value}")
        print()
        
        print("6. Performance Summary")
        print("-" * 40)
        
        # Calculate overall performance metrics
        total_entities = final_info.get('entity_count', 0)
        final_size_mb = final_info.get('file_size_mb', 0)
        
        print(f"Total entities in database: {total_entities}")
        print(f"Final database size: {final_size_mb:.2f} MB")
        print(f"Average entity size: {(final_size_mb * 1024 * 1024) / total_entities:.1f} bytes" if total_entities > 0 else "N/A")
        
        # Performance ratings
        insert_rate = benchmarks.get('insert_benchmark', {}).get('entities_per_second', 0)
        query_rate = benchmarks.get('get_all_entities', {}).get('queries_per_second', 0)
        
        print(f"Insert performance: {insert_rate:.1f} entities/second")
        print(f"Query performance: {query_rate:.1f} queries/second")
        
        # Performance assessment
        if insert_rate > 100:
            print("✓ Insert performance: Excellent")
        elif insert_rate > 50:
            print("⚠ Insert performance: Good")
        else:
            print("✗ Insert performance: Needs improvement")
            
        if query_rate > 20:
            print("✓ Query performance: Excellent")
        elif query_rate > 10:
            print("⚠ Query performance: Good")
        else:
            print("✗ Query performance: Needs improvement")
        
        store.close()
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    run_comprehensive_database_analysis()