"""Calculator plugin system for CashCow."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Protocol

from ..models.base import BaseEntity


class Calculator(Protocol):
    """Protocol for calculator functions."""
    
    def __call__(self, entity: BaseEntity, context: Dict[str, Any]) -> float:
        """Calculate a value for the entity given the context.
        
        Args:
            entity: The entity to calculate for
            context: Calculation context (date, scenario, etc.)
            
        Returns:
            Calculated value
        """
        ...


class CalculatorRegistry:
    """Registry for calculator functions."""
    
    def __init__(self):
        """Initialize the calculator registry."""
        self._calculators: Dict[str, Dict[str, Callable]] = {}
        self._calculator_metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}
    
    def register(self, entity_type: str, calculator_name: str, 
                description: Optional[str] = None, 
                dependencies: Optional[List[str]] = None):
        """Decorator to register a calculator function.
        
        Args:
            entity_type: Type of entity this calculator works with
            calculator_name: Name of the calculator
            description: Optional description of what the calculator does
            dependencies: Optional list of other calculators this depends on
        """
        def decorator(func: Callable) -> Callable:
            # Initialize entity type if not exists
            if entity_type not in self._calculators:
                self._calculators[entity_type] = {}
                self._calculator_metadata[entity_type] = {}
            
            # Register the calculator
            self._calculators[entity_type][calculator_name] = func
            
            # Store metadata
            self._calculator_metadata[entity_type][calculator_name] = {
                'description': description or func.__doc__ or '',
                'dependencies': dependencies or [],
                'function': func.__name__,
            }
            
            return func
        
        return decorator
    
    def get_calculator(self, entity_type: str, calculator_name: str) -> Optional[Callable]:
        """Get a calculator function.
        
        Args:
            entity_type: Type of entity
            calculator_name: Name of calculator
            
        Returns:
            Calculator function or None if not found
        """
        return self._calculators.get(entity_type, {}).get(calculator_name)
    
    def get_calculators(self, entity_type: str) -> Dict[str, Callable]:
        """Get all calculators for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            Dictionary of calculator functions
        """
        return self._calculators.get(entity_type, {})
    
    def list_calculators(self, entity_type: Optional[str] = None) -> Dict[str, List[str]]:
        """List all available calculators.
        
        Args:
            entity_type: Optional entity type filter
            
        Returns:
            Dictionary mapping entity types to lists of calculator names
        """
        if entity_type:
            return {entity_type: list(self._calculators.get(entity_type, {}).keys())}
        
        return {
            et: list(calcs.keys()) 
            for et, calcs in self._calculators.items()
        }
    
    def get_calculator_metadata(self, entity_type: str, calculator_name: str) -> Dict[str, Any]:
        """Get metadata for a calculator.
        
        Args:
            entity_type: Type of entity
            calculator_name: Name of calculator
            
        Returns:
            Calculator metadata
        """
        return self._calculator_metadata.get(entity_type, {}).get(calculator_name, {})
    
    def calculate(self, entity: BaseEntity, calculator_name: str, 
                 context: Dict[str, Any]) -> Optional[float]:
        """Calculate a value using a named calculator.
        
        Args:
            entity: Entity to calculate for
            calculator_name: Name of calculator to use
            context: Calculation context
            
        Returns:
            Calculated value or None if calculator not found
        """
        calc_func = self.get_calculator(entity.type, calculator_name)
        if calc_func:
            return calc_func(entity, context)
        return None
    
    def calculate_all(self, entity: BaseEntity, context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all available values for an entity.
        
        Args:
            entity: Entity to calculate for
            context: Calculation context
            
        Returns:
            Dictionary of calculated values
        """
        results = {}
        calculators = self.get_calculators(entity.type)
        
        for calc_name, calc_func in calculators.items():
            try:
                result = calc_func(entity, context)
                if result is not None:
                    results[calc_name] = result
            except Exception as e:
                # Log error but continue with other calculators
                print(f"Error calculating {calc_name} for {entity.name}: {e}")
        
        return results
    
    def validate_dependencies(self, entity_type: str, calculator_name: str) -> List[str]:
        """Validate that all dependencies are available.
        
        Args:
            entity_type: Type of entity
            calculator_name: Name of calculator
            
        Returns:
            List of missing dependencies
        """
        metadata = self.get_calculator_metadata(entity_type, calculator_name)
        dependencies = metadata.get('dependencies', [])
        
        missing = []
        available_calculators = self.get_calculators(entity_type)
        
        for dep in dependencies:
            if dep not in available_calculators:
                missing.append(dep)
        
        return missing


class CalculationContext:
    """Context for calculations."""
    
    def __init__(self, 
                 as_of_date: date,
                 scenario: str = "baseline",
                 include_projections: bool = True,
                 additional_params: Optional[Dict[str, Any]] = None):
        """Initialize calculation context.
        
        Args:
            as_of_date: Date to calculate as of
            scenario: Scenario name
            include_projections: Whether to include projected values
            additional_params: Additional parameters for calculations
        """
        self.as_of_date = as_of_date
        self.scenario = scenario
        self.include_projections = include_projections
        self.additional_params = additional_params or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for passing to calculators."""
        return {
            'as_of_date': self.as_of_date,
            'scenario': self.scenario,
            'include_projections': self.include_projections,
            **self.additional_params
        }


class CalculatorMixin:
    """Mixin class to add calculator functionality to entities."""
    
    @classmethod
    def get_registry(cls) -> CalculatorRegistry:
        """Get the global calculator registry."""
        return get_calculator_registry()
    
    def calculate(self, calculator_name: str, context: CalculationContext) -> Optional[float]:
        """Calculate a value using a named calculator.
        
        Args:
            calculator_name: Name of calculator
            context: Calculation context
            
        Returns:
            Calculated value or None if calculator not found
        """
        registry = self.get_registry()
        return registry.calculate(self, calculator_name, context.to_dict())
    
    def calculate_all(self, context: CalculationContext) -> Dict[str, float]:
        """Calculate all available values for this entity.
        
        Args:
            context: Calculation context
            
        Returns:
            Dictionary of calculated values
        """
        registry = self.get_registry()
        return registry.calculate_all(self, context.to_dict())


# Global calculator registry
_calculator_registry: Optional[CalculatorRegistry] = None


def get_calculator_registry() -> CalculatorRegistry:
    """Get the global calculator registry."""
    global _calculator_registry
    if _calculator_registry is None:
        _calculator_registry = CalculatorRegistry()
    return _calculator_registry


def register_calculator(entity_type: str, name: str, 
                       description: Optional[str] = None,
                       dependencies: Optional[List[str]] = None):
    """Decorator to register a calculator with the global registry.
    
    Args:
        entity_type: Type of entity this calculator works with
        name: Name of the calculator
        description: Optional description
        dependencies: Optional list of dependencies
    """
    registry = get_calculator_registry()
    return registry.register(entity_type, name, description, dependencies)