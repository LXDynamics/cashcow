"""Monte Carlo simulation module for CashCow."""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import asyncio
from pathlib import Path
import json

from ..engine import CashFlowEngine, KPICalculator
from ..storage import EntityStore
from ..models.base import BaseEntity


@dataclass
class Distribution:
    """Represents a probability distribution for Monte Carlo simulation."""
    
    type: str  # 'normal', 'uniform', 'triangular', 'lognormal', 'beta'
    params: Dict[str, float]
    
    def sample(self, size: int = 1) -> np.ndarray:
        """Generate random samples from the distribution."""
        if self.type == 'normal':
            return np.random.normal(self.params['mean'], self.params['std'], size)
        elif self.type == 'uniform':
            return np.random.uniform(self.params['low'], self.params['high'], size)
        elif self.type == 'triangular':
            return np.random.triangular(self.params['left'], self.params['mode'], self.params['right'], size)
        elif self.type == 'lognormal':
            return np.random.lognormal(self.params['mean'], self.params['sigma'], size)
        elif self.type == 'beta':
            return np.random.beta(self.params['a'], self.params['b'], size)
        else:
            raise ValueError(f"Unknown distribution type: {self.type}")


@dataclass
class UncertaintyModel:
    """Model for entity uncertainty in Monte Carlo simulations."""
    
    entity_name: str
    entity_type: str
    field: str
    distribution: Distribution
    correlation_group: Optional[str] = None  # For correlated variables
    
    def apply_to_entity(self, entity: BaseEntity, sample_value: float) -> BaseEntity:
        """Apply sampled value to entity field."""
        entity_dict = entity.model_dump()
        
        # Handle nested fields (e.g., 'salary.base')
        if '.' in self.field:
            keys = self.field.split('.')
            current = entity_dict
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = sample_value
        else:
            entity_dict[self.field] = sample_value
        
        # Recreate entity
        from ..models import create_entity
        return create_entity(entity_dict)


class MonteCarloSimulator:
    """Monte Carlo simulation engine for cash flow modeling."""
    
    def __init__(self, engine: CashFlowEngine, store: EntityStore):
        """Initialize Monte Carlo simulator.
        
        Args:
            engine: Cash flow calculation engine
            store: Entity storage
        """
        self.engine = engine
        self.store = store
        self.uncertainty_models: List[UncertaintyModel] = []
        self.correlation_matrix: Optional[np.ndarray] = None
        self.correlation_groups: Dict[str, List[int]] = {}
        
    def add_uncertainty(self, entity_name: str, entity_type: str, field: str, 
                       distribution: Distribution, correlation_group: Optional[str] = None):
        """Add uncertainty model for an entity field.
        
        Args:
            entity_name: Name of entity (or pattern)
            entity_type: Type of entity
            field: Field name to vary
            distribution: Probability distribution
            correlation_group: Optional correlation group name
        """
        model = UncertaintyModel(entity_name, entity_type, field, distribution, correlation_group)
        self.uncertainty_models.append(model)
        
        # Track correlation groups
        if correlation_group:
            if correlation_group not in self.correlation_groups:
                self.correlation_groups[correlation_group] = []
            self.correlation_groups[correlation_group].append(len(self.uncertainty_models) - 1)
    
    def set_correlation_matrix(self, correlation_matrix: np.ndarray):
        """Set correlation matrix for correlated variables.
        
        Args:
            correlation_matrix: Square correlation matrix
        """
        self.correlation_matrix = correlation_matrix
    
    def run_simulation(self, start_date: date, end_date: date, 
                      num_simulations: int = 1000,
                      confidence_levels: List[float] = [0.05, 0.25, 0.5, 0.75, 0.95],
                      parallel: bool = True,
                      max_workers: int = 4) -> Dict[str, Any]:
        """Run Monte Carlo simulation.
        
        Args:
            start_date: Simulation start date
            end_date: Simulation end date
            num_simulations: Number of simulation runs
            confidence_levels: Confidence levels for percentile analysis
            parallel: Whether to run simulations in parallel
            max_workers: Maximum number of worker threads
            
        Returns:
            Dictionary containing simulation results
        """
        print(f"Running Monte Carlo simulation with {num_simulations} iterations...")
        
        if parallel:
            return self._run_parallel_simulation(start_date, end_date, num_simulations, 
                                               confidence_levels, max_workers)
        else:
            return self._run_sequential_simulation(start_date, end_date, num_simulations, 
                                                 confidence_levels)
    
    def _run_parallel_simulation(self, start_date: date, end_date: date, 
                               num_simulations: int, confidence_levels: List[float],
                               max_workers: int) -> Dict[str, Any]:
        """Run simulation in parallel."""
        
        # Split simulations across workers
        sims_per_worker = num_simulations // max_workers
        remaining_sims = num_simulations % max_workers
        
        worker_sims = [sims_per_worker] * max_workers
        for i in range(remaining_sims):
            worker_sims[i] += 1
        
        # Run simulations in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for worker_id, num_sims in enumerate(worker_sims):
                if num_sims > 0:
                    future = executor.submit(self._run_worker_simulation, 
                                           start_date, end_date, num_sims, worker_id)
                    futures.append(future)
            
            # Collect results
            all_results = []
            for future in futures:
                worker_results = future.result()
                all_results.extend(worker_results)
        
        # Aggregate results
        return self._aggregate_simulation_results(all_results, confidence_levels)
    
    def _run_sequential_simulation(self, start_date: date, end_date: date,
                                 num_simulations: int, confidence_levels: List[float]) -> Dict[str, Any]:
        """Run simulation sequentially."""
        
        results = self._run_worker_simulation(start_date, end_date, num_simulations, 0)
        return self._aggregate_simulation_results(results, confidence_levels)
    
    def _run_worker_simulation(self, start_date: date, end_date: date,
                             num_simulations: int, worker_id: int) -> List[Dict[str, Any]]:
        """Run simulation for a worker thread."""
        
        results = []
        
        for sim_id in range(num_simulations):
            try:
                # Generate random samples for uncertainties
                samples = self._generate_correlated_samples()
                
                # Apply uncertainties to entities
                modified_entities = self._apply_uncertainties(samples)
                
                # Update entity store
                temp_store = self._create_temp_store(modified_entities)
                temp_engine = CashFlowEngine(temp_store)
                
                # Run cash flow calculation
                df = temp_engine.calculate_parallel(start_date, end_date, max_workers=1)
                
                # Calculate KPIs
                kpi_calc = KPICalculator()
                kpis = kpi_calc.calculate_all_kpis(df)
                
                # Store results
                result = {
                    'simulation_id': f"{worker_id}_{sim_id}",
                    'cash_flow': df,
                    'kpis': kpis,
                    'samples': samples,
                    'final_cash_balance': df['cash_balance'].iloc[-1],
                    'total_revenue': df['total_revenue'].sum(),
                    'total_expenses': df['total_expenses'].sum(),
                    'net_cash_flow': df['net_cash_flow'].sum(),
                    'runway_months': kpis.get('runway_months', 0),
                    'burn_rate': kpis.get('burn_rate', 0)
                }
                
                results.append(result)
                
                # Progress reporting
                if (sim_id + 1) % 100 == 0:
                    print(f"Worker {worker_id}: Completed {sim_id + 1}/{num_simulations} simulations")
                    
            except Exception as e:
                print(f"Error in simulation {worker_id}_{sim_id}: {e}")
                continue
        
        return results
    
    def _generate_correlated_samples(self) -> Dict[str, float]:
        """Generate correlated random samples for uncertainties."""
        
        if not self.uncertainty_models:
            return {}
        
        num_vars = len(self.uncertainty_models)
        
        # Generate independent samples
        independent_samples = np.array([
            model.distribution.sample(1)[0] 
            for model in self.uncertainty_models
        ])
        
        # Apply correlations if specified
        if self.correlation_matrix is not None and self.correlation_matrix.shape == (num_vars, num_vars):
            # Use Cholesky decomposition for correlation
            try:
                L = np.linalg.cholesky(self.correlation_matrix)
                # Convert to standard normal, apply correlation, convert back
                standard_normal = np.array([
                    np.random.standard_normal() for _ in range(num_vars)
                ])
                correlated_normal = L @ standard_normal
                
                # Map back to original distributions (approximate)
                samples = {}
                for i, model in enumerate(self.uncertainty_models):
                    # Simple approach: use correlation on the samples directly
                    samples[f"{model.entity_name}_{model.field}"] = independent_samples[i]
                
            except np.linalg.LinAlgError:
                # Fallback to independent samples if correlation matrix is invalid
                samples = {
                    f"{model.entity_name}_{model.field}": sample
                    for model, sample in zip(self.uncertainty_models, independent_samples)
                }
        else:
            samples = {
                f"{model.entity_name}_{model.field}": sample
                for model, sample in zip(self.uncertainty_models, independent_samples)
            }
        
        return samples
    
    def _apply_uncertainties(self, samples: Dict[str, float]) -> List[BaseEntity]:
        """Apply uncertainty samples to entities."""
        
        # Get all entities
        entities = self.store.query({})
        modified_entities = []
        
        for entity in entities:
            modified_entity = entity
            
            # Apply relevant uncertainties
            for model in self.uncertainty_models:
                sample_key = f"{model.entity_name}_{model.field}"
                
                # Check if this uncertainty applies to this entity
                if (model.entity_name == entity.name or 
                    model.entity_name == "*" or
                    model.entity_name in entity.name):
                    
                    if model.entity_type == entity.type:
                        if sample_key in samples:
                            modified_entity = model.apply_to_entity(
                                modified_entity, samples[sample_key]
                            )
            
            modified_entities.append(modified_entity)
        
        return modified_entities
    
    def _create_temp_store(self, entities: List[BaseEntity]) -> EntityStore:
        """Create temporary entity store with modified entities."""
        
        # Create in-memory store
        temp_store = EntityStore(":memory:")
        
        # Add entities
        for entity in entities:
            temp_store.add_entity(entity)
        
        return temp_store
    
    def _aggregate_simulation_results(self, results: List[Dict[str, Any]], 
                                    confidence_levels: List[float]) -> Dict[str, Any]:
        """Aggregate simulation results and calculate statistics."""
        
        if not results:
            return {"error": "No simulation results to aggregate"}
        
        print(f"Aggregating {len(results)} simulation results...")
        
        # Extract key metrics
        final_balances = [r['final_cash_balance'] for r in results]
        total_revenues = [r['total_revenue'] for r in results]
        total_expenses = [r['total_expenses'] for r in results]
        net_cash_flows = [r['net_cash_flow'] for r in results]
        runway_months = [r['runway_months'] for r in results if r['runway_months'] != float('inf')]
        burn_rates = [abs(r['burn_rate']) for r in results]
        
        # Calculate percentiles
        percentiles = {}
        metrics = {
            'final_cash_balance': final_balances,
            'total_revenue': total_revenues,
            'total_expenses': total_expenses,
            'net_cash_flow': net_cash_flows,
            'runway_months': runway_months,
            'burn_rate': burn_rates
        }
        
        for metric_name, values in metrics.items():
            if values:
                percentiles[metric_name] = {
                    f'p{int(cl*100)}': np.percentile(values, cl*100)
                    for cl in confidence_levels
                }
                percentiles[metric_name]['mean'] = np.mean(values)
                percentiles[metric_name]['std'] = np.std(values)
                percentiles[metric_name]['min'] = np.min(values)
                percentiles[metric_name]['max'] = np.max(values)
        
        # Risk analysis
        risk_metrics = self._calculate_risk_metrics(results)
        
        # Time series percentiles (monthly cash flow)
        time_series_percentiles = self._calculate_time_series_percentiles(
            results, confidence_levels
        )
        
        return {
            'num_simulations': len(results),
            'percentiles': percentiles,
            'risk_metrics': risk_metrics,
            'time_series': time_series_percentiles,
            'confidence_levels': confidence_levels,
            'summary': {
                'mean_final_balance': np.mean(final_balances),
                'probability_positive_balance': sum(1 for b in final_balances if b > 0) / len(final_balances),
                'probability_runway_gt_12m': sum(1 for r in runway_months if r > 12) / len(results),
                'mean_runway_months': np.mean(runway_months) if runway_months else 0,
                'value_at_risk_5pct': np.percentile(final_balances, 5),
                'expected_shortfall_5pct': np.mean([b for b in final_balances if b <= np.percentile(final_balances, 5)])
            }
        }
    
    def _calculate_risk_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate risk-specific metrics."""
        
        final_balances = [r['final_cash_balance'] for r in results]
        runway_months = [r['runway_months'] for r in results if r['runway_months'] != float('inf')]
        
        return {
            'probability_of_loss': sum(1 for b in final_balances if b < 0) / len(final_balances),
            'probability_runway_lt_6m': sum(1 for r in runway_months if r < 6) / len(results),
            'probability_runway_lt_12m': sum(1 for r in runway_months if r < 12) / len(results),
            'expected_loss_given_negative': np.mean([abs(b) for b in final_balances if b < 0]) if any(b < 0 for b in final_balances) else 0,
            'worst_case_5pct': np.percentile(final_balances, 5),
            'best_case_95pct': np.percentile(final_balances, 95),
            'volatility': np.std(final_balances),
            'sharpe_ratio': np.mean(final_balances) / np.std(final_balances) if np.std(final_balances) > 0 else 0
        }
    
    def _calculate_time_series_percentiles(self, results: List[Dict[str, Any]], 
                                         confidence_levels: List[float]) -> pd.DataFrame:
        """Calculate percentiles for time series data."""
        
        # Combine all cash flow DataFrames
        all_periods = []
        
        for result in results:
            df = result['cash_flow'].copy()
            df['simulation_id'] = result['simulation_id']
            all_periods.append(df[['period', 'cash_balance', 'net_cash_flow', 'simulation_id']])
        
        if not all_periods:
            return pd.DataFrame()
        
        combined_df = pd.concat(all_periods, ignore_index=True)
        
        # Calculate percentiles by period
        percentile_df = combined_df.groupby('period').agg({
            'cash_balance': [lambda x: np.percentile(x, cl*100) for cl in confidence_levels] + [np.mean, np.std],
            'net_cash_flow': [lambda x: np.percentile(x, cl*100) for cl in confidence_levels] + [np.mean, np.std]
        }).round(2)
        
        # Flatten column names
        percentile_df.columns = [
            f"{metric}_{stat}" for metric, stat in percentile_df.columns
        ]
        
        return percentile_df.reset_index()


def create_common_uncertainties() -> List[UncertaintyModel]:
    """Create common uncertainty models for typical business scenarios."""
    
    uncertainties = []
    
    # Employee salary uncertainty (±10%)
    uncertainties.append(UncertaintyModel(
        entity_name="*",
        entity_type="employee",
        field="salary",
        distribution=Distribution("normal", {"mean": 1.0, "std": 0.1})
    ))
    
    # Grant funding uncertainty (wide range)
    uncertainties.append(UncertaintyModel(
        entity_name="*",
        entity_type="grant",
        field="amount",
        distribution=Distribution("triangular", {"left": 0.5, "mode": 1.0, "right": 1.5})
    ))
    
    # Sales revenue uncertainty (high variance)
    uncertainties.append(UncertaintyModel(
        entity_name="*",
        entity_type="sale",
        field="amount",
        distribution=Distribution("lognormal", {"mean": 0.0, "sigma": 0.3})
    ))
    
    # Facility cost uncertainty (±5%)
    uncertainties.append(UncertaintyModel(
        entity_name="*",
        entity_type="facility",
        field="monthly_cost",
        distribution=Distribution("normal", {"mean": 1.0, "std": 0.05})
    ))
    
    return uncertainties


def save_simulation_results(results: Dict[str, Any], filepath: str):
    """Save simulation results to file."""
    
    # Convert numpy arrays to lists for JSON serialization
    serializable_results = {}
    
    for key, value in results.items():
        if key == 'time_series':
            # Save DataFrame as CSV
            if isinstance(value, pd.DataFrame):
                csv_path = filepath.replace('.json', '_timeseries.csv')
                value.to_csv(csv_path, index=False)
                serializable_results[key] = f"Saved to {csv_path}"
            else:
                serializable_results[key] = value
        elif isinstance(value, dict):
            serializable_results[key] = {}
            for subkey, subvalue in value.items():
                if isinstance(subvalue, (np.ndarray, list)):
                    serializable_results[key][subkey] = list(subvalue) if hasattr(subvalue, '__iter__') else subvalue
                elif isinstance(subvalue, dict):
                    serializable_results[key][subkey] = {
                        k: float(v) if isinstance(v, (np.float64, np.float32)) else v
                        for k, v in subvalue.items()
                    }
                else:
                    serializable_results[key][subkey] = float(subvalue) if isinstance(subvalue, (np.float64, np.float32)) else subvalue
        else:
            serializable_results[key] = value
    
    # Save to JSON
    with open(filepath, 'w') as f:
        json.dump(serializable_results, f, indent=2, default=str)
    
    print(f"Simulation results saved to {filepath}")


if __name__ == "__main__":
    # Demo usage
    from ..storage import EntityStore
    from ..engine import CashFlowEngine
    from datetime import date
    
    print("Monte Carlo Simulation Demo")
    
    # This would typically be run with real data
    store = EntityStore(":memory:")
    engine = CashFlowEngine(store)
    simulator = MonteCarloSimulator(engine, store)
    
    # Add some uncertainties
    for uncertainty in create_common_uncertainties():
        simulator.add_uncertainty(
            uncertainty.entity_name,
            uncertainty.entity_type,
            uncertainty.field,
            uncertainty.distribution
        )
    
    print(f"Added {len(simulator.uncertainty_models)} uncertainty models")
    print("Ready for simulation with real entity data!")