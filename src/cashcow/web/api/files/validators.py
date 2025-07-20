"""
CashCow Web API - File and entity validation.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from cashcow.models.base import BaseEntity
from pydantic import ValidationError


class FileValidator:
    """Validates file content and entity data."""
    
    def __init__(self):
        """Initialize file validator."""
        self.entity_type_schemas = self._load_entity_schemas()
    
    def _load_entity_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load entity validation schemas.
        
        Returns:
            Dictionary of entity type to schema mappings
        """
        return {
            "employee": {
                "required_fields": ["type", "name", "start_date", "salary"],
                "optional_fields": ["end_date", "position", "department", "overhead_multiplier", "tags", "notes"],
                "field_types": {
                    "type": str,
                    "name": str,
                    "start_date": (str, date),
                    "end_date": (str, date, type(None)),
                    "salary": (int, float),
                    "position": (str, type(None)),
                    "department": (str, type(None)),
                    "overhead_multiplier": (int, float),
                    "tags": list,
                    "notes": (str, type(None))
                },
                "field_constraints": {
                    "salary": {"min": 0},
                    "overhead_multiplier": {"min": 1.0, "max": 3.0}
                }
            },
            
            "grant": {
                "required_fields": ["type", "name", "start_date", "amount"],
                "optional_fields": ["end_date", "agency", "program", "grant_number", "tags", "notes"],
                "field_types": {
                    "type": str,
                    "name": str,
                    "start_date": (str, date),
                    "end_date": (str, date, type(None)),
                    "amount": (int, float),
                    "agency": (str, type(None)),
                    "program": (str, type(None)),
                    "grant_number": (str, type(None)),
                    "tags": list,
                    "notes": (str, type(None))
                },
                "field_constraints": {
                    "amount": {"min": 0}
                }
            },
            
            "investment": {
                "required_fields": ["type", "name", "start_date", "amount"],
                "optional_fields": ["end_date", "investor", "round_type", "pre_money_valuation", "tags", "notes"],
                "field_types": {
                    "type": str,
                    "name": str,
                    "start_date": (str, date),
                    "end_date": (str, date, type(None)),
                    "amount": (int, float),
                    "investor": (str, type(None)),
                    "round_type": (str, type(None)),
                    "pre_money_valuation": (int, float, type(None)),
                    "tags": list,
                    "notes": (str, type(None))
                },
                "field_constraints": {
                    "amount": {"min": 0},
                    "pre_money_valuation": {"min": 0}
                }
            },
            
            "facility": {
                "required_fields": ["type", "name", "start_date", "monthly_cost"],
                "optional_fields": ["end_date", "location", "size_sqft", "facility_type", "tags", "notes"],
                "field_types": {
                    "type": str,
                    "name": str,
                    "start_date": (str, date),
                    "end_date": (str, date, type(None)),
                    "monthly_cost": (int, float),
                    "location": (str, type(None)),
                    "size_sqft": (int, type(None)),
                    "facility_type": (str, type(None)),
                    "tags": list,
                    "notes": (str, type(None))
                },
                "field_constraints": {
                    "monthly_cost": {"min": 0},
                    "size_sqft": {"min": 0}
                }
            },
            
            "software": {
                "required_fields": ["type", "name", "start_date", "monthly_cost"],
                "optional_fields": ["end_date", "vendor", "license_count", "annual_cost", "tags", "notes"],
                "field_types": {
                    "type": str,
                    "name": str,
                    "start_date": (str, date),
                    "end_date": (str, date, type(None)),
                    "monthly_cost": (int, float),
                    "vendor": (str, type(None)),
                    "license_count": (int, type(None)),
                    "annual_cost": (int, float, type(None)),
                    "tags": list,
                    "notes": (str, type(None))
                },
                "field_constraints": {
                    "monthly_cost": {"min": 0},
                    "annual_cost": {"min": 0},
                    "license_count": {"min": 1}
                }
            },
            
            "equipment": {
                "required_fields": ["type", "name", "start_date", "cost", "purchase_date"],
                "optional_fields": ["end_date", "vendor", "category", "depreciation_years", "tags", "notes"],
                "field_types": {
                    "type": str,
                    "name": str,
                    "start_date": (str, date),
                    "end_date": (str, date, type(None)),
                    "cost": (int, float),
                    "purchase_date": (str, date),
                    "vendor": (str, type(None)),
                    "category": (str, type(None)),
                    "depreciation_years": (int, type(None)),
                    "tags": list,
                    "notes": (str, type(None))
                },
                "field_constraints": {
                    "cost": {"min": 0},
                    "depreciation_years": {"min": 1, "max": 50}
                }
            },
            
            "project": {
                "required_fields": ["type", "name", "start_date", "total_budget"],
                "optional_fields": ["end_date", "project_manager", "status", "completion_percentage", "tags", "notes"],
                "field_types": {
                    "type": str,
                    "name": str,
                    "start_date": (str, date),
                    "end_date": (str, date, type(None)),
                    "total_budget": (int, float),
                    "project_manager": (str, type(None)),
                    "status": (str, type(None)),
                    "completion_percentage": (int, float, type(None)),
                    "tags": list,
                    "notes": (str, type(None))
                },
                "field_constraints": {
                    "total_budget": {"min": 0},
                    "completion_percentage": {"min": 0, "max": 100}
                }
            }
        }
    
    def validate_entity_data(self, entity_data: Dict[str, Any]) -> List[str]:
        """Validate entity data against schema.
        
        Args:
            entity_data: Entity data dictionary
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for required type field
        if "type" not in entity_data:
            errors.append("Missing required field: type")
            return errors
        
        entity_type = entity_data["type"]
        
        # Check if entity type is supported
        if entity_type not in self.entity_type_schemas:
            errors.append(f"Unsupported entity type: {entity_type}")
            return errors
        
        schema = self.entity_type_schemas[entity_type]
        
        # Check required fields
        for required_field in schema["required_fields"]:
            if required_field not in entity_data:
                errors.append(f"Missing required field: {required_field}")
            elif entity_data[required_field] is None or entity_data[required_field] == "":
                errors.append(f"Required field '{required_field}' cannot be empty")
        
        # Validate field types and constraints
        for field_name, field_value in entity_data.items():
            if field_name in schema["field_types"]:
                field_errors = self._validate_field(
                    field_name, field_value, schema, entity_type
                )
                errors.extend(field_errors)
        
        # Custom validation rules
        custom_errors = self._validate_custom_rules(entity_data, entity_type)
        errors.extend(custom_errors)
        
        return errors
    
    def _validate_field(self, field_name: str, field_value: Any, 
                       schema: Dict[str, Any], entity_type: str) -> List[str]:
        """Validate individual field.
        
        Args:
            field_name: Field name
            field_value: Field value
            schema: Entity schema
            entity_type: Entity type
            
        Returns:
            List of validation errors for this field
        """
        errors = []
        
        # Skip validation for None values on optional fields
        if field_value is None and field_name not in schema["required_fields"]:
            return errors
        
        # Type validation
        expected_types = schema["field_types"][field_name]
        if not isinstance(expected_types, tuple):
            expected_types = (expected_types,)
        
        # Handle date string conversion
        if field_name.endswith("_date") and isinstance(field_value, str):
            try:
                field_value = self._parse_date(field_value)
            except ValueError as e:
                errors.append(f"Invalid date format for {field_name}: {str(e)}")
                return errors
        
        # Check type
        if not any(isinstance(field_value, t) for t in expected_types):
            type_names = [t.__name__ for t in expected_types if t is not type(None)]
            errors.append(f"Field '{field_name}' must be of type {' or '.join(type_names)}")
            return errors
        
        # Constraint validation
        if field_name in schema.get("field_constraints", {}):
            constraint_errors = self._validate_constraints(
                field_name, field_value, schema["field_constraints"][field_name]
            )
            errors.extend(constraint_errors)
        
        return errors
    
    def _validate_constraints(self, field_name: str, field_value: Any, 
                            constraints: Dict[str, Any]) -> List[str]:
        """Validate field constraints.
        
        Args:
            field_name: Field name
            field_value: Field value
            constraints: Constraint dictionary
            
        Returns:
            List of constraint validation errors
        """
        errors = []
        
        if "min" in constraints and isinstance(field_value, (int, float)):
            if field_value < constraints["min"]:
                errors.append(f"Field '{field_name}' must be >= {constraints['min']}")
        
        if "max" in constraints and isinstance(field_value, (int, float)):
            if field_value > constraints["max"]:
                errors.append(f"Field '{field_name}' must be <= {constraints['max']}")
        
        if "options" in constraints:
            if field_value not in constraints["options"]:
                errors.append(f"Field '{field_name}' must be one of: {constraints['options']}")
        
        if "min_length" in constraints and isinstance(field_value, str):
            if len(field_value) < constraints["min_length"]:
                errors.append(f"Field '{field_name}' must be at least {constraints['min_length']} characters")
        
        if "max_length" in constraints and isinstance(field_value, str):
            if len(field_value) > constraints["max_length"]:
                errors.append(f"Field '{field_name}' must be at most {constraints['max_length']} characters")
        
        return errors
    
    def _validate_custom_rules(self, entity_data: Dict[str, Any], entity_type: str) -> List[str]:
        """Apply custom validation rules.
        
        Args:
            entity_data: Entity data
            entity_type: Entity type
            
        Returns:
            List of custom validation errors
        """
        errors = []
        
        # Date range validation
        if "start_date" in entity_data and "end_date" in entity_data:
            start_date = entity_data["start_date"]
            end_date = entity_data["end_date"]
            
            if end_date is not None:
                # Convert strings to dates for comparison
                if isinstance(start_date, str):
                    start_date = self._parse_date(start_date)
                if isinstance(end_date, str):
                    end_date = self._parse_date(end_date)
                
                if start_date > end_date:
                    errors.append("Start date must be before end date")
        
        # Entity-specific validations
        if entity_type == "employee":
            errors.extend(self._validate_employee_specific(entity_data))
        elif entity_type == "grant":
            errors.extend(self._validate_grant_specific(entity_data))
        elif entity_type == "project":
            errors.extend(self._validate_project_specific(entity_data))
        
        return errors
    
    def _validate_employee_specific(self, entity_data: Dict[str, Any]) -> List[str]:
        """Employee-specific validation rules.
        
        Args:
            entity_data: Employee entity data
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Equity validation
        equity_fields = ["equity_shares", "equity_start_date", "equity_cliff_months", "equity_vest_years"]
        has_equity_fields = any(field in entity_data for field in equity_fields)
        
        if has_equity_fields:
            if "equity_shares" not in entity_data or entity_data["equity_shares"] <= 0:
                errors.append("Equity shares must be positive when equity fields are provided")
        
        # Bonus validation
        if "bonus_performance_max" in entity_data:
            bonus = entity_data["bonus_performance_max"]
            if isinstance(bonus, (int, float)) and (bonus < 0 or bonus > 1):
                errors.append("Performance bonus must be between 0 and 1 (as percentage)")
        
        return errors
    
    def _validate_grant_specific(self, entity_data: Dict[str, Any]) -> List[str]:
        """Grant-specific validation rules.
        
        Args:
            entity_data: Grant entity data
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Indirect cost rate validation
        if "indirect_cost_rate" in entity_data:
            rate = entity_data["indirect_cost_rate"]
            if isinstance(rate, (int, float)) and (rate < 0 or rate > 1):
                errors.append("Indirect cost rate must be between 0 and 1")
        
        return errors
    
    def _validate_project_specific(self, entity_data: Dict[str, Any]) -> List[str]:
        """Project-specific validation rules.
        
        Args:
            entity_data: Project entity data
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Status validation
        valid_statuses = ["planned", "active", "on_hold", "completed", "cancelled"]
        if "status" in entity_data:
            status = entity_data["status"]
            if status and status not in valid_statuses:
                errors.append(f"Project status must be one of: {valid_statuses}")
        
        # Priority validation
        valid_priorities = ["low", "medium", "high", "critical"]
        if "priority" in entity_data:
            priority = entity_data["priority"]
            if priority and priority not in valid_priorities:
                errors.append(f"Project priority must be one of: {valid_priorities}")
        
        return errors
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date string to date object.
        
        Args:
            date_str: Date string
            
        Returns:
            Date object
        """
        # Try different date formats
        formats = [
            "%Y-%m-%d",      # ISO format
            "%m/%d/%Y",      # US format
            "%d/%m/%Y",      # European format
            "%Y-%m-%d %H:%M:%S",  # Datetime format
            "%m/%d/%Y %H:%M:%S"   # US datetime format
        ]
        
        for date_format in formats:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                return parsed_date.date()
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_str}")
    
    def validate_file_format(self, file_content: str, file_type: str) -> List[str]:
        """Validate file format.
        
        Args:
            file_content: File content as string
            file_type: Expected file type
            
        Returns:
            List of format validation errors
        """
        errors = []
        
        if file_type.lower() == "yaml":
            errors.extend(self._validate_yaml_format(file_content))
        elif file_type.lower() == "csv":
            errors.extend(self._validate_csv_format(file_content))
        elif file_type.lower() in ["json"]:
            errors.extend(self._validate_json_format(file_content))
        
        return errors
    
    def _validate_yaml_format(self, content: str) -> List[str]:
        """Validate YAML format.
        
        Args:
            content: YAML content
            
        Returns:
            List of format errors
        """
        errors = []
        
        try:
            import yaml
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            errors.append(f"YAML parsing error: {str(e)}")
        
        return errors
    
    def _validate_csv_format(self, content: str) -> List[str]:
        """Validate CSV format.
        
        Args:
            content: CSV content
            
        Returns:
            List of format errors
        """
        errors = []
        
        try:
            import csv
            import io
            
            # Try to parse CSV
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            
            if len(rows) < 1:
                errors.append("CSV file must have at least a header row")
            elif len(rows) < 2:
                errors.append("CSV file must have at least one data row")
            else:
                # Check for consistent column count
                header_cols = len(rows[0])
                for i, row in enumerate(rows[1:], 2):
                    if len(row) != header_cols:
                        errors.append(f"Row {i} has {len(row)} columns, expected {header_cols}")
        
        except Exception as e:
            errors.append(f"CSV parsing error: {str(e)}")
        
        return errors
    
    def _validate_json_format(self, content: str) -> List[str]:
        """Validate JSON format.
        
        Args:
            content: JSON content
            
        Returns:
            List of format errors
        """
        errors = []
        
        try:
            import json
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            errors.append(f"JSON parsing error: {str(e)}")
        
        return errors
    
    def get_entity_template(self, entity_type: str) -> Dict[str, Any]:
        """Get template for entity type.
        
        Args:
            entity_type: Entity type
            
        Returns:
            Entity template with example values
        """
        if entity_type not in self.entity_type_schemas:
            return {}
        
        schema = self.entity_type_schemas[entity_type]
        template = {}
        
        # Add required fields with example values
        example_values = {
            "type": entity_type,
            "name": f"Example {entity_type.title()}",
            "start_date": "2024-01-01",
            "end_date": None,
            "salary": 100000,
            "amount": 500000,
            "monthly_cost": 5000,
            "cost": 25000,
            "purchase_date": "2024-01-01",
            "total_budget": 250000,
            "tags": [],
            "notes": ""
        }
        
        for field in schema["required_fields"]:
            template[field] = example_values.get(field, "")
        
        # Add some common optional fields
        common_optional = ["end_date", "tags", "notes"]
        for field in common_optional:
            if field in schema["optional_fields"]:
                template[field] = example_values.get(field)
        
        return template
    
    def get_supported_entity_types(self) -> List[str]:
        """Get list of supported entity types.
        
        Returns:
            List of entity type names
        """
        return list(self.entity_type_schemas.keys())
    
    def get_entity_field_info(self, entity_type: str) -> Dict[str, Any]:
        """Get field information for entity type.
        
        Args:
            entity_type: Entity type
            
        Returns:
            Dictionary with field information
        """
        if entity_type not in self.entity_type_schemas:
            return {}
        
        schema = self.entity_type_schemas[entity_type]
        
        return {
            "required_fields": schema["required_fields"],
            "optional_fields": schema["optional_fields"],
            "field_types": {k: [t.__name__ for t in (v if isinstance(v, tuple) else (v,))] 
                           for k, v in schema["field_types"].items()},
            "field_constraints": schema.get("field_constraints", {})
        }