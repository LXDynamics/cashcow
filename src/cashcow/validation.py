"""Validation framework for CashCow entities."""

from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import ValidationError

from .config import get_config
from .models import BaseEntity, create_entity


class ValidationResult:
    """Result of entity validation."""
    
    def __init__(self):
        """Initialize validation result."""
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.entity_name: Optional[str] = None
        self.entity_type: Optional[str] = None
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def __str__(self) -> str:
        """String representation of validation result."""
        lines = []
        if self.entity_name and self.entity_type:
            lines.append(f"Validation for {self.entity_type}: {self.entity_name}")
        
        if self.is_valid:
            lines.append("✓ Valid")
        else:
            lines.append("✗ Invalid")
        
        for error in self.errors:
            lines.append(f"  Error: {error}")
        
        for warning in self.warnings:
            lines.append(f"  Warning: {warning}")
        
        return "\n".join(lines)


class EntityValidator:
    """Validator for CashCow entities."""
    
    def __init__(self):
        """Initialize the validator."""
        self.config = get_config()
    
    def validate_entity(self, entity: BaseEntity) -> ValidationResult:
        """Validate a single entity.
        
        Args:
            entity: Entity to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        result.entity_name = entity.name
        result.entity_type = entity.type
        
        # Basic Pydantic validation is already done
        # Add business rule validation
        
        # Check required fields
        self._validate_required_fields(entity, result)
        
        # Check date consistency
        self._validate_dates(entity, result)
        
        # Check business rules
        self._validate_business_rules(entity, result)
        
        # Check entity-specific rules
        self._validate_entity_specific(entity, result)
        
        return result
    
    def validate_data_dict(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate entity data before creating entity object.
        
        Args:
            data: Raw entity data
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        # Check basic structure
        if not isinstance(data, dict):
            result.add_error("Entity data must be a dictionary")
            return result
        
        # Check required top-level fields
        required_fields = ['type', 'name', 'start_date']
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        if not result.is_valid:
            return result
        
        result.entity_type = data.get('type')
        result.entity_name = data.get('name')
        
        # Try to create entity to validate structure
        try:
            entity = create_entity(data)
            # If successful, run full validation
            return self.validate_entity(entity)
        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(str(x) for x in error['loc'])
                result.add_error(f"{field}: {error['msg']}")
        except Exception as e:
            result.add_error(f"Unexpected error: {str(e)}")
        
        return result
    
    def _validate_required_fields(self, entity: BaseEntity, result: ValidationResult) -> None:
        """Validate entity has required fields per configuration."""
        entity_config = self.config.get_entity_config(entity.type)
        if not entity_config:
            result.add_warning(f"No configuration found for entity type: {entity.type}")
            return
        
        for field in entity_config.required_fields:
            value = getattr(entity, field, None)
            if value is None or (isinstance(value, (str, list, dict)) and len(value) == 0):
                result.add_error(f"Required field '{field}' is missing or empty")
    
    def _validate_dates(self, entity: BaseEntity, result: ValidationResult) -> None:
        """Validate date consistency."""
        # Check start_date is not in the future (unless it's a planned entity)
        today = date.today()
        if entity.start_date > today:
            # This might be okay for planned entities
            result.add_warning(f"Start date {entity.start_date} is in the future")
        
        # Check end_date is after start_date
        if entity.end_date and entity.end_date < entity.start_date:
            result.add_error(f"End date {entity.end_date} is before start date {entity.start_date}")
        
        # Check for reasonable date ranges
        if entity.end_date:
            duration_years = (entity.end_date.year - entity.start_date.year)
            if duration_years > 10:
                result.add_warning(f"Duration of {duration_years} years seems unusually long")
    
    def _validate_business_rules(self, entity: BaseEntity, result: ValidationResult) -> None:
        """Validate general business rules."""
        # Check for reasonable monetary values
        monetary_fields = ['salary', 'amount', 'cost', 'monthly_cost', 'total_budget']
        for field in monetary_fields:
            value = getattr(entity, field, None)
            if value is not None:
                if value < 0:
                    result.add_error(f"{field} cannot be negative: {value}")
                elif value > 1_000_000_000:  # 1 billion
                    result.add_warning(f"{field} seems unusually large: ${value:,.2f}")
        
        # Check percentage fields
        percentage_fields = ['overhead_multiplier', 'completion_percentage', 'indirect_cost_rate']
        for field in percentage_fields:
            value = getattr(entity, field, None)
            if value is not None:
                if field == 'overhead_multiplier':
                    if value < 1.0 or value > 5.0:
                        result.add_warning(f"Overhead multiplier {value} is outside typical range (1.0-5.0)")
                elif field == 'completion_percentage':
                    if value < 0 or value > 100:
                        result.add_error(f"Completion percentage must be 0-100: {value}")
                elif field == 'indirect_cost_rate':
                    if value < 0 or value > 1.0:
                        result.add_error(f"Indirect cost rate must be 0-1.0: {value}")
    
    def _validate_entity_specific(self, entity: BaseEntity, result: ValidationResult) -> None:
        """Validate entity-specific business rules."""
        from .models.employee import Employee
        from .models.project import Project
        from .models.revenue import Grant, Investment
        
        if isinstance(entity, Employee):
            self._validate_employee(entity, result)
        elif isinstance(entity, Grant):
            self._validate_grant(entity, result)
        elif isinstance(entity, Investment):
            self._validate_investment(entity, result)
        elif isinstance(entity, Project):
            self._validate_project(entity, result)
    
    def _validate_employee(self, employee, result: ValidationResult) -> None:
        """Validate employee-specific rules."""
        # Check salary ranges
        if employee.salary < 30000:
            result.add_warning(f"Salary ${employee.salary:,.2f} seems low")
        elif employee.salary > 500000:
            result.add_warning(f"Salary ${employee.salary:,.2f} seems high")
        
        # Check equity vesting
        if employee.equity_eligible:
            if not employee.equity_shares:
                result.add_warning("Employee is equity eligible but no shares specified")
            
            if employee.equity_start_date and employee.equity_start_date < employee.start_date:
                result.add_error("Equity start date cannot be before employment start date")
    
    def _validate_grant(self, grant, result: ValidationResult) -> None:
        """Validate grant-specific rules."""
        # Check payment schedule consistency
        if grant.payment_schedule:
            total_scheduled = sum(p.get('amount', 0) for p in grant.payment_schedule)
            if abs(total_scheduled - grant.amount) > 1000:  # Allow for small rounding
                result.add_error(f"Payment schedule total ${total_scheduled:,.2f} doesn't match grant amount ${grant.amount:,.2f}")
        
        # Check milestones
        if grant.milestones and grant.payment_schedule:
            milestone_count = len(grant.milestones)
            payment_count = len(grant.payment_schedule)
            if milestone_count > payment_count * 2:  # More than 2 milestones per payment
                result.add_warning("Large number of milestones relative to payments")
    
    def _validate_investment(self, investment, result: ValidationResult) -> None:
        """Validate investment-specific rules."""
        # Check valuation consistency
        if investment.pre_money_valuation and investment.post_money_valuation:
            expected_post = investment.pre_money_valuation + investment.amount
            if abs(investment.post_money_valuation - expected_post) > 100000:
                result.add_warning("Post-money valuation doesn't match pre-money + investment amount")
        
        # Check share math
        if all([investment.amount, investment.post_money_valuation, investment.share_price]):
            expected_shares = investment.amount / investment.share_price
            if investment.shares_issued and abs(investment.shares_issued - expected_shares) > 1000:
                result.add_warning("Share count doesn't match amount / share price")
    
    def _validate_project(self, project, result: ValidationResult) -> None:
        """Validate project-specific rules."""
        # Check budget categories sum
        if project.budget_categories:
            total_budget_categories = sum(project.budget_categories.values())
            if abs(total_budget_categories - project.total_budget) > 1000:
                result.add_error(f"Budget categories sum ${total_budget_categories:,.2f} doesn't match total budget ${project.total_budget:,.2f}")
        
        # Check milestone budget consistency
        if project.milestones:
            milestone_budget = sum(m.get('budget', 0) for m in project.milestones if 'budget' in m)
            if milestone_budget > 0 and milestone_budget > project.total_budget * 1.1:  # 10% tolerance
                result.add_warning(f"Milestone budgets ${milestone_budget:,.2f} exceed project budget")
        
        # Check completion vs status
        if project.completion_percentage == 100 and project.status != 'completed':
            result.add_warning("Project is 100% complete but status is not 'completed'")


class ReferentialValidator:
    """Validator for referential integrity between entities."""
    
    def __init__(self, entities: List[BaseEntity]):
        """Initialize with list of entities to validate against.
        
        Args:
            entities: List of all entities for cross-validation
        """
        self.entities = entities
        self.entity_names = {e.name for e in entities}
        self.entity_by_name = {e.name: e for e in entities}
    
    def validate_references(self) -> List[ValidationResult]:
        """Validate all referential integrity.
        
        Returns:
            List of validation results with reference errors
        """
        results = []
        
        for entity in self.entities:
            result = ValidationResult()
            result.entity_name = entity.name
            result.entity_type = entity.type
            
            self._validate_entity_references(entity, result)
            
            if not result.is_valid or result.warnings:
                results.append(result)
        
        return results
    
    def _validate_entity_references(self, entity: BaseEntity, result: ValidationResult) -> None:
        """Validate references in a single entity."""
        from .models.project import Project
        
        # Check team member references
        if isinstance(entity, Project) and entity.team_members:
            for member_name in entity.team_members:
                if member_name not in self.entity_names:
                    result.add_error(f"Team member '{member_name}' not found in entities")
                else:
                    member_entity = self.entity_by_name[member_name]
                    if member_entity.type != 'employee':
                        result.add_error(f"Team member '{member_name}' is not an employee")
        
        # Check project dependencies
        if isinstance(entity, Project) and entity.dependencies:
            for dep_name in entity.dependencies:
                if dep_name not in self.entity_names:
                    result.add_warning(f"Dependency '{dep_name}' not found in entities")


def validate_entity(entity: BaseEntity) -> ValidationResult:
    """Validate a single entity.
    
    Args:
        entity: Entity to validate
        
    Returns:
        Validation result
    """
    validator = EntityValidator()
    return validator.validate_entity(entity)


def validate_entity_data(data: Dict[str, Any]) -> ValidationResult:
    """Validate entity data dictionary.
    
    Args:
        data: Entity data to validate
        
    Returns:
        Validation result
    """
    validator = EntityValidator()
    return validator.validate_data_dict(data)


def validate_entities(entities: List[BaseEntity]) -> Tuple[List[ValidationResult], List[ValidationResult]]:
    """Validate a list of entities with referential integrity.
    
    Args:
        entities: List of entities to validate
        
    Returns:
        Tuple of (individual validation results, referential validation results)
    """
    # Individual validation
    validator = EntityValidator()
    individual_results = [validator.validate_entity(entity) for entity in entities]
    
    # Referential validation
    ref_validator = ReferentialValidator(entities)
    referential_results = ref_validator.validate_references()
    
    return individual_results, referential_results