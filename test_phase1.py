#!/usr/bin/env python3
"""Quick test to verify Phase 1 implementation."""

import sys
from pathlib import Path
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cashcow.models import Employee, Grant, create_entity
from cashcow.config import get_config
from cashcow.storage import YamlEntityLoader

def test_models():
    """Test entity models."""
    print("Testing models...")
    
    # Test Employee
    employee = Employee(
        name="John Doe",
        start_date=date(2024, 1, 1),
        salary=120000,
        position="Engineer",
        overhead_multiplier=1.3
    )
    
    print(f"Employee: {employee.name}, Active: {employee.is_active(date.today())}")
    print(f"Monthly cost: ${employee.calculate_total_cost(date.today()):,.2f}")
    
    # Test Grant
    grant = Grant(
        name="NSF SBIR",
        start_date=date(2024, 1, 1),
        amount=1000000,
        agency="NSF"
    )
    
    print(f"Grant: {grant.name}, Amount: ${grant.amount:,.2f}")
    
    # Test factory function
    data = {
        "type": "employee",
        "name": "Jane Smith",
        "start_date": "2024-01-15",
        "salary": 150000,
        "position": "Lead Engineer"
    }
    
    entity = create_entity(data)
    print(f"Created entity: {entity.name} ({entity.type})")
    
    print("✓ Models test passed\n")

def test_config():
    """Test configuration system."""
    print("Testing configuration...")
    
    try:
        config = get_config()
        print(f"Config version: {config.config.version}")
        print(f"Database: {config.config.database}")
        
        # Test entity config
        employee_config = config.get_entity_config("employee")
        if employee_config:
            print(f"Employee required fields: {employee_config.required_fields}")
            print(f"Employee calculators: {employee_config.calculators}")
        
        # Test KPIs
        kpis = config.get_kpis()
        print(f"Available KPIs: {[kpi.name for kpi in kpis]}")
        
        print("✓ Configuration test passed\n")
        
    except Exception as e:
        print(f"⚠ Configuration test failed: {e}\n")

def test_yaml_loader():
    """Test YAML loader."""
    print("Testing YAML loader...")
    
    try:
        # Create entities directory if it doesn't exist
        entities_dir = Path("entities")
        entities_dir.mkdir(exist_ok=True)
        
        loader = YamlEntityLoader(entities_dir)
        
        # Create a test employee
        employee = Employee(
            name="Test Employee",
            start_date=date(2024, 1, 1),
            salary=100000,
            position="Test Engineer"
        )
        
        # Save it
        file_path = loader.save_entity(employee)
        print(f"Saved employee to: {file_path}")
        
        # Load it back
        loaded_employee = loader.load_file(file_path)
        if loaded_employee:
            print(f"Loaded employee: {loaded_employee.name}")
            print("✓ YAML loader test passed\n")
        else:
            print("⚠ Failed to load employee\n")
            
    except Exception as e:
        print(f"⚠ YAML loader test failed: {e}\n")

if __name__ == "__main__":
    print("=== Phase 1 Integration Test ===\n")
    
    test_models()
    test_config()
    test_yaml_loader()
    
    print("=== Phase 1 Complete! ===")
    print("\nNext steps:")
    print("1. Run 'poetry install' to install dependencies")
    print("2. Start Phase 2: Entity System")
    print("3. Create calculator plugins")
    print("4. Implement cash flow engine")