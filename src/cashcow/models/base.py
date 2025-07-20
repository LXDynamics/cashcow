"""Base models for the CashCow system."""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class BaseEntity(BaseModel):
    """Base class for all entities in the system.

    Supports flexible schema - any additional fields are allowed and preserved.
    """

    model_config = ConfigDict(extra='allow')  # Accept any fields

    # Required fields for all entities
    type: str
    name: str
    start_date: date

    # Common optional fields
    end_date: Optional[date] = None
    tags: List[str] = []
    notes: Optional[str] = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_dates(cls, v: Any) -> Optional[date]:
        """Parse date strings to date objects."""
        if v is None:
            return None
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure end_date is after start_date if provided."""
        if v is not None and 'start_date' in info.data:
            start = info.data['start_date']
            if isinstance(start, date) and v < start:
                raise ValueError('end_date must be after start_date')
        return v

    def is_active(self, context=None) -> bool:
        """Check if the entity is active on a given date."""
        if isinstance(context, dict):
            as_of_date = context.get('as_of_date', date.today())
        else:
            as_of_date = context or date.today()

        if self.start_date > as_of_date:
            return False
        if self.end_date is None:
            return True
        return self.end_date >= as_of_date

    def get_field(self, field_name: str, default: Any = None) -> Any:
        """Get a field value with a default if not present."""
        return getattr(self, field_name, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary, including extra fields."""
        return self.model_dump()

    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        """Create entity from YAML dictionary."""
        return cls(**data)
