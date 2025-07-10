"""Configuration management for CashCow."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class EntityTypeConfig(BaseModel):
    """Configuration for an entity type."""
    
    required_fields: List[str]
    calculators: List[str]
    default_overhead_multiplier: Optional[float] = None


class KPIConfig(BaseModel):
    """Configuration for a KPI."""
    
    name: str
    description: str
    category: str


class ReportingConfig(BaseModel):
    """Configuration for reporting."""
    
    default_forecast_months: int = 24
    chart_style: str = "seaborn"
    output_formats: List[str] = ["csv", "json", "html"]


class ScenarioConfig(BaseModel):
    """Configuration for scenarios."""
    
    default: str = "baseline"
    sensitivity_variables: List[str] = []


class CashCowConfig(BaseModel):
    """Main configuration for CashCow."""
    
    version: str
    database: str = "cashcow.db"
    entity_types: Dict[str, EntityTypeConfig]
    kpis: List[KPIConfig]
    reporting: ReportingConfig
    scenarios: ScenarioConfig


class Config:
    """Configuration manager for CashCow."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If not provided,
                        looks for config/settings.yaml relative to project root.
        """
        if config_path is None:
            # Try to find config file
            possible_paths = [
                Path("config/settings.yaml"),
                Path("../config/settings.yaml"),
                Path("../../config/settings.yaml"),
                Path.home() / ".cashcow" / "settings.yaml",
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
            else:
                # Use default config
                config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        
        self.config_path = Path(config_path)
        self._config: Optional[CashCowConfig] = None
        self._raw_config: Dict[str, Any] = {}
        
        if self.config_path.exists():
            self.load()
    
    def load(self) -> None:
        """Load configuration from file."""
        with open(self.config_path, 'r') as f:
            self._raw_config = yaml.safe_load(f)
        
        # Parse into Pydantic models
        if 'cashcow' in self._raw_config:
            config_data = self._raw_config['cashcow']
            
            # Convert entity types
            entity_types = {}
            for name, et_config in config_data.get('entity_types', {}).items():
                entity_types[name] = EntityTypeConfig(**et_config)
            
            # Convert KPIs
            kpis = [KPIConfig(**kpi) for kpi in config_data.get('kpis', [])]
            
            # Convert other configs
            reporting = ReportingConfig(**config_data.get('reporting', {}))
            scenarios = ScenarioConfig(**config_data.get('scenarios', {}))
            
            self._config = CashCowConfig(
                version=config_data['version'],
                database=config_data.get('database', 'cashcow.db'),
                entity_types=entity_types,
                kpis=kpis,
                reporting=reporting,
                scenarios=scenarios
            )
    
    @property
    def config(self) -> CashCowConfig:
        """Get the configuration object."""
        if self._config is None:
            raise ValueError("Configuration not loaded")
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated key.
        
        Args:
            key: Dot-separated key (e.g., 'cashcow.database')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        parts = key.split('.')
        value = self._raw_config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def get_entity_config(self, entity_type: str) -> Optional[EntityTypeConfig]:
        """Get configuration for a specific entity type.
        
        Args:
            entity_type: Type of entity (employee, grant, etc.)
            
        Returns:
            Entity type configuration or None
        """
        return self.config.entity_types.get(entity_type)
    
    def get_required_fields(self, entity_type: str) -> List[str]:
        """Get required fields for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            List of required field names
        """
        entity_config = self.get_entity_config(entity_type)
        if entity_config:
            return entity_config.required_fields
        return []
    
    def get_calculators(self, entity_type: str) -> List[str]:
        """Get calculator names for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            List of calculator names
        """
        entity_config = self.get_entity_config(entity_type)
        if entity_config:
            return entity_config.calculators
        return []
    
    def get_kpis(self, category: Optional[str] = None) -> List[KPIConfig]:
        """Get KPI configurations.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of KPI configurations
        """
        kpis = self.config.kpis
        
        if category:
            kpis = [kpi for kpi in kpis if kpi.category == category]
        
        return kpis
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file.
        
        Args:
            config_path: Path to save to. Uses current path if not provided.
        """
        if config_path is None:
            config_path = self.config_path
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump({'cashcow': self._raw_config.get('cashcow', {})}, 
                     f, default_flow_style=False, sort_keys=False)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def load_config(config_path: Path) -> Config:
    """Load configuration from a specific path.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration instance
    """
    global _config
    _config = Config(config_path)
    return _config