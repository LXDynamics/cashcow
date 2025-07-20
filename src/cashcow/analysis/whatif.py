"""What-If analysis module for CashCow."""

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd

from ..engine import CashFlowEngine, KPICalculator
from ..models.base import BaseEntity
from ..storage import EntityStore


@dataclass
class Parameter:
    """Represents a parameter for what-if analysis."""

    name: str
    entity_name: str
    entity_type: str
    field: str
    base_value: Union[float, str, date]
    current_value: Union[float, str, date] = None

    def __post_init__(self):
        if self.current_value is None:
            self.current_value = self.base_value


@dataclass
class WhatIfScenario:
    """What-If scenario with parameter changes."""

    name: str
    description: str
    parameters: List[Parameter] = field(default_factory=list)

    def add_parameter(self, parameter: Parameter):
        """Add parameter to scenario."""
        self.parameters.append(parameter)

    def set_parameter_value(self, param_name: str, value: Union[float, str, date]):
        """Set value for a specific parameter."""
        for param in self.parameters:
            if param.name == param_name:
                param.current_value = value
                break
        else:
            raise ValueError(f"Parameter '{param_name}' not found in scenario")

    def get_parameter_changes(self) -> Dict[str, Dict[str, Any]]:
        """Get all parameter changes from base values."""
        changes = {}
        for param in self.parameters:
            if param.current_value != param.base_value:
                key = f"{param.entity_name}_{param.field}"
                changes[key] = {
                    'entity_name': param.entity_name,
                    'entity_type': param.entity_type,
                    'field': param.field,
                    'base_value': param.base_value,
                    'new_value': param.current_value,
                    'change': self._calculate_change(param.base_value, param.current_value)
                }
        return changes

    def _calculate_change(self, base: Union[float, str, date],
                         current: Union[float, str, date]) -> Union[float, str]:
        """Calculate change between base and current value."""
        if isinstance(base, (int, float)) and isinstance(current, (int, float)):
            if base != 0:
                return (current - base) / base  # Percentage change
            else:
                return current - base  # Absolute change
        else:
            return f"{base} -> {current}"


class WhatIfAnalyzer:
    """What-If analysis engine for cash flow modeling."""

    def __init__(self, engine: CashFlowEngine, store: EntityStore):
        """Initialize What-If analyzer.

        Args:
            engine: Cash flow calculation engine
            store: Entity storage
        """
        self.engine = engine
        self.store = store
        self.scenarios: Dict[str, WhatIfScenario] = {}
        self.base_entities: List[BaseEntity] = []

        # Load base entities
        self._load_base_entities()

    def _load_base_entities(self):
        """Load base entities for comparison."""
        self.base_entities = self.store.query({})

    def create_scenario(self, name: str, description: str) -> WhatIfScenario:
        """Create new what-if scenario.

        Args:
            name: Scenario name
            description: Scenario description

        Returns:
            Created scenario
        """
        scenario = WhatIfScenario(name, description)
        self.scenarios[name] = scenario
        return scenario

    def add_parameter_to_scenario(self, scenario_name: str, parameter: Parameter):
        """Add parameter to existing scenario."""
        if scenario_name not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found")

        self.scenarios[scenario_name].add_parameter(parameter)

    def run_sensitivity_analysis(self, parameter: Parameter,
                                value_range: List[Union[float, str, date]],
                                start_date: date, end_date: date) -> Dict[str, Any]:
        """Run sensitivity analysis for a single parameter.

        Args:
            parameter: Parameter to analyze
            value_range: Range of values to test
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Sensitivity analysis results
        """
        print(f"Running sensitivity analysis for {parameter.name}...")

        results = {
            'parameter': parameter,
            'value_range': value_range,
            'scenarios': [],
            'metrics': {
                'final_cash_balance': [],
                'total_revenue': [],
                'total_expenses': [],
                'net_cash_flow': [],
                'runway_months': [],
                'burn_rate': []
            }
        }

        for value in value_range:
            # Create temporary scenario
            temp_scenario = WhatIfScenario(f"temp_{value}", f"Sensitivity test with {parameter.name}={value}")
            temp_param = deepcopy(parameter)
            temp_param.current_value = value
            temp_scenario.add_parameter(temp_param)

            # Run calculation
            try:
                scenario_result = self.calculate_scenario(temp_scenario, start_date, end_date)

                results['scenarios'].append({
                    'value': value,
                    'cash_flow': scenario_result['cash_flow'],
                    'kpis': scenario_result['kpis']
                })

                # Extract key metrics
                df = scenario_result['cash_flow']
                kpis = scenario_result['kpis']

                results['metrics']['final_cash_balance'].append(df['cash_balance'].iloc[-1])
                results['metrics']['total_revenue'].append(df['total_revenue'].sum())
                results['metrics']['total_expenses'].append(df['total_expenses'].sum())
                results['metrics']['net_cash_flow'].append(df['net_cash_flow'].sum())
                results['metrics']['runway_months'].append(kpis.get('runway_months', 0))
                results['metrics']['burn_rate'].append(kpis.get('burn_rate', 0))

            except Exception as e:
                print(f"Error calculating scenario for {parameter.name}={value}: {e}")
                # Add NaN values to maintain alignment
                for metric_list in results['metrics'].values():
                    metric_list.append(np.nan)

        # Calculate sensitivity metrics
        results['sensitivity_metrics'] = self._calculate_sensitivity_metrics(
            results['metrics'], value_range
        )

        return results

    def run_multi_parameter_analysis(self, scenario: WhatIfScenario,
                                   parameter_ranges: Dict[str, List[Union[float, str, date]]],
                                   start_date: date, end_date: date,
                                   max_combinations: int = 100) -> Dict[str, Any]:
        """Run analysis with multiple parameter combinations.

        Args:
            scenario: Base scenario
            parameter_ranges: Dict of parameter_name -> list of values
            start_date: Analysis start date
            end_date: Analysis end date
            max_combinations: Maximum number of combinations to test

        Returns:
            Multi-parameter analysis results
        """
        print(f"Running multi-parameter analysis with {len(parameter_ranges)} parameters...")

        # Generate parameter combinations
        combinations = self._generate_parameter_combinations(
            parameter_ranges, max_combinations
        )

        results = {
            'scenario': scenario,
            'parameter_ranges': parameter_ranges,
            'combinations': [],
            'num_combinations': len(combinations),
            'summary_stats': {}
        }

        for i, combination in enumerate(combinations):
            try:
                # Create test scenario
                test_scenario = deepcopy(scenario)

                # Apply parameter values
                for param_name, value in combination.items():
                    test_scenario.set_parameter_value(param_name, value)

                # Calculate
                scenario_result = self.calculate_scenario(test_scenario, start_date, end_date)

                # Store result
                df = scenario_result['cash_flow']
                kpis = scenario_result['kpis']

                combination_result = {
                    'combination_id': i,
                    'parameters': combination,
                    'final_cash_balance': df['cash_balance'].iloc[-1],
                    'total_revenue': df['total_revenue'].sum(),
                    'total_expenses': df['total_expenses'].sum(),
                    'net_cash_flow': df['net_cash_flow'].sum(),
                    'runway_months': kpis.get('runway_months', 0),
                    'burn_rate': kpis.get('burn_rate', 0),
                    'kpis': kpis
                }

                results['combinations'].append(combination_result)

                if (i + 1) % 10 == 0:
                    print(f"Completed {i + 1}/{len(combinations)} combinations")

            except Exception as e:
                print(f"Error in combination {i}: {e}")
                continue

        # Calculate summary statistics
        results['summary_stats'] = self._calculate_multi_param_stats(results['combinations'])

        return results

    def calculate_scenario(self, scenario: WhatIfScenario,
                         start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculate cash flow for a what-if scenario.

        Args:
            scenario: What-if scenario
            start_date: Calculation start date
            end_date: Calculation end date

        Returns:
            Scenario calculation results
        """
        # Apply scenario parameters to entities
        modified_entities = self._apply_scenario_to_entities(scenario)

        # Create temporary store
        temp_store = self._create_temp_store(modified_entities)
        temp_engine = CashFlowEngine(temp_store)

        # Calculate cash flow
        df = temp_engine.calculate_parallel(start_date, end_date)

        # Calculate KPIs
        kpi_calc = KPICalculator()
        kpis = kpi_calc.calculate_all_kpis(df)

        return {
            'scenario': scenario,
            'cash_flow': df,
            'kpis': kpis,
            'parameter_changes': scenario.get_parameter_changes()
        }

    def find_breakeven_value(self, parameter: Parameter, target_metric: str,
                           target_value: float, start_date: date, end_date: date,
                           search_range: Tuple[float, float] = None,
                           tolerance: float = 0.01) -> Dict[str, Any]:
        """Find parameter value that achieves target metric value.

        Args:
            parameter: Parameter to optimize
            target_metric: Target metric name (e.g., 'final_cash_balance')
            target_value: Target value for metric
            start_date: Analysis start date
            end_date: Analysis end date
            search_range: Search range (min, max) for parameter
            tolerance: Convergence tolerance

        Returns:
            Breakeven analysis results
        """
        print(f"Finding breakeven value for {parameter.name} to achieve {target_metric}={target_value}")

        if search_range is None:
            # Default search range around base value
            base = float(parameter.base_value)
            search_range = (base * 0.1, base * 3.0)

        # Binary search for breakeven value
        low, high = search_range
        iterations = 0
        max_iterations = 50

        best_value = None
        best_metric = None
        search_history = []

        while iterations < max_iterations and (high - low) > tolerance:
            mid = (low + high) / 2

            # Test mid value
            temp_scenario = WhatIfScenario("breakeven_test", "Breakeven test")
            temp_param = deepcopy(parameter)
            temp_param.current_value = mid
            temp_scenario.add_parameter(temp_param)

            try:
                result = self.calculate_scenario(temp_scenario, start_date, end_date)

                if target_metric == 'final_cash_balance':
                    metric_value = result['cash_flow']['cash_balance'].iloc[-1]
                elif target_metric == 'total_revenue':
                    metric_value = result['cash_flow']['total_revenue'].sum()
                elif target_metric == 'runway_months':
                    metric_value = result['kpis'].get('runway_months', 0)
                else:
                    metric_value = result['kpis'].get(target_metric, 0)

                search_history.append({
                    'parameter_value': mid,
                    'metric_value': metric_value,
                    'target_value': target_value,
                    'difference': abs(metric_value - target_value)
                })

                if abs(metric_value - target_value) <= tolerance:
                    best_value = mid
                    best_metric = metric_value
                    break
                elif metric_value < target_value:
                    low = mid
                else:
                    high = mid

                iterations += 1

            except Exception as e:
                print(f"Error in breakeven iteration {iterations}: {e}")
                break

        return {
            'parameter': parameter,
            'target_metric': target_metric,
            'target_value': target_value,
            'breakeven_value': best_value,
            'achieved_metric': best_metric,
            'iterations': iterations,
            'search_history': search_history,
            'converged': best_value is not None
        }

    def compare_scenarios(self, scenario_names: List[str],
                         start_date: date, end_date: date) -> Dict[str, Any]:
        """Compare multiple what-if scenarios.

        Args:
            scenario_names: List of scenario names to compare
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Scenario comparison results
        """
        print(f"Comparing {len(scenario_names)} what-if scenarios...")

        results = {
            'scenarios': {},
            'comparison_table': [],
            'best_scenarios': {},
            'worst_scenarios': {}
        }

        # Calculate each scenario
        for name in scenario_names:
            if name not in self.scenarios:
                print(f"Warning: Scenario '{name}' not found")
                continue

            try:
                scenario_result = self.calculate_scenario(self.scenarios[name], start_date, end_date)
                results['scenarios'][name] = scenario_result

                # Extract key metrics for comparison
                df = scenario_result['cash_flow']
                kpis = scenario_result['kpis']

                comparison_row = {
                    'scenario_name': name,
                    'final_cash_balance': df['cash_balance'].iloc[-1],
                    'total_revenue': df['total_revenue'].sum(),
                    'total_expenses': df['total_expenses'].sum(),
                    'net_cash_flow': df['net_cash_flow'].sum(),
                    'runway_months': kpis.get('runway_months', 0),
                    'burn_rate': kpis.get('burn_rate', 0),
                    'parameter_changes': len(scenario_result['parameter_changes'])
                }

                results['comparison_table'].append(comparison_row)

            except Exception as e:
                print(f"Error calculating scenario '{name}': {e}")

        # Find best and worst scenarios
        if results['comparison_table']:
            comparison_df = pd.DataFrame(results['comparison_table'])

            metrics = ['final_cash_balance', 'total_revenue', 'net_cash_flow', 'runway_months']
            for metric in metrics:
                if metric in comparison_df.columns:
                    best_idx = comparison_df[metric].idxmax()
                    worst_idx = comparison_df[metric].idxmin()

                    results['best_scenarios'][metric] = comparison_df.iloc[best_idx]['scenario_name']
                    results['worst_scenarios'][metric] = comparison_df.iloc[worst_idx]['scenario_name']

        return results

    def _apply_scenario_to_entities(self, scenario: WhatIfScenario) -> List[BaseEntity]:
        """Apply scenario parameters to entities."""

        modified_entities = []

        for entity in self.base_entities:
            modified_entity = entity

            # Apply relevant parameters
            for param in scenario.parameters:
                if (param.entity_name == entity.name or
                    param.entity_name == "*" or
                    param.entity_name in entity.name):

                    if param.entity_type == entity.type:
                        # Apply parameter change
                        modified_entity = self._apply_parameter_to_entity(
                            modified_entity, param
                        )

            modified_entities.append(modified_entity)

        return modified_entities

    def _apply_parameter_to_entity(self, entity: BaseEntity, param: Parameter) -> BaseEntity:
        """Apply parameter change to entity."""

        entity_dict = entity.model_dump()

        # Handle nested fields
        if '.' in param.field:
            keys = param.field.split('.')
            current = entity_dict
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = param.current_value
        else:
            entity_dict[param.field] = param.current_value

        # Recreate entity
        from ..models import create_entity
        return create_entity(entity_dict)

    def _create_temp_store(self, entities: List[BaseEntity]) -> EntityStore:
        """Create temporary entity store."""

        temp_store = EntityStore(":memory:")

        for entity in entities:
            temp_store.add_entity(entity)

        return temp_store

    def _generate_parameter_combinations(self, parameter_ranges: Dict[str, List],
                                       max_combinations: int) -> List[Dict[str, Any]]:
        """Generate parameter combinations for testing."""

        import itertools

        # Get all combinations
        keys = list(parameter_ranges.keys())
        value_lists = list(parameter_ranges.values())

        all_combinations = list(itertools.product(*value_lists))

        # Limit combinations if too many
        if len(all_combinations) > max_combinations:
            # Sample evenly
            step = len(all_combinations) // max_combinations
            selected_combinations = all_combinations[::step][:max_combinations]
        else:
            selected_combinations = all_combinations

        # Convert to list of dictionaries
        combinations = []
        for combo in selected_combinations:
            combination_dict = dict(zip(keys, combo))
            combinations.append(combination_dict)

        return combinations

    def _calculate_sensitivity_metrics(self, metrics: Dict[str, List],
                                     value_range: List) -> Dict[str, Any]:
        """Calculate sensitivity analysis metrics."""

        sensitivity = {}

        for metric_name, metric_values in metrics.items():
            if len(metric_values) == len(value_range) and len(value_range) > 1:
                # Calculate correlation between parameter and metric
                param_values = [float(v) for v in value_range if isinstance(v, (int, float))]
                metric_vals = [v for v in metric_values if not np.isnan(v)]

                if len(param_values) == len(metric_vals) and len(param_values) > 1:
                    correlation = np.corrcoef(param_values, metric_vals)[0, 1]

                    # Calculate elasticity (percentage change in metric / percentage change in parameter)
                    param_pct_change = (max(param_values) - min(param_values)) / min(param_values) if min(param_values) > 0 else 0
                    metric_pct_change = (max(metric_vals) - min(metric_vals)) / abs(min(metric_vals)) if min(metric_vals) != 0 else 0

                    elasticity = metric_pct_change / param_pct_change if param_pct_change != 0 else 0

                    sensitivity[metric_name] = {
                        'correlation': correlation,
                        'elasticity': elasticity,
                        'min_value': min(metric_vals),
                        'max_value': max(metric_vals),
                        'range': max(metric_vals) - min(metric_vals),
                        'volatility': np.std(metric_vals)
                    }

        return sensitivity

    def _calculate_multi_param_stats(self, combinations: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics for multi-parameter analysis."""

        if not combinations:
            return {}

        # Extract metrics
        metrics = {}
        for key in ['final_cash_balance', 'total_revenue', 'total_expenses',
                   'net_cash_flow', 'runway_months', 'burn_rate']:
            values = [combo[key] for combo in combinations if key in combo and not np.isnan(combo[key])]
            if values:
                metrics[key] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'median': np.median(values),
                    'q25': np.percentile(values, 25),
                    'q75': np.percentile(values, 75)
                }

        # Find best and worst combinations
        if combinations:
            best_combo = max(combinations, key=lambda x: x.get('final_cash_balance', -float('inf')))
            worst_combo = min(combinations, key=lambda x: x.get('final_cash_balance', float('inf')))

            return {
                'metrics': metrics,
                'best_combination': best_combo,
                'worst_combination': worst_combo,
                'num_positive_outcomes': sum(1 for combo in combinations if combo.get('final_cash_balance', 0) > 0),
                'success_rate': sum(1 for combo in combinations if combo.get('final_cash_balance', 0) > 0) / len(combinations)
            }

        return {'metrics': metrics}


def create_standard_parameters(entities: List[BaseEntity]) -> List[Parameter]:
    """Create standard parameters for what-if analysis."""

    parameters = []

    for entity in entities:
        if entity.type == 'employee':
            # Salary parameter
            current_salary = getattr(entity, 'salary', 75000)
            parameters.append(Parameter(
                name=f"{entity.name}_salary",
                entity_name=entity.name,
                entity_type='employee',
                field='salary',
                base_value=current_salary
            ))

        elif entity.type == 'grant':
            # Grant amount parameter
            current_amount = getattr(entity, 'amount', 100000)
            parameters.append(Parameter(
                name=f"{entity.name}_amount",
                entity_name=entity.name,
                entity_type='grant',
                field='amount',
                base_value=current_amount
            ))

        elif entity.type == 'sale':
            # Sale amount parameter
            current_amount = getattr(entity, 'amount', 50000)
            parameters.append(Parameter(
                name=f"{entity.name}_amount",
                entity_name=entity.name,
                entity_type='sale',
                field='amount',
                base_value=current_amount
            ))

        elif entity.type == 'facility':
            # Facility cost parameter
            current_cost = getattr(entity, 'monthly_cost', 10000)
            parameters.append(Parameter(
                name=f"{entity.name}_monthly_cost",
                entity_name=entity.name,
                entity_type='facility',
                field='monthly_cost',
                base_value=current_cost
            ))

    return parameters


if __name__ == "__main__":
    # Demo usage
    print("What-If Analysis Demo")
    print("Ready for analysis with real entity data!")
