"""Database storage for CashCow entities."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Column,
    Date,
    Integer,
    String,
    create_engine,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..models import BaseEntity, create_entity

Base = declarative_base()


class EntityRecord(Base):
    """SQLite table for storing entities."""

    __tablename__ = 'entities'

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)
    file_path = Column(String, nullable=False, unique=True)
    data = Column(JSON, nullable=False)  # Full entity data as JSON
    created_at = Column(Date, default=datetime.utcnow)
    updated_at = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)


class EntityStore:
    """Store for managing entities with SQLite backend."""

    def __init__(self, db_path: str = "cashcow.db"):
        """Initialize the entity store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.async_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)
        self.AsyncSession = sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        Base.metadata.create_all(self.engine)

    async def sync_from_yaml(self, entities_dir: Path) -> int:
        """Load all YAML files into SQLite for fast querying.

        Args:
            entities_dir: Root directory containing entity YAML files

        Returns:
            Number of entities synced
        """
        import yaml

        count = 0
        session = None
        try:
            session = self.AsyncSession()
            # Clear existing records
            await session.execute(text(f"DELETE FROM {EntityRecord.__tablename__}"))

            # Walk through all YAML files
            for yaml_file in entities_dir.rglob("*.yaml"):
                try:
                    with open(yaml_file) as f:
                        data = yaml.safe_load(f)

                    if data and isinstance(data, dict) and 'type' in data:
                        # Create entity to validate data
                        entity = create_entity(data)

                        # Store in database
                        record = EntityRecord(
                            type=entity.type,
                            name=entity.name,
                            start_date=entity.start_date,
                            end_date=entity.end_date,
                            file_path=str(yaml_file),
                            data=json.loads(entity.model_dump_json())
                        )
                        session.add(record)
                        count += 1

                except Exception as e:
                    print(f"Error loading {yaml_file}: {e}")

            await session.commit()
        finally:
            if session:
                await session.close()

        return count

    def query(self, filters: Optional[Dict[str, Any]] = None) -> List[BaseEntity]:
        """Query entities with optional filters.

        Args:
            filters: Dictionary of filters to apply
                - type: Entity type (employee, grant, etc.)
                - active_on: Date to check if entity is active
                - tags: List of tags to filter by
                - name_contains: Substring to search in name

        Returns:
            List of matching entities
        """
        with self.Session() as session:
            query = session.query(EntityRecord)

            if filters:
                if 'type' in filters:
                    query = query.filter(EntityRecord.type == filters['type'])

                if 'active_on' in filters:
                    active_date = filters['active_on']
                    if isinstance(active_date, str):
                        active_date = date.fromisoformat(active_date)

                    query = query.filter(
                        EntityRecord.start_date <= active_date,
                        (EntityRecord.end_date.is_(None)) |
                        (EntityRecord.end_date >= active_date)
                    )

                if 'name_contains' in filters:
                    query = query.filter(
                        EntityRecord.name.contains(filters['name_contains'])
                    )

            results = []
            for record in query.all():
                entity = create_entity(record.data)

                # Additional filtering for tags if needed
                if filters and 'tags' in filters:
                    filter_tags = set(filters['tags'])
                    entity_tags = set(entity.tags)
                    if not filter_tags.intersection(entity_tags):
                        continue

                results.append(entity)

            return results

    def get_by_name(self, name: str, entity_type: Optional[str] = None) -> Optional[BaseEntity]:
        """Get a single entity by name.

        Args:
            name: Entity name
            entity_type: Optional entity type filter

        Returns:
            Entity if found, None otherwise
        """
        filters = {'name_contains': name}
        if entity_type:
            filters['type'] = entity_type

        results = self.query(filters)
        if results and results[0].name == name:
            return results[0]
        return None

    def get_active_entities(self, as_of_date: date, entity_type: Optional[str] = None) -> List[BaseEntity]:
        """Get all active entities as of a specific date.

        Args:
            as_of_date: Date to check active status
            entity_type: Optional filter by entity type

        Returns:
            List of active entities
        """
        filters = {'active_on': as_of_date}
        if entity_type:
            filters['type'] = entity_type
        return self.query(filters)

    def add_entity(self, entity: BaseEntity, file_path: Optional[str] = None) -> int:
        """Add a single entity to the store.

        Args:
            entity: Entity to add
            file_path: Optional file path (for temporary/memory storage can be None)

        Returns:
            Entity ID in database
        """
        import uuid

        with self.Session() as session:
            # Generate unique file path if not provided
            if not file_path:
                unique_id = str(uuid.uuid4())[:8]
                file_path = f"temp_{entity.type}_{entity.name}_{unique_id}"

            record = EntityRecord(
                type=entity.type,
                name=entity.name,
                start_date=entity.start_date,
                end_date=entity.end_date,
                file_path=file_path,
                data=json.loads(entity.model_dump_json())
            )
            session.add(record)
            session.commit()
            return record.id

    def get_all_entities(self) -> List[BaseEntity]:
        """Get all entities from the store.

        Returns:
            List of all entities
        """
        return self.query()

    def get_entities_by_type(self, entity_type: str) -> List[BaseEntity]:
        """Get entities by type.

        Args:
            entity_type: Type of entities to retrieve

        Returns:
            List of entities of specified type
        """
        return self.query({'type': entity_type})

    def get_entities_by_tags(self, tags: List[str]) -> List[BaseEntity]:
        """Get entities by tags.

        Args:
            tags: List of tags to filter by

        Returns:
            List of entities matching tags
        """
        return self.query({'tags': tags})

    def update_entity(self, entity: BaseEntity) -> None:
        """Update an existing entity in the store.

        Args:
            entity: Updated entity object
        """
        with self.Session() as session:
            # Find existing record by name and type
            record = session.query(EntityRecord).filter(
                EntityRecord.name == entity.name,
                EntityRecord.type == entity.type
            ).first()

            if record:
                # Update the record
                record.start_date = entity.start_date
                record.end_date = entity.end_date
                record.data = json.loads(entity.model_dump_json())
                record.updated_at = datetime.utcnow().date()
                session.commit()
            else:
                # Entity doesn't exist, add it
                self.add_entity(entity)

    def delete_entity(self, entity_name: str, entity_type: Optional[str] = None) -> bool:
        """Delete an entity from the store.

        Args:
            entity_name: Name of entity to delete
            entity_type: Optional entity type for more specific deletion

        Returns:
            True if entity was deleted, False if not found
        """
        with self.Session() as session:
            query = session.query(EntityRecord).filter(
                EntityRecord.name == entity_name
            )

            if entity_type:
                query = query.filter(EntityRecord.type == entity_type)

            record = query.first()
            if record:
                session.delete(record)
                session.commit()
                return True
            return False

    def close(self):
        """Close database connections."""
        self.engine.dispose()

    async def aclose(self):
        """Close async database connections."""
        await self.async_engine.dispose()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.aclose()

    def __del__(self):
        """Destructor to ensure cleanup when object is garbage collected."""
        try:
            self.close()
        except Exception:
            pass
