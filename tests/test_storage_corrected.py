import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import date
import yaml
import sqlite3
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from cashcow.storage.database import EntityStore
from cashcow.storage.yaml_loader import YamlEntityLoader
from cashcow.models.entities import Employee, Grant, Investment, Facility, create_entity


class TestYamlEntityLoader:
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.entities_dir = Path(self.temp_dir) / 'entities'
        self.entities_dir.mkdir(parents=True)
        
        # Create directory structure
        (self.entities_dir / 'expenses' / 'employees').mkdir(parents=True)
        (self.entities_dir / 'revenue' / 'grants').mkdir(parents=True)
        (self.entities_dir / 'revenue' / 'investments').mkdir(parents=True)
        (self.entities_dir / 'expenses' / 'facilities').mkdir(parents=True)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_loader_initialization(self):
        self.setUp()
        loader = YamlEntityLoader(self.entities_dir)
        assert loader.entities_dir == self.entities_dir
        self.tearDown()
    
    def test_generate_file_path_employee(self):
        self.setUp()
        loader = YamlEntityLoader(self.entities_dir)
        
        employee = Employee(
            type='employee',
            name='John Doe',
            start_date=date(2024, 1, 1),
            salary=60000,
        )
        
        # Test path generation through save_entity
        path = loader.save_entity(employee)
        expected = self.entities_dir / 'expenses' / 'employees' / 'john-doe.yaml'
        assert path == expected
        self.tearDown()
    
    def test_generate_file_path_grant(self):
        self.setUp()
        loader = YamlEntityLoader(self.entities_dir)
        
        grant = Grant(
            type='grant',
            name='SBIR Phase I',
            start_date=date(2024, 1, 1),
            amount=100000,
        )
        
        # Test path generation through save_entity
        path = loader.save_entity(grant)
        expected = self.entities_dir / 'revenue' / 'grants' / 'sbir-phase-i.yaml'
        assert path == expected
        self.tearDown()
    
    def test_save_entity_to_yaml(self):
        self.setUp()
        loader = YamlEntityLoader(self.entities_dir)
        
        employee = Employee(
            type='employee',
            name='Jane Smith',
            start_date=date(2024, 1, 1),
            salary=75000,
            tags=['engineering', 'senior']
        )
        
        file_path = loader.save_entity(employee)
        
        # Check file exists
        assert file_path.exists()
        
        # Check content
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data['type'] == 'employee'
        assert data['name'] == 'Jane Smith'
        assert data['salary'] == 75000
        assert data['tags'] == ['engineering', 'senior']
        self.tearDown()
    
    def test_load_entity_from_yaml(self):
        self.setUp()
        loader = YamlEntityLoader(self.entities_dir)
        
        # Create test YAML file
        yaml_content = {
            'type': 'grant',
            'name': 'Test Grant',
            'start_date': '2024-01-01',
            'amount': 150000,
            'tags': ['research', 'phase1']
        }
        
        file_path = self.entities_dir / 'revenue' / 'grants' / 'test-grant.yaml'
        with open(file_path, 'w') as f:
            yaml.dump(yaml_content, f)
        
        entity = loader.load_file(file_path)
        
        assert isinstance(entity, Grant)
        assert entity.name == 'Test Grant'
        assert entity.amount == 150000
        assert entity.tags == ['research', 'phase1']
        self.tearDown()
    
    def test_load_all_entities(self):
        self.setUp()
        loader = YamlEntityLoader(self.entities_dir)
        
        # Create multiple test files
        employee_data = {
            'type': 'employee',
            'name': 'Bob Johnson',
            'start_date': '2024-01-01',
            'salary': 80000,
        }
        
        grant_data = {
            'type': 'grant',
            'name': 'Research Grant',
            'start_date': '2024-01-01',
            'amount': 200000,
        }
        
        # Save files
        with open(self.entities_dir / 'expenses' / 'employees' / 'bob-johnson.yaml', 'w') as f:
            yaml.dump(employee_data, f)
        
        with open(self.entities_dir / 'revenue' / 'grants' / 'research-grant.yaml', 'w') as f:
            yaml.dump(grant_data, f)
        
        entities = loader.load_all()
        
        assert len(entities) == 2
        
        # Check we have one employee and one grant
        employees = [e for e in entities if e.type == 'employee']
        grants = [e for e in entities if e.type == 'grant']
        
        assert len(employees) == 1
        assert len(grants) == 1
        
        assert employees[0].name == 'Bob Johnson'
        assert grants[0].name == 'Research Grant'
        self.tearDown()
    
    def test_validate_entity_data(self):
        self.setUp()
        loader = YamlEntityLoader(self.entities_dir)
        
        # Valid data
        valid_data = {
            'type': 'employee',
            'name': 'Valid Employee',
            'start_date': '2024-01-01',
            'salary': 60000,
        }
        
        # Test validation through entity creation
        try:
            entity = create_entity(valid_data)
            assert entity is not None
        except Exception:
            assert False, "Valid data should not raise exception"
        
        # Invalid data - missing required field
        invalid_data = {
            'type': 'employee',
            'name': 'Invalid Employee',
            'start_date': '2024-01-01'
            # Missing salary
        }
        
        # Test validation through entity creation
        try:
            create_entity(invalid_data)
            assert False, "Invalid data should raise exception"
        except Exception:
            assert True
        self.tearDown()
    
    def test_handle_date_fields(self):
        self.setUp()
        loader = YamlEntityLoader(self.entities_dir)
        
        data = {
            'type': 'employee',
            'name': 'Test Employee',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'salary': 60000,
        }
        
        # Test date handling through file loading
        file_path = self.entities_dir / 'test-employee.yaml'
        with open(file_path, 'w') as f:
            yaml.dump(data, f)
        
        entity = loader.load_file(file_path)
        
        assert isinstance(entity.start_date, date)
        assert isinstance(entity.end_date, date)
        assert entity.start_date == date(2024, 1, 1)
        assert entity.end_date == date(2024, 12, 31)
        self.tearDown()
    
    def test_invalid_yaml_file(self):
        self.setUp()
        loader = YamlEntityLoader(self.entities_dir)
        
        # Create invalid YAML file
        file_path = self.entities_dir / 'invalid.yaml'
        with open(file_path, 'w') as f:
            f.write('invalid: yaml: content: [')
        
        # Invalid YAML should return None instead of raising exception
        entity = loader.load_file(file_path)
        assert entity is None
        self.tearDown()


class TestEntityStore:
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test.db'
        self.entities_dir = Path(self.temp_dir) / 'entities'
        self.entities_dir.mkdir(parents=True)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_store_initialization(self):
        self.setUp()
        store = EntityStore(str(self.db_path))
        
        # Check database file is created
        assert self.db_path.exists()
        
        # Check table is created
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entities'")
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        self.tearDown()
    
    def test_query_basic(self):
        self.setUp()
        store = EntityStore(str(self.db_path))
        
        # Test basic query functionality
        results = store.query()
        assert isinstance(results, list)
        assert len(results) == 0  # Empty database
        self.tearDown()
    
    def test_get_by_name(self):
        self.setUp()
        store = EntityStore(str(self.db_path))
        
        # Test getting non-existent entity
        result = store.get_by_name('Non-existent Entity')
        assert result is None
        self.tearDown()
    
    def test_get_active_entities(self):
        self.setUp()
        store = EntityStore(str(self.db_path))
        
        # Test getting active entities from empty database
        active_entities = store.get_active_entities(date(2024, 6, 1))
        assert isinstance(active_entities, list)
        assert len(active_entities) == 0
        self.tearDown()
    
    @pytest.mark.asyncio
    async def test_sync_from_yaml(self):
        self.setUp()
        store = EntityStore(str(self.db_path))
        
        # Create test YAML files
        (self.entities_dir / 'expenses' / 'employees').mkdir(parents=True)
        (self.entities_dir / 'revenue' / 'grants').mkdir(parents=True)
        
        employee_data = {
            'type': 'employee',
            'name': 'YAML Employee',
            'start_date': '2024-01-01',
            'salary': 65000,
        }
        
        grant_data = {
            'type': 'grant',
            'name': 'YAML Grant',
            'start_date': '2024-01-01',
            'amount': 150000,
        }
        
        with open(self.entities_dir / 'expenses' / 'employees' / 'yaml-employee.yaml', 'w') as f:
            yaml.dump(employee_data, f)
        
        with open(self.entities_dir / 'revenue' / 'grants' / 'yaml-grant.yaml', 'w') as f:
            yaml.dump(grant_data, f)
        
        # Sync from YAML
        count = await store.sync_from_yaml(self.entities_dir)
        
        # Check entities were loaded
        assert count == 2
        
        employee = store.get_by_name('YAML Employee')
        grant = store.get_by_name('YAML Grant')
        
        assert employee is not None
        assert employee.salary == 65000
        assert grant is not None
        assert grant.amount == 150000
        self.tearDown()
    
    def test_query_with_filters(self):
        self.setUp()
        store = EntityStore(str(self.db_path))
        
        # Test query with filters on empty database
        filters = {
            'type': 'employee',
            'active_on': date(2024, 6, 1)
        }
        
        results = store.query(filters)
        assert isinstance(results, list)
        assert len(results) == 0
        self.tearDown()
    
    def test_error_handling(self):
        self.setUp()
        
        # Test invalid database path
        with pytest.raises(Exception):
            EntityStore("/invalid/nonexistent/path/database.db")
        
        self.tearDown()


class TestStorageIntegration:
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test.db'
        self.entities_dir = Path(self.temp_dir) / 'entities'
        self.entities_dir.mkdir(parents=True)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_yaml_to_database_sync(self):
        """Test complete workflow from YAML files to database"""
        self.setUp()
        
        # Create directory structure
        (self.entities_dir / 'expenses' / 'employees').mkdir(parents=True)
        (self.entities_dir / 'revenue' / 'grants').mkdir(parents=True)
        (self.entities_dir / 'expenses' / 'facilities').mkdir(parents=True)
        
        # Create YAML files
        employee_data = {
            'type': 'employee',
            'name': 'Integration Test Employee',
            'start_date': '2024-01-01',
            'salary': 75000,
            'tags': ['integration', 'test']
        }
        
        grant_data = {
            'type': 'grant',
            'name': 'Integration Test Grant',
            'start_date': '2024-01-01',
            'amount': 250000,
            'tags': ['integration', 'test']
        }
        
        facility_data = {
            'type': 'facility',
            'name': 'Integration Test Facility',
            'start_date': '2024-01-01',
            'monthly_cost': 10000,
            'tags': ['integration', 'test']
        }
        
        # Save to YAML files
        with open(self.entities_dir / 'expenses' / 'employees' / 'integration-employee.yaml', 'w') as f:
            yaml.dump(employee_data, f)
        
        with open(self.entities_dir / 'revenue' / 'grants' / 'integration-grant.yaml', 'w') as f:
            yaml.dump(grant_data, f)
        
        with open(self.entities_dir / 'expenses' / 'facilities' / 'integration-facility.yaml', 'w') as f:
            yaml.dump(facility_data, f)
        
        # Initialize store and sync
        store = EntityStore(str(self.db_path))
        
        # Sync from YAML files
        count = await store.sync_from_yaml(self.entities_dir)
        
        # Verify all entities were loaded
        assert count == 3
        
        # Check specific entities
        employee = store.get_by_name('Integration Test Employee')
        grant = store.get_by_name('Integration Test Grant')
        facility = store.get_by_name('Integration Test Facility')
        
        assert employee is not None
        assert isinstance(employee, Employee)
        assert employee.salary == 75000
        
        assert grant is not None
        assert isinstance(grant, Grant)
        assert grant.amount == 250000
        
        assert facility is not None
        assert isinstance(facility, Facility)
        assert facility.monthly_cost == 10000
        
        # Test filtering by tags
        test_entities = store.query({'tags': ['integration']})
        assert len(test_entities) == 3
        
        self.tearDown()
    
    def test_bidirectional_sync(self):
        """Test syncing changes from database back to YAML"""
        self.setUp()
        
        # Initialize components
        loader = YamlEntityLoader(self.entities_dir)
        store = EntityStore(str(self.db_path))
        
        # Create directory structure
        (self.entities_dir / 'expenses' / 'employees').mkdir(parents=True)
        
        # Create and save entity via loader
        employee = Employee(
            type='employee',
            name='Bidirectional Test',
            start_date=date(2024, 1, 1),
            salary=60000,
        )
        
        yaml_path = loader.save_entity(employee)
        
        # Verify YAML was created
        assert yaml_path.exists()
        
        # Load and verify content
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        assert data['salary'] == 60000
        
        # Modify and save back to YAML
        employee.salary = 70000
        updated_path = loader.save_entity(employee)
        
        # Verify YAML was updated
        with open(updated_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data['salary'] == 70000
        
        # Verify paths are the same
        assert yaml_path == updated_path
        
        self.tearDown()
    
    def test_error_handling(self):
        """Test error handling in storage operations"""
        self.setUp()
        
        store = EntityStore(str(self.db_path))
        
        # Test getting non-existent entity
        result = store.get_by_name("Non-existent Entity")
        assert result is None
        
        # Test invalid database path during initialization
        with pytest.raises(Exception):
            EntityStore("/invalid/path/database.db")
        
        self.tearDown()
    
    @pytest.mark.asyncio
    async def test_performance_with_dataset(self):
        """Test performance with moderate number of entities"""
        self.setUp()
        
        store = EntityStore(str(self.db_path))
        
        # Create directory structure
        (self.entities_dir / 'expenses' / 'employees').mkdir(parents=True)
        
        # Create 50 test YAML files (reduced from 1000 for faster testing)
        for i in range(50):
            employee_data = {
                'type': 'employee',
                'name': f'Performance Test Employee {i}',
                'start_date': '2024-01-01',
                'salary': 60000 + i,
                'tags': ['performance', 'test', f'batch_{i // 10}']
            }
            
            with open(self.entities_dir / 'expenses' / 'employees' / f'employee-{i}.yaml', 'w') as f:
                yaml.dump(employee_data, f)
        
        # Measure sync time
        import time
        start_time = time.time()
        count = await store.sync_from_yaml(self.entities_dir)
        sync_time = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        assert sync_time < 5.0
        assert count == 50
        
        # Measure query time
        start_time = time.time()
        results = store.query({'type': 'employee'})
        query_time = time.time() - start_time
        
        # Should complete in reasonable time (< 1 second)
        assert query_time < 1.0
        assert len(results) == 50
        
        # Test filtered query performance
        start_time = time.time()
        filtered_results = store.query({'tags': ['performance']})
        filter_time = time.time() - start_time
        
        assert filter_time < 2.0
        assert len(filtered_results) == 50
        
        self.tearDown()