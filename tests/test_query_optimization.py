"""
Query optimization analysis for CashCow database.

This script analyzes query execution plans and identifies optimization opportunities.
"""

import sqlite3
import tempfile
import time
from datetime import date
from pathlib import Path
from typing import List, Dict

from cashcow.models.entities import Employee, Grant, Investment
from cashcow.storage.database import EntityStore


def analyze_query_plans(db_path: str) -> Dict:
    """Analyze SQLite query execution plans."""
    results = {}
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Test queries and their plans
        test_queries = {
            'count_all': "SELECT COUNT(*) FROM entities",
            'get_by_type': "SELECT * FROM entities WHERE type = 'employee'",
            'get_active': "SELECT * FROM entities WHERE start_date <= date('2024-06-01') AND (end_date IS NULL OR end_date >= date('2024-06-01'))",
            'get_by_name': "SELECT * FROM entities WHERE name LIKE '%Employee%'",
            'get_recent': "SELECT * FROM entities ORDER BY created_at DESC LIMIT 10",
            'complex_filter': "SELECT * FROM entities WHERE type = 'employee' AND start_date >= date('2024-01-01') AND json_extract(data, '$.salary') > 50000"
        }
        
        for query_name, sql in test_queries.items():
            try:
                # Get query plan
                cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
                plan = cursor.fetchall()
                
                # Time the query
                start_time = time.time()
                cursor.execute(sql)
                results_count = len(cursor.fetchall())
                execution_time = time.time() - start_time
                
                results[query_name] = {
                    'sql': sql,
                    'plan': plan,
                    'execution_time': execution_time,
                    'results_count': results_count
                }
                
            except Exception as e:
                results[query_name] = {
                    'sql': sql,
                    'error': str(e)
                }
    
    return results


def test_index_effectiveness(db_path: str) -> Dict:
    """Test the effectiveness of database indexes."""
    results = {}
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get index information
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        indexes = cursor.fetchall()
        
        results['indexes'] = indexes
        
        # Test queries with and without indexes
        test_cases = [
            {
                'name': 'type_filter',
                'query': "SELECT COUNT(*) FROM entities WHERE type = 'employee'",
                'expected_index': 'ix_entities_type'
            },
            {
                'name': 'date_range',
                'query': "SELECT COUNT(*) FROM entities WHERE start_date >= date('2024-01-01')",
                'expected_index': 'ix_entities_start_date'
            },
            {
                'name': 'name_search',
                'query': "SELECT COUNT(*) FROM entities WHERE name = 'Test Employee'",
                'expected_index': 'ix_entities_name'
            }
        ]
        
        for test_case in test_cases:
            query = test_case['query']
            
            # Time with indexes
            start_time = time.time()
            cursor.execute(query)
            result = cursor.fetchone()[0]
            time_with_index = time.time() - start_time
            
            # Get the query plan to verify index usage
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan_with_index = cursor.fetchall()
            
            results[test_case['name']] = {
                'query': query,
                'time_with_index': time_with_index,
                'plan_with_index': plan_with_index,
                'result_count': result,
                'uses_expected_index': any(test_case['expected_index'] in str(step) for step in plan_with_index)
            }
    
    return results


def analyze_table_statistics(db_path: str) -> Dict:
    """Analyze table statistics and data distribution."""
    results = {}
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Basic table stats
        cursor.execute("SELECT COUNT(*) FROM entities")
        total_count = cursor.fetchone()[0]
        
        # Type distribution
        cursor.execute("SELECT type, COUNT(*) FROM entities GROUP BY type ORDER BY COUNT(*) DESC")
        type_distribution = cursor.fetchall()
        
        # Date range analysis
        cursor.execute("SELECT MIN(start_date), MAX(start_date) FROM entities")
        date_range = cursor.fetchone()
        
        # Data size analysis
        cursor.execute("SELECT AVG(LENGTH(data)) as avg_data_size, MAX(LENGTH(data)) as max_data_size FROM entities")
        data_size_stats = cursor.fetchone()
        
        # Most recent entities
        cursor.execute("SELECT type, name, created_at FROM entities ORDER BY created_at DESC LIMIT 5")
        recent_entities = cursor.fetchall()
        
        results = {
            'total_entities': total_count,
            'type_distribution': type_distribution,
            'date_range': date_range,
            'avg_data_size_bytes': data_size_stats[0] if data_size_stats[0] else 0,
            'max_data_size_bytes': data_size_stats[1] if data_size_stats[1] else 0,
            'recent_entities': recent_entities
        }
    
    return results


def identify_performance_issues(db_path: str, entity_count: int) -> List[str]:
    """Identify potential performance issues."""
    issues = []
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check for missing indexes on filtered columns
        cursor.execute("PRAGMA index_list(entities)")
        indexes = cursor.fetchall()
        index_names = [idx[1] for idx in indexes]
        
        expected_indexes = ['ix_entities_type', 'ix_entities_start_date', 'ix_entities_end_date', 'ix_entities_name']
        for expected in expected_indexes:
            if expected not in index_names:
                issues.append(f"Missing index: {expected}")
        
        # Check for large JSON data
        cursor.execute("SELECT AVG(LENGTH(data)), MAX(LENGTH(data)) FROM entities")
        avg_size, max_size = cursor.fetchone()
        
        if avg_size and avg_size > 2000:
            issues.append(f"Large average JSON size: {avg_size:.0f} bytes")
        
        if max_size and max_size > 10000:
            issues.append(f"Very large JSON record: {max_size} bytes")
        
        # Check fragmentation
        cursor.execute("PRAGMA freelist_count")
        freelist = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        if page_count > 0:
            fragmentation = freelist / page_count
            if fragmentation > 0.1:
                issues.append(f"High fragmentation: {fragmentation:.2%}")
        
        # Check for lack of query optimization
        cursor.execute("SELECT COUNT(*) FROM sqlite_stat1")
        has_stats = cursor.fetchone()[0] > 0
        
        if not has_stats and entity_count > 1000:
            issues.append("Missing table statistics (run ANALYZE)")
        
        # Check table size vs entity count efficiency
        file_size = Path(db_path).stat().st_size
        if entity_count > 0:
            bytes_per_entity = file_size / entity_count
            if bytes_per_entity > 2000:
                issues.append(f"High storage overhead: {bytes_per_entity:.0f} bytes per entity")
    
    return issues


def run_query_optimization_analysis():
    """Run comprehensive query optimization analysis."""
    print("=== CashCow Database Query Optimization Analysis ===\n")
    
    # Create test database
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "optimization_test.db"
    store = EntityStore(str(db_path))
    
    try:
        # Add test data
        print("Creating test dataset...")
        entities = []
        for i in range(1000):
            if i % 3 == 0:
                entity = Employee(
                    type='employee',
                    name=f'Employee {i}',
                    start_date=date(2024, 1, 1),
                    salary=50000 + i,
                    position=f'Position {i % 10}',
                    department=f'Department {i % 5}'
                )
            elif i % 3 == 1:
                entity = Grant(
                    type='grant',
                    name=f'Grant {i}',
                    start_date=date(2024, 1, 1),
                    amount=100000 + i,
                    agency=f'Agency {i % 5}'
                )
            else:
                entity = Investment(
                    type='investment',
                    name=f'Investment {i}',
                    start_date=date(2024, 1, 1),
                    amount=500000 + i,
                    investor=f'Investor {i % 10}'
                )
            entities.append(entity)
            store.add_entity(entity)
        
        print(f"Added {len(entities)} entities to test database\n")
        
        # Analyze query plans
        print("1. Query Execution Plans")
        print("-" * 40)
        query_plans = analyze_query_plans(str(db_path))
        for query_name, info in query_plans.items():
            print(f"\n{query_name}:")
            if 'error' in info:
                print(f"  Error: {info['error']}")
            else:
                print(f"  Execution time: {info['execution_time']:.4f}s")
                print(f"  Results: {info['results_count']}")
                print(f"  Query plan:")
                for step in info['plan']:
                    print(f"    {step}")
        
        print("\n2. Index Effectiveness")
        print("-" * 40)
        index_analysis = test_index_effectiveness(str(db_path))
        print("Available indexes:")
        for name, sql in index_analysis['indexes']:
            print(f"  {name}: {sql}")
        
        print("\nIndex usage analysis:")
        for test_name, results in index_analysis.items():
            if test_name == 'indexes':
                continue
            print(f"\n{test_name}:")
            print(f"  Query: {results['query']}")
            print(f"  Execution time: {results['time_with_index']:.4f}s")
            print(f"  Uses expected index: {results['uses_expected_index']}")
            print(f"  Query plan: {results['plan_with_index']}")
        
        print("\n3. Table Statistics")
        print("-" * 40)
        stats = analyze_table_statistics(str(db_path))
        print(f"Total entities: {stats['total_entities']}")
        print(f"Type distribution: {stats['type_distribution']}")
        print(f"Date range: {stats['date_range']}")
        print(f"Average data size: {stats['avg_data_size_bytes']:.0f} bytes")
        print(f"Max data size: {stats['max_data_size_bytes']} bytes")
        
        print("\n4. Performance Issues")
        print("-" * 40)
        issues = identify_performance_issues(str(db_path), len(entities))
        if issues:
            for issue in issues:
                print(f"⚠ {issue}")
        else:
            print("✓ No performance issues detected")
        
        print("\n5. Optimization Recommendations")
        print("-" * 40)
        
        # Check if ANALYZE has been run
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_stat1")
            has_stats = cursor.fetchone()[0] > 0
        
        if not has_stats:
            print("• Run ANALYZE to update table statistics")
            
            # Run ANALYZE and test performance improvement
            print("  Running ANALYZE...")
            cursor.execute("ANALYZE")
            
            # Re-test a query
            test_query = "SELECT COUNT(*) FROM entities WHERE type = 'employee'"
            start_time = time.time()
            cursor.execute(test_query)
            result = cursor.fetchone()[0]
            after_analyze_time = time.time() - start_time
            print(f"  Query time after ANALYZE: {after_analyze_time:.4f}s")
        
        # Test VACUUM effectiveness
        file_size_before = Path(db_path).stat().st_size
        print(f"• Database file size before VACUUM: {file_size_before / 1024:.1f} KB")
        
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("VACUUM")
        
        file_size_after = Path(db_path).stat().st_size
        size_reduction = file_size_before - file_size_after
        print(f"• Database file size after VACUUM: {file_size_after / 1024:.1f} KB")
        print(f"• Space reclaimed: {size_reduction / 1024:.1f} KB ({size_reduction / file_size_before:.1%})")
        
        # Additional recommendations
        if stats['avg_data_size_bytes'] > 1500:
            print("• Consider normalizing large JSON data into separate tables")
        
        if stats['total_entities'] > 10000:
            print("• Consider implementing table partitioning for very large datasets")
        
        print("• Use prepared statements for frequently executed queries")
        print("• Consider connection pooling for high-concurrency scenarios")
        
        store.close()
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    run_query_optimization_analysis()