"""YAML file loader for CashCow entities."""

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..models import BaseEntity, create_entity


class DateSafeLoader(yaml.SafeLoader):
    """Custom YAML loader that handles dates properly."""
    pass


def date_constructor(loader, node):
    """Construct a date from YAML."""
    value = loader.construct_scalar(node)
    return date.fromisoformat(value)


def datetime_constructor(loader, node):
    """Construct a datetime from YAML."""
    value = loader.construct_scalar(node)
    return datetime.fromisoformat(value)


# Register date/datetime constructors
DateSafeLoader.add_constructor('!date', date_constructor)
DateSafeLoader.add_constructor('!datetime', datetime_constructor)


class YamlEntityLoader:
    """Loader for YAML entity files."""
    
    def __init__(self, entities_dir: Union[str, Path]):
        """Initialize the YAML loader.
        
        Args:
            entities_dir: Root directory containing entity YAML files
        """
        self.entities_dir = Path(entities_dir)
        if not self.entities_dir.exists():
            raise ValueError(f"Entities directory does not exist: {entities_dir}")
    
    def load_file(self, file_path: Union[str, Path]) -> Optional[BaseEntity]:
        """Load a single entity from a YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Entity object or None if file is invalid
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'r') as f:
                data = yaml.load(f, Loader=DateSafeLoader)
            
            if not data or not isinstance(data, dict):
                return None
            
            # Add file path as metadata
            data['_file_path'] = str(file_path)
            
            return create_entity(data)
            
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def load_all(self) -> List[BaseEntity]:
        """Load all entities from the entities directory.
        
        Returns:
            List of all loaded entities
        """
        entities = []
        
        for yaml_file in self.entities_dir.rglob("*.yaml"):
            entity = self.load_file(yaml_file)
            if entity:
                entities.append(entity)
        
        return entities
    
    def load_by_type(self, entity_type: str) -> List[BaseEntity]:
        """Load all entities of a specific type.
        
        Args:
            entity_type: Type of entities to load (employee, grant, etc.)
            
        Returns:
            List of entities of the specified type
        """
        type_dir = self.entities_dir / entity_type.lower()
        entities = []
        
        if type_dir.exists():
            for yaml_file in type_dir.rglob("*.yaml"):
                entity = self.load_file(yaml_file)
                if entity and entity.type == entity_type:
                    entities.append(entity)
        
        return entities
    
    def save_entity(self, entity: BaseEntity, file_path: Optional[Union[str, Path]] = None) -> Path:
        """Save an entity to a YAML file.
        
        Args:
            entity: Entity to save
            file_path: Optional specific file path. If not provided, generates one.
            
        Returns:
            Path to the saved file
        """
        if file_path is None:
            # Generate file path based on entity type and name
            type_dir = self.entities_dir
            
            # Map entity types to directories
            if entity.type in ['employee']:
                type_dir = type_dir / 'expenses' / 'employees'
            elif entity.type in ['grant', 'investment', 'sale', 'service']:
                type_dir = type_dir / 'revenue' / f"{entity.type}s"
            elif entity.type in ['facility', 'software', 'equipment']:
                type_dir = type_dir / 'expenses' / f"{entity.type.lower()}s"
            elif entity.type == 'project':
                type_dir = type_dir / 'projects'
            else:
                type_dir = type_dir / entity.type
            
            # Create directory if it doesn't exist
            type_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename from entity name
            safe_name = entity.name.lower().replace(' ', '-').replace('/', '-')
            file_path = type_dir / f"{safe_name}.yaml"
        else:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert entity to dict and remove internal fields
        data = entity.to_dict()
        data.pop('_file_path', None)
        
        # Custom representer for dates
        def date_representer(dumper, value):
            return dumper.represent_scalar('tag:yaml.org,2002:str', value.isoformat())
        
        yaml.add_representer(date, date_representer)
        yaml.add_representer(datetime, date_representer)
        
        # Write YAML file
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        return file_path
    
    def generate_file_path(self, entity: BaseEntity) -> Path:
        """Generate file path for an entity based on its type and name.
        
        Args:
            entity: Entity to generate path for
            
        Returns:
            Path where the entity file should be saved
        """
        type_dir = self.entities_dir
        
        # Map entity types to directories
        if entity.type in ['employee']:
            type_dir = type_dir / 'expenses' / 'employees'
        elif entity.type in ['grant', 'investment', 'sale', 'service']:
            type_dir = type_dir / 'revenue' / f"{entity.type}s"
        elif entity.type in ['facility', 'software', 'equipment']:
            type_dir = type_dir / 'expenses' / f"{entity.type.lower()}s"
        elif entity.type == 'project':
            type_dir = type_dir / 'projects'
        else:
            type_dir = type_dir / entity.type
        
        # Generate filename from entity name
        safe_name = entity.name.lower().replace(' ', '-').replace('/', '-')
        return type_dir / f"{safe_name}.yaml"
    
    def load_entity(self, file_path: Union[str, Path]) -> Optional[BaseEntity]:
        """Load a single entity from a YAML file. Alias for load_file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Entity object or None if file is invalid
            
        Raises:
            yaml.YAMLError: If YAML file is malformed
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'r') as f:
                data = yaml.load(f, Loader=DateSafeLoader)
            
            if not data or not isinstance(data, dict):
                return None
            
            # Add file path as metadata
            data['_file_path'] = str(file_path)
            
            return create_entity(data)
            
        except yaml.YAMLError:
            # Re-raise YAML errors for test compatibility
            raise
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def load_all_entities(self) -> List[BaseEntity]:
        """Load all entities from the entities directory. Alias for load_all.
        
        Returns:
            List of all loaded entities
        """
        return self.load_all()
    
    def validate_entity_data(self, data: Dict[str, Any]) -> bool:
        """Validate entity data structure.
        
        Args:
            data: Entity data dictionary
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            create_entity(data)
            return True
        except Exception:
            return False
    
    def handle_date_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process date fields in entity data.
        
        Args:
            data: Entity data dictionary
            
        Returns:
            Processed data with date objects
        """
        from datetime import date
        
        processed_data = data.copy()
        
        # Convert string dates to date objects
        for field in ['start_date', 'end_date']:
            if field in processed_data and isinstance(processed_data[field], str):
                try:
                    processed_data[field] = date.fromisoformat(processed_data[field])
                except ValueError:
                    pass  # Keep original value if conversion fails
        
        return processed_data
    
    def validate_all(self) -> Dict[str, List[str]]:
        """Validate all YAML files in the entities directory.
        
        Returns:
            Dictionary mapping file paths to lists of validation errors
        """
        errors = {}
        
        for yaml_file in self.entities_dir.rglob("*.yaml"):
            try:
                entity = self.load_file(yaml_file)
                if not entity:
                    errors[str(yaml_file)] = ["Failed to load entity"]
            except Exception as e:
                errors[str(yaml_file)] = [str(e)]
        
        return errors