"""Scenario management for CashCow cash flow modeling."""

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import yaml

from ..models.base import BaseEntity
from ..storage.database import EntityStore
from .cashflow import CashFlowEngine


class Scenario:
    """Represents a modeling scenario with overrides and filters."""

    def __init__(self,
                 name: str,
                 description: str = "",
                 assumptions: Optional[Dict[str, Any]] = None,
                 entity_overrides: Optional[List[Dict[str, Any]]] = None,
                 entity_filters: Optional[Dict[str, Any]] = None):
        """Initialize a scenario.

        Args:
            name: Scenario name
            description: Description of the scenario
            assumptions: Global assumptions for the scenario
            entity_overrides: List of entity-specific overrides
            entity_filters: Filters for including/excluding entities
        """
        self.name = name
        self.description = description
        self.assumptions = assumptions or {}
        self.entity_overrides = entity_overrides or []
        self.entity_filters = entity_filters or {}

    def apply_to_entity(self, entity: BaseEntity) -> BaseEntity:
        """Apply scenario overrides to an entity.

        Args:
            entity: Original entity

        Returns:
            Modified entity with scenario applied
        """
        # Create a copy of the entity data
        entity_data = entity.to_dict()

        # Apply entity-specific overrides
        for override in self.entity_overrides:
            if self._matches_override_criteria(entity, override):
                self._apply_override(entity_data, override)

        # Apply global assumptions
        self._apply_global_assumptions(entity_data)

        # Create new entity with modified data
        from ..models.entities import create_entity
        return create_entity(entity_data)

    def _matches_override_criteria(self, entity: BaseEntity, override: Dict[str, Any]) -> bool:
        """Check if entity matches override criteria."""
        # Match by name
        if 'entity' in override and override['entity'] == entity.name:
            return True

        # Match by type
        if 'entity_type' in override and override['entity_type'] == entity.type:
            return True

        # Match by pattern
        if 'name_pattern' in override:
            import re
            pattern = override['name_pattern']
            if re.search(pattern, entity.name, re.IGNORECASE):
                return True

        # Match by tags
        if 'tags' in override:
            required_tags = set(override['tags'])
            entity_tags = set(entity.tags)
            if required_tags.intersection(entity_tags):
                return True

        return False

    def _apply_override(self, entity_data: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Apply a single override to entity data."""
        if 'field' in override and 'value' in override:
            # Simple field override
            entity_data[override['field']] = override['value']

        elif 'multiplier' in override and 'field' in override:
            # Multiplier override
            field = override['field']
            if field in entity_data and isinstance(entity_data[field], (int, float)):
                entity_data[field] *= override['multiplier']

        elif 'changes' in override:
            # Multiple field changes
            for field, value in override['changes'].items():
                entity_data[field] = value

    def _apply_global_assumptions(self, entity_data: Dict[str, Any]) -> None:
        """Apply global scenario assumptions to entity data."""
        entity_type = entity_data.get('type', '').lower()

        # Apply growth rates
        if 'revenue_growth_rate' in self.assumptions and entity_type in ['sale', 'service']:
            growth_rate = self.assumptions['revenue_growth_rate']
            # This would be applied in calculations, not directly to entity
            pass

        # Apply overhead multipliers
        if 'overhead_multiplier' in self.assumptions and entity_type == 'employee':
            if 'overhead_multiplier' not in entity_data:
                entity_data['overhead_multiplier'] = self.assumptions['overhead_multiplier']

        # Apply hiring rate adjustments
        if 'hiring_delay_months' in self.assumptions and entity_type == 'employee':
            from datetime import timedelta
            if 'start_date' in entity_data:
                current_start = entity_data['start_date']
                if isinstance(current_start, str):
                    current_start = date.fromisoformat(current_start)

                delay_days = self.assumptions['hiring_delay_months'] * 30
                new_start = current_start + timedelta(days=delay_days)
                entity_data['start_date'] = new_start

    def should_include_entity(self, entity: BaseEntity) -> bool:
        """Check if entity should be included in this scenario."""
        # Check include filters
        if 'include_types' in self.entity_filters:
            if entity.type not in self.entity_filters['include_types']:
                return False

        # Check exclude filters
        if 'exclude_types' in self.entity_filters:
            if entity.type in self.entity_filters['exclude_types']:
                return False

        # Check include patterns
        if 'include_patterns' in self.entity_filters:
            import re
            patterns = self.entity_filters['include_patterns']
            if not any(re.search(pattern, entity.name, re.IGNORECASE) for pattern in patterns):
                return False

        # Check exclude patterns
        if 'exclude_patterns' in self.entity_filters:
            import re
            patterns = self.entity_filters['exclude_patterns']
            if any(re.search(pattern, entity.name, re.IGNORECASE) for pattern in patterns):
                return False

        # Check tag filters
        if 'require_tags' in self.entity_filters:
            required_tags = set(self.entity_filters['require_tags'])
            entity_tags = set(entity.tags)
            if not required_tags.intersection(entity_tags):
                return False

        if 'exclude_tags' in self.entity_filters:
            excluded_tags = set(self.entity_filters['exclude_tags'])
            entity_tags = set(entity.tags)
            if excluded_tags.intersection(entity_tags):
                return False

        return True

    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> 'Scenario':
        """Load scenario from YAML file.

        Args:
            yaml_path: Path to YAML file

        Returns:
            Scenario object
        """
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        return cls(
            name=data['name'],
            description=data.get('description', ''),
            assumptions=data.get('assumptions', {}),
            entity_overrides=data.get('entity_overrides', []),
            entity_filters=data.get('entity_filters', {})
        )

    def to_yaml(self, yaml_path: Union[str, Path]) -> None:
        """Save scenario to YAML file.

        Args:
            yaml_path: Path to save YAML file
        """
        data = {
            'name': self.name,
            'description': self.description,
            'assumptions': self.assumptions,
            'entity_overrides': self.entity_overrides,
            'entity_filters': self.entity_filters,
        }

        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


class ScenarioManager:
    """Manages scenarios and applies them to cash flow calculations."""

    def __init__(self, store: EntityStore, cashflow_engine: CashFlowEngine):
        """Initialize scenario manager.

        Args:
            store: Entity store
            cashflow_engine: Cash flow calculation engine
        """
        self.store = store
        self.engine = cashflow_engine
        self.scenarios: Dict[str, Scenario] = {}

        # Load default scenarios
        self._create_default_scenarios()

    def add_scenario(self, scenario: Scenario) -> None:
        """Add a scenario to the manager.

        Args:
            scenario: Scenario to add
        """
        self.scenarios[scenario.name] = scenario

    def load_scenario(self, yaml_path: Union[str, Path]) -> None:
        """Load scenario from YAML file.

        Args:
            yaml_path: Path to YAML file
        """
        scenario = Scenario.from_yaml(yaml_path)
        self.add_scenario(scenario)

    def load_scenarios_from_directory(self, scenarios_dir: Union[str, Path]) -> None:
        """Load all scenarios from a directory.

        Args:
            scenarios_dir: Directory containing scenario YAML files
        """
        scenarios_path = Path(scenarios_dir)
        if not scenarios_path.exists():
            return

        for yaml_file in scenarios_path.glob("*.yaml"):
            try:
                self.load_scenario(yaml_file)
            except Exception as e:
                print(f"Error loading scenario {yaml_file}: {e}")

    def get_scenario(self, name: str) -> Optional[Scenario]:
        """Get scenario by name.

        Args:
            name: Scenario name

        Returns:
            Scenario or None if not found
        """
        return self.scenarios.get(name)

    def list_scenarios(self) -> List[str]:
        """List all available scenario names.

        Returns:
            List of scenario names
        """
        return list(self.scenarios.keys())

    def apply_scenario(self, scenario_name: str, entities: List[BaseEntity]) -> List[BaseEntity]:
        """Apply scenario to a list of entities.

        Args:
            scenario_name: Name of scenario to apply
            entities: List of entities to modify

        Returns:
            List of modified entities
        """
        scenario = self.get_scenario(scenario_name)
        if not scenario:
            raise ValueError(f"Scenario '{scenario_name}' not found")

        modified_entities = []

        for entity in entities:
            # Check if entity should be included
            if scenario.should_include_entity(entity):
                # Apply scenario modifications
                modified_entity = scenario.apply_to_entity(entity)
                modified_entities.append(modified_entity)

        return modified_entities

    def calculate_scenario(self,
                          scenario_name: str,
                          start_date: date,
                          end_date: date) -> pd.DataFrame:
        """Calculate cash flow for a specific scenario.

        Args:
            scenario_name: Name of scenario
            start_date: Start of calculation period
            end_date: End of calculation period

        Returns:
            DataFrame with cash flow results
        """
        # Get all entities
        entities = self.store.query()

        # Apply scenario
        scenario_entities = self.apply_scenario(scenario_name, entities)

        # Temporarily replace entities in store
        original_query = self.store.query
        self.store.query = lambda filters=None: scenario_entities

        try:
            # Calculate cash flow
            return self.engine.calculate_period(start_date, end_date, scenario_name)
        finally:
            # Restore original query method
            self.store.query = original_query

    def compare_scenarios(self,
                         scenario_names: List[str],
                         start_date: date,
                         end_date: date) -> Dict[str, pd.DataFrame]:
        """Compare multiple scenarios.

        Args:
            scenario_names: List of scenario names to compare
            start_date: Start of calculation period
            end_date: End of calculation period

        Returns:
            Dictionary mapping scenario names to their results
        """
        results = {}

        for scenario_name in scenario_names:
            results[scenario_name] = self.calculate_scenario(
                scenario_name, start_date, end_date
            )

        return results

    def _create_default_scenarios(self) -> None:
        """Create default scenarios."""
        # Baseline scenario
        baseline = Scenario(
            name="baseline",
            description="Conservative baseline scenario with current assumptions",
            assumptions={
                'revenue_growth_rate': 0.10,  # 10% annual growth
                'overhead_multiplier': 1.3,
                'hiring_delay_months': 0,
            }
        )
        self.add_scenario(baseline)

        # Optimistic scenario
        optimistic = Scenario(
            name="optimistic",
            description="Optimistic growth scenario",
            assumptions={
                'revenue_growth_rate': 0.25,  # 25% annual growth
                'overhead_multiplier': 1.2,   # Lower overhead
                'hiring_delay_months': -1,    # Hire 1 month early
            },
            entity_overrides=[
                {
                    'entity_type': 'sale',
                    'multiplier': 1.5,
                    'field': 'amount'
                },
                {
                    'entity_type': 'service',
                    'multiplier': 1.2,
                    'field': 'monthly_amount'
                }
            ]
        )
        self.add_scenario(optimistic)

        # Conservative scenario
        conservative = Scenario(
            name="conservative",
            description="Conservative scenario with reduced growth",
            assumptions={
                'revenue_growth_rate': 0.05,  # 5% annual growth
                'overhead_multiplier': 1.4,   # Higher overhead
                'hiring_delay_months': 2,     # Hire 2 months late
            },
            entity_overrides=[
                {
                    'entity_type': 'sale',
                    'multiplier': 0.8,
                    'field': 'amount'
                },
                {
                    'entity_type': 'grant',
                    'multiplier': 0.9,
                    'field': 'amount'
                }
            ]
        )
        self.add_scenario(conservative)

        # Cash preservation scenario
        cash_preservation = Scenario(
            name="cash_preservation",
            description="Scenario focused on preserving cash and reducing burn",
            assumptions={
                'overhead_multiplier': 1.1,   # Reduced overhead
                'hiring_delay_months': 6,     # Delay hiring 6 months
            },
            entity_filters={
                'exclude_tags': ['non_essential'],
                'exclude_patterns': ['bonus', 'stipend']
            },
            entity_overrides=[
                {
                    'name_pattern': '.*bonus.*',
                    'field': 'bonus_performance_max',
                    'value': 0.0
                },
                {
                    'entity_type': 'facility',
                    'multiplier': 0.9,
                    'field': 'monthly_cost'
                }
            ]
        )
        self.add_scenario(cash_preservation)


def create_scenario_summary(scenario_results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create summary comparison of multiple scenarios.

    Args:
        scenario_results: Dictionary of scenario results

    Returns:
        DataFrame with scenario comparison
    """
    summary_data = []

    for scenario_name, df in scenario_results.items():
        if len(df) == 0:
            continue

        summary = {
            'scenario': scenario_name,
            'total_revenue': df['total_revenue'].sum(),
            'total_expenses': df['total_expenses'].sum(),
            'net_cash_flow': df['net_cash_flow'].sum(),
            'final_cash_balance': df['cash_balance'].iloc[-1],
            'average_monthly_burn': -df['net_cash_flow'].mean(),
            'months_cash_positive': (df['net_cash_flow'] > 0).sum(),
            'peak_employees': df['active_employees'].max(),
            'peak_monthly_revenue': df['total_revenue'].max(),
            'peak_monthly_expenses': df['total_expenses'].max(),
        }
        summary_data.append(summary)

    return pd.DataFrame(summary_data)
