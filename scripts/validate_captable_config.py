#!/usr/bin/env python3
"""Validation script for cap table configuration and sample entities."""

import yaml
import sys
from pathlib import Path
from datetime import date

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cashcow.models.captable import create_captable_entity
from cashcow.config import get_config


def load_yaml_file(file_path: Path) -> dict:
    """Load and parse a YAML file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None


def validate_entity_file(file_path: Path) -> bool:
    """Validate a single entity file."""
    print(f"  Validating {file_path.name}...")
    
    data = load_yaml_file(file_path)
    if data is None:
        return False
    
    try:
        # Try to create the entity
        entity = create_captable_entity(data)
        print(f"    ✓ Created {entity.type}: {entity.name}")
        return True
    except Exception as e:
        print(f"    ❌ Validation failed: {e}")
        return False


def validate_config():
    """Validate the cap table configuration."""
    print("🔍 Validating cap table configuration...")
    
    try:
        config = get_config()
        
        # Check that cap table entity types are present
        required_cap_table_types = ['shareholder', 'share_class', 'funding_round']
        entity_types = config._raw_config.get('cashcow', {}).get('entity_types', {})
        
        for entity_type in required_cap_table_types:
            if entity_type in entity_types:
                print(f"  ✓ {entity_type} configuration found")
                
                # Check required fields
                required_fields = entity_types[entity_type].get('required_fields', [])
                print(f"    Required fields: {required_fields}")
                
                # Check calculators
                calculators = entity_types[entity_type].get('calculators', [])
                print(f"    Calculators: {calculators}")
                
                # Check validation rules
                validation_rules = entity_types[entity_type].get('validation_rules', [])
                if validation_rules:
                    print(f"    Validation rules: {validation_rules}")
                
            else:
                print(f"  ❌ {entity_type} configuration missing")
                return False
        
        # Check cap table KPIs
        kpis = config._raw_config.get('cashcow', {}).get('kpis', [])
        cap_table_kpis = [kpi for kpi in kpis if kpi.get('category') in ['ownership', 'governance']]
        
        print(f"  ✓ Found {len(cap_table_kpis)} cap table KPIs")
        for kpi in cap_table_kpis:
            print(f"    - {kpi['name']}: {kpi['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def validate_sample_entities():
    """Validate all sample cap table entities."""
    print("\n🔍 Validating sample cap table entities...")
    
    base_path = Path(__file__).parent.parent / "entities" / "captable"
    
    if not base_path.exists():
        print(f"❌ Cap table entities directory not found: {base_path}")
        return False
    
    total_files = 0
    valid_files = 0
    
    # Validate each subdirectory
    for subdir in ['shareholders', 'share_classes', 'funding_rounds']:
        subdir_path = base_path / subdir
        
        if not subdir_path.exists():
            print(f"❌ Subdirectory not found: {subdir}")
            continue
            
        print(f"\n📁 Validating {subdir}:")
        
        yaml_files = list(subdir_path.glob('*.yaml'))
        if not yaml_files:
            print(f"  ⚠️  No YAML files found in {subdir}")
            continue
        
        for yaml_file in yaml_files:
            total_files += 1
            if validate_entity_file(yaml_file):
                valid_files += 1
    
    print(f"\n📊 Validation Summary:")
    print(f"  Total files: {total_files}")
    print(f"  Valid files: {valid_files}")
    print(f"  Success rate: {valid_files/total_files*100:.1f}%" if total_files > 0 else "  No files found")
    
    return valid_files == total_files


def main():
    """Main validation function."""
    print("🚀 CashCow Cap Table Configuration Validator")
    print("=" * 50)
    
    # Validate configuration
    config_valid = validate_config()
    
    # Validate sample entities
    entities_valid = validate_sample_entities()
    
    # Overall result
    print("\n" + "=" * 50)
    if config_valid and entities_valid:
        print("✅ All validations passed! Cap table configuration is ready.")
        return 0
    else:
        print("❌ Some validations failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())